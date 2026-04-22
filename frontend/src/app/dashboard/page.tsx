"use client";

import { useRef, useState } from "react";
import WebcamCapture from "@/components/WebcamCapture";
import EmotionChart from "@/components/EmotionChart";
import ClassroomStats from "@/components/ClassroomStats";
import { api } from "@/lib/api";
import { FaceResult, LogEntry } from "@/lib/types";

export default function DashboardPage() {
  const [sessionId, setSessionId]     = useState<number | null>(null);
  const [isRunning, setIsRunning]     = useState(false);
  const [logs, setLogs]               = useState<LogEntry[]>([]);
  const [currentFaces, setCurrentFaces] = useState<FaceResult[]>([]);
  const sessionTitle = useRef(`Session ${new Date().toLocaleString()}`);
  const frameCount   = useRef(0);

  async function startSession() {
    const { data } = await api.post("/sessions", { title: sessionTitle.current });
    setSessionId(data.id);
    setIsRunning(true);
    setLogs([]);
    setCurrentFaces([]);
    frameCount.current = 0;
  }

  async function stopSession() {
    setIsRunning(false);
    if (sessionId) {
      await api.patch(`/sessions/${sessionId}`, { status: "ended" });
    }
  }

  async function handleFrame(imageBlob: Blob) {
    if (!isRunning || !sessionId) return;

    const form = new FormData();
    form.append("file", imageBlob, "frame.jpg");

    try {
      const { data } = await api.post("/api/ai/emotion/predict", form, {
        headers: { "Content-Type": "multipart/form-data" },
        baseURL: "",
      });

      if (!data.success || !data.results?.length) {
        setCurrentFaces([]);
        return;
      }

      const faces: FaceResult[] = data.results;
      setCurrentFaces(faces);

      const now = Date.now();
      const newEntries: LogEntry[] = faces.map((f) => ({
        face_index: f.face_index,
        emotion:    f.emotion,
        confidence: f.confidence,
        engagement: f.engagement,
        timestamp:  now,
      }));

      // Keep up to 1800 raw entries (30 faces × 60 frames)
      setLogs((prev) => [...prev.slice(-1800), ...newEntries]);

      // Persist every 5th frame
      frameCount.current += 1;
      if (frameCount.current % 5 === 0) {
        await Promise.all(
          faces.map((f) =>
            api.post(`/sessions/${sessionId}/logs`, {
              emotion:    f.emotion,
              confidence: f.confidence,
              engagement: f.engagement,
              all_scores: f.all_scores,
              face_index: f.face_index,
            })
          )
        );
      }
    } catch {
      // silently ignore network errors during capture
    }
  }

  return (
    <main className="min-h-screen p-6 space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-bold">SEAS Dashboard</h1>
        <div className="flex gap-3">
          {!isRunning ? (
            <button
              onClick={startSession}
              className="bg-green-600 hover:bg-green-500 px-4 py-2 rounded-lg text-sm font-semibold transition"
            >
              Start Session
            </button>
          ) : (
            <button
              onClick={stopSession}
              className="bg-red-600 hover:bg-red-500 px-4 py-2 rounded-lg text-sm font-semibold transition"
            >
              End Session
            </button>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <WebcamCapture
            isActive={isRunning}
            onFrame={handleFrame}
            captureIntervalMs={1000}
            faceResults={currentFaces}
          />
          <ClassroomStats faceResults={currentFaces} />
        </div>

        <div>
          <EmotionChart logs={logs} />
        </div>
      </div>
    </main>
  );
}
