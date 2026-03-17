"use client";

import { useEffect, useRef, useState } from "react";
import WebcamCapture from "@/components/WebcamCapture";
import EmotionChart from "@/components/EmotionChart";
import EngagementBadge from "@/components/EngagementBadge";
import { api } from "@/lib/api";

interface LogEntry {
  emotion: string;
  confidence: number;
  engagement: string;
  timestamp: number;
}

export default function DashboardPage() {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [latestResult, setLatestResult] = useState<LogEntry | null>(null);
  const sessionTitle = useRef(`Session ${new Date().toLocaleString()}`);

  async function startSession() {
    const { data } = await api.post("/sessions", { title: sessionTitle.current });
    setSessionId(data.id);
    setIsRunning(true);
    setLogs([]);
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

      if (!data.success || !data.result?.face_detected) return;

      const entry: LogEntry = {
        emotion:    data.result.emotion,
        confidence: data.result.confidence,
        engagement: data.result.engagement,
        timestamp:  Date.now(),
      };

      setLatestResult(entry);
      setLogs((prev) => [...prev.slice(-299), entry]);

      // Persist to backend every 5th frame
      if (logs.length % 5 === 0) {
        await api.post(`/sessions/${sessionId}/logs`, {
          emotion:    entry.emotion,
          confidence: entry.confidence,
          engagement: entry.engagement,
        });
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
            emotion={latestResult?.emotion ?? null}
            confidence={latestResult?.confidence ?? null}
          />
          {latestResult && <EngagementBadge engagement={latestResult.engagement} emotion={latestResult.emotion} confidence={latestResult.confidence} />}
        </div>

        <div>
          <EmotionChart logs={logs} />
        </div>
      </div>
    </main>
  );
}
