"use client";

import { useEffect, useRef, useState } from "react";
import { FaceDetector, FilesetResolver } from "@mediapipe/tasks-vision";

interface Props {
  isActive: boolean;
  onFrame: (blob: Blob) => void;
  captureIntervalMs?: number;
  emotion?: string | null;
  confidence?: number | null;
}

const LABEL_COLORS: Record<string, string> = {
  happy:     "#22c55e",
  confused:  "#f59e0b",
  bored:     "#6b7280",
  attentive: "#3b82f6",
};

export default function WebcamCapture({
  isActive,
  onFrame,
  captureIntervalMs = 1000,
  emotion,
  confidence,
}: Props) {
  const videoRef    = useRef<HTMLVideoElement>(null);
  const captureRef  = useRef<HTMLCanvasElement>(null);   // hidden, for JPEG frames
  const overlayRef  = useRef<HTMLCanvasElement>(null);   // visible, for drawing
  const streamRef   = useRef<MediaStream | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const rafRef      = useRef<number | null>(null);
  const detectorRef = useRef<FaceDetector | null>(null);
  const emotionRef  = useRef<{ label: string; conf: number } | null>(null);

  const [detectorReady, setDetectorReady] = useState(false);

  // Keep a ref so the draw loop always has the latest emotion without re-creating it
  useEffect(() => {
    if (emotion) emotionRef.current = { label: emotion, conf: confidence ?? 0 };
    else emotionRef.current = null;
  }, [emotion, confidence]);

  // Load MediaPipe FaceDetector once on mount
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const vision = await FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/wasm"
      );
      const detector = await FaceDetector.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath:
            "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
          delegate: "GPU",
        },
        runningMode: "VIDEO",
        minDetectionConfidence: 0.5,
      });
      if (!cancelled) {
        detectorRef.current = detector;
        setDetectorReady(true);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (isActive && detectorReady) {
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
  }, [isActive, detectorReady]);

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      // Emotion-prediction capture loop (throttled)
      intervalRef.current = setInterval(captureFrame, captureIntervalMs);
      // Real-time detection draw loop
      drawLoop();
    } catch (err) {
      console.error("Camera access denied:", err);
    }
  }

  function stopCamera() {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    const overlay = overlayRef.current;
    if (overlay) overlay.getContext("2d")!.clearRect(0, 0, overlay.width, overlay.height);
  }

  function captureFrame() {
    const video  = videoRef.current;
    const canvas = captureRef.current;
    if (!video || !canvas || video.readyState < 2) return;
    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")!.drawImage(video, 0, 0);
    canvas.toBlob((blob) => { if (blob) onFrame(blob); }, "image/jpeg", 0.8);
  }

  function drawLoop() {
    const video   = videoRef.current;
    const overlay = overlayRef.current;
    const detector = detectorRef.current;

    if (!video || !overlay || !detector || video.readyState < 2) {
      rafRef.current = requestAnimationFrame(drawLoop);
      return;
    }

    // Sync overlay size to displayed video size
    if (overlay.width !== video.clientWidth || overlay.height !== video.clientHeight) {
      overlay.width  = video.clientWidth;
      overlay.height = video.clientHeight;
    }

    const ctx = overlay.getContext("2d")!;
    ctx.clearRect(0, 0, overlay.width, overlay.height);

    try {
      const result = detector.detectForVideo(video, performance.now());
      for (const detection of result.detections) {
        const bb = detection.boundingBox;
        if (!bb) continue;

        // MediaPipe returns pixel coords relative to the source video dimensions
        const scaleX = overlay.width  / video.videoWidth;
        const scaleY = overlay.height / video.videoHeight;
        const x = bb.originX * scaleX;
        const y = bb.originY * scaleY;
        const w = bb.width   * scaleX;
        const h = bb.height  * scaleY;

        const em   = emotionRef.current;
        const color = em ? (LABEL_COLORS[em.label.toLowerCase()] ?? "#22c55e") : "#22c55e";

        // Bounding box
        ctx.strokeStyle = color;
        ctx.lineWidth   = 2.5;
        ctx.strokeRect(x, y, w, h);

        // Corner accents for a nicer look
        const cs = Math.min(w, h) * 0.15;
        ctx.lineWidth = 3;
        [[x, y], [x + w, y], [x, y + h], [x + w, y + h]].forEach(([cx, cy], i) => {
          ctx.beginPath();
          ctx.moveTo(cx + (i % 2 === 0 ? cs : -cs), cy);
          ctx.lineTo(cx, cy);
          ctx.lineTo(cx, cy + (i < 2 ? cs : -cs));
          ctx.stroke();
        });

        // Emotion label
        if (em) {
          const label = `${em.label}  ${(em.conf * 100).toFixed(0)}%`;
          ctx.font = "bold 13px monospace";
          const tw = ctx.measureText(label).width;
          const pad = 5;
          const labelY = y > 22 ? y - 6 : y + h + 18;

          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.roundRect(x, labelY - 15, tw + pad * 2, 19, 4);
          ctx.fill();

          ctx.fillStyle = "#000";
          ctx.fillText(label, x + pad, labelY);
        }
      }
    } catch {
      // detector not warmed up yet
    }

    rafRef.current = requestAnimationFrame(drawLoop);
  }

  return (
    <div className="relative bg-gray-900 rounded-xl overflow-hidden border border-gray-800 aspect-video flex items-center justify-center">
      <video ref={videoRef} muted playsInline className="w-full h-full object-cover" />
      <canvas ref={captureRef} className="hidden" />
      <canvas ref={overlayRef} className="absolute inset-0 w-full h-full pointer-events-none" />
      {!isActive && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-500 text-sm">
          Camera inactive — start a session to begin
        </div>
      )}
      {isActive && !detectorReady && (
        <div className="absolute bottom-2 left-2 text-xs text-yellow-400 bg-black/60 px-2 py-1 rounded">
          Loading face detector…
        </div>
      )}
    </div>
  );
}
