"use client";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { useMemo } from "react";
import { LogEntry } from "@/lib/types";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

interface Props {
  logs: LogEntry[];
}

const ENGAGEMENT_VALUES: Record<string, number> = {
  engaged:    3,
  neutral:    2,
  confused:   1,
  disengaged: 0,
  unknown:    -1,
};

const COLOR_MAP: Record<string, string> = {
  engaged:    "#22c55e",
  neutral:    "#64748b",
  confused:   "#f59e0b",
  disengaged: "#ef4444",
};

function valueToColor(v: number): string {
  if (v >= 2.5) return COLOR_MAP.engaged;
  if (v >= 1.5) return COLOR_MAP.neutral;
  if (v >= 0.5) return COLOR_MAP.confused;
  return COLOR_MAP.disengaged;
}

export default function EmotionChart({ logs }: Props) {
  // Group entries by timestamp (all faces in one frame share the same timestamp),
  // average their engagement values, then take the last 60 frames.
  const frameData = useMemo(() => {
    const frameMap = new Map<number, number[]>();
    for (const log of logs) {
      const v = ENGAGEMENT_VALUES[log.engagement] ?? -1;
      if (v < 0) continue;
      if (!frameMap.has(log.timestamp)) frameMap.set(log.timestamp, []);
      frameMap.get(log.timestamp)!.push(v);
    }
    return Array.from(frameMap.entries())
      .sort(([a], [b]) => a - b)
      .slice(-60)
      .map(([, values]) => values.reduce((s, v) => s + v, 0) / values.length);
  }, [logs]);

  const pointColors = frameData.map(valueToColor);

  const chartData = useMemo(() => ({
    labels: frameData.map((_, i) => `${i + 1}`),
    datasets: [
      {
        label: "Class Engagement",
        data: frameData,
        borderColor: pointColors,
        backgroundColor: "rgba(59,130,246,0.08)",
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: pointColors,
        fill: true,
        tension: 0.3,
      },
    ],
  }), [frameData, pointColors]);

  const options = {
    responsive: true,
    animation: { duration: 200 } as const,
    scales: {
      y: {
        min: -0.5,
        max: 3.5,
        ticks: {
          stepSize: 1,
          callback: (v: number | string) => {
            const map: Record<number, string> = { 3: "Engaged", 2: "Neutral", 1: "Confused", 0: "Disengaged" };
            return map[Number(v)] ?? "";
          },
          color: "#94a3b8",
        },
        grid: { color: "#1e293b" },
      },
      x: { display: false },
    },
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: "Class Engagement Over Time",
        color: "#e2e8f0",
        font: { size: 14 },
      },
    },
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      {frameData.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-12">No data yet — start a session.</p>
      ) : (
        <Line data={chartData} options={options} />
      )}
    </div>
  );
}
