"use client";

import { FaceResult } from "@/lib/types";

interface Props {
  faceResults: FaceResult[];
}

const ENGAGEMENT_STYLES: Record<string, string> = {
  engaged:    "border-green-700 bg-green-950 text-green-300",
  neutral:    "border-gray-700 bg-gray-900 text-gray-300",
  confused:   "border-amber-700 bg-amber-950 text-amber-300",
  disengaged: "border-red-700 bg-red-950 text-red-300",
};

const ENGAGEMENT_LABELS: Record<string, string> = {
  engaged:    "Engaged",
  neutral:    "Neutral",
  confused:   "Confused",
  disengaged: "Disengaged",
};

export default function ClassroomStats({ faceResults }: Props) {
  if (faceResults.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-sm text-gray-500 text-center">
        No faces detected — point the camera at the class.
      </div>
    );
  }

  const counts = faceResults.reduce<Record<string, number>>((acc, f) => {
    acc[f.engagement] = (acc[f.engagement] ?? 0) + 1;
    return acc;
  }, {});

  const total      = faceResults.length;
  const engaged    = counts.engaged    ?? 0;
  const neutral    = counts.neutral    ?? 0;
  const confused   = counts.confused   ?? 0;
  const disengaged = counts.disengaged ?? 0;
  const engagedPct = total > 0 ? Math.round((engaged / total) * 100) : 0;

  return (
    <div className="space-y-3">
      {/* Aggregate overview */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <p className="text-xs text-gray-400 mb-3 font-medium uppercase tracking-wide">
          Class Overview — {total} student{total !== 1 ? "s" : ""} detected
        </p>
        <div className="grid grid-cols-4 gap-2 text-center mb-3">
          {[
            { label: "Engaged",    count: engaged,    color: "text-green-400" },
            { label: "Neutral",    count: neutral,    color: "text-gray-400"  },
            { label: "Confused",   count: confused,   color: "text-amber-400" },
            { label: "Disengaged", count: disengaged, color: "text-red-400"   },
          ].map(({ label, count, color }) => (
            <div key={label}>
              <p className={`text-2xl font-bold ${color}`}>{count}</p>
              <p className="text-xs text-gray-500">{label}</p>
            </div>
          ))}
        </div>
        {/* Engagement bar */}
        <div className="w-full h-2 rounded-full bg-gray-800 overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all duration-500"
            style={{ width: `${engagedPct}%` }}
          />
        </div>
        <p className="mt-1.5 text-xs text-gray-400 text-center">
          {engaged} of {total} students engaged ({engagedPct}%)
        </p>
      </div>

      {/* Per-student cards */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {faceResults.map((face) => {
          const style = ENGAGEMENT_STYLES[face.engagement] ?? ENGAGEMENT_STYLES.neutral;
          const label = ENGAGEMENT_LABELS[face.engagement] ?? face.engagement;
          return (
            <div
              key={face.face_index}
              className={`rounded-lg border p-3 space-y-0.5 ${style}`}
            >
              <p className="text-xs font-semibold opacity-60">Student #{face.face_index + 1}</p>
              <p className="text-sm font-bold">{label}</p>
              <p className="text-xs capitalize opacity-70">{face.emotion}</p>
              <p className="text-xs opacity-50">{(face.confidence * 100).toFixed(0)}% conf.</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
