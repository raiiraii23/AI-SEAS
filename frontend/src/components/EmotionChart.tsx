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

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

interface LogEntry {
  engagement: string;
  timestamp: number;
}

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

export default function EmotionChart({ logs }: Props) {
  const visible = logs.slice(-60); // last 60 data points

  const chartData = useMemo(() => ({
    labels: visible.map((_, i) => `${i + 1}`),
    datasets: [
      {
        label: "Engagement Level",
        data: visible.map((l) => ENGAGEMENT_VALUES[l.engagement] ?? -1),
        borderColor: visible.map((l) => COLOR_MAP[l.engagement] ?? "#334155"),
        backgroundColor: "rgba(59,130,246,0.08)",
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: visible.map((l) => COLOR_MAP[l.engagement] ?? "#334155"),
        fill: true,
        tension: 0.3,
      },
    ],
  }), [visible]);

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
        text: "Real-time Engagement Timeline",
        color: "#e2e8f0",
        font: { size: 14 },
      },
    },
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      {visible.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-12">No data yet — start a session.</p>
      ) : (
        <Line data={chartData} options={options} />
      )}
    </div>
  );
}
