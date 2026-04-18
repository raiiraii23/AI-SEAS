"use client";

import { useEffect, useRef, useState, useCallback } from "react";
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
  const streamImgRef    = useRef<HTMLImageElement>(null);
  const canvasRef       = useRef<HTMLCanvasElement>(null);   // hidden canvas for frame capture
  const overlayRef      = useRef<HTMLCanvasElement>(null);   // visible canvas for drawing
  const intervalRef     = useRef<ReturnType<typeof setInterval> | null>(null);
  const rafRef          = useRef<number | null>(null);
  const detectorRef     = useRef<FaceDetector | null>(null);
  const emotionRef      = useRef<{ label: string; conf: number } | null>(null);
  const reconnectTimer  = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [detectorReady, setDetectorReady] = useState(false);
  const [streamStatus, setStreamStatus] = useState<"connecting" | "connected" | "error">("connecting");

  // ---- MJPEG stream connection with auto-reconnect ----
  const connectStream = useCallback(() => {
    const img = streamImgRef.current;
    if (!img) return;

    // Clear any pending reconnect
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }

    setStreamStatus("connecting");

    // Bust cache with a unique timestamp so the browser opens a fresh connection
    const streamUrl = `/api/ai/emotion/stream?t=${Date.now()}`;
    img.src = "";

    img.onload = () => {
      // For MJPEG multipart streams, onload fires each time a new frame arrives
      // in some browsers, or once on first frame in others. Either way, mark connected.
      setStreamStatus("connected");
    };

    img.onerror = () => {
      setStreamStatus("error");
      // Auto-reconnect after 3 seconds
      reconnectTimer.current = setTimeout(() => {
        connectStream();
      }, 3000);
    };

    img.src = streamUrl;
  }, []);

  // Connect on mount, clean up on unmount
  useEffect(() => {
    connectStream();

    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (streamImgRef.current) {
        streamImgRef.current.onload = null;
        streamImgRef.current.onerror = null;
        streamImgRef.current.src = "";
      }
    };
  }, [connectStream]);

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
      intervalRef.current = setInterval(captureFrame, captureIntervalMs);
      drawLoop();
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      const overlay = overlayRef.current;
      if (overlay) overlay.getContext("2d")!.clearRect(0, 0, overlay.width, overlay.height);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [isActive, detectorReady, captureIntervalMs]);

  function captureFrame() {
    const img    = streamImgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas || !img.naturalWidth) return;
    canvas.width  = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    try {
      ctx.drawImage(img, 0, 0);
      canvas.toBlob((blob) => { if (blob) onFrame(blob); }, "image/jpeg", 0.8);
    } catch {
      // CORS or other restriction
    }
  }

  function drawLoop() {
    const img     = streamImgRef.current;
    const overlay = overlayRef.current;
    const detector = detectorRef.current;

    if (!img || !overlay || !detector) {
      rafRef.current = requestAnimationFrame(drawLoop);
      return;
    }

    // Sync overlay size to displayed image size
    if (overlay.width !== img.clientWidth || overlay.height !== img.clientHeight) {
      overlay.width  = img.clientWidth;
      overlay.height = img.clientHeight;
    }

    const ctx = overlay.getContext("2d")!;
    ctx.clearRect(0, 0, overlay.width, overlay.height);

    try {
      const result = detector.detectForVideo(img, performance.now());
      for (const detection of result.detections) {
        const bb = detection.boundingBox;
        if (!bb) continue;

        // MediaPipe returns pixel coords relative to the source image dimensions
        const scaleX = overlay.width  / img.naturalWidth;
        const scaleY = overlay.height / img.naturalHeight;
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
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        ref={streamImgRef}
        className="w-full h-full object-contain"
        alt="Camera Stream"
        crossOrigin="anonymous"
        style={{ imageRendering: "auto" }}
      />
      <canvas ref={canvasRef} className="hidden" />
      <canvas ref={overlayRef} className="absolute inset-0 w-full h-full pointer-events-none" />

      {/* Status overlays */}
      {streamStatus === "connecting" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/70">
          <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mb-3" />
          <span className="text-blue-400 text-sm">Connecting to camera stream…</span>
        </div>
      )}
      {streamStatus === "error" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/70 text-center px-4">
          <span className="text-red-400 text-sm font-medium mb-1">Camera stream unavailable</span>
          <span className="text-gray-500 text-xs">Retrying automatically…</span>
        </div>
      )}
      {streamStatus === "connected" && (
        <div className="absolute top-2 right-2 flex items-center gap-1.5 text-xs text-green-400 bg-black/60 px-2 py-1 rounded">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          Live
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
