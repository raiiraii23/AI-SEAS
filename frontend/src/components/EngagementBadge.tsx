import clsx from "clsx";

interface Props {
  engagement: string;
  emotion: string;
  confidence: number;
}

const ENGAGEMENT_STYLES: Record<string, string> = {
  engaged:    "bg-green-900 border-green-600 text-green-300",
  neutral:    "bg-gray-800 border-gray-600 text-gray-300",
  confused:   "bg-amber-900 border-amber-600 text-amber-300",
  disengaged: "bg-red-900 border-red-600 text-red-300",
  unknown:    "bg-gray-800 border-gray-700 text-gray-400",
};

const ENGAGEMENT_LABELS: Record<string, string> = {
  engaged:    "Engaged",
  neutral:    "Neutral",
  confused:   "Confused",
  disengaged: "Disengaged",
  unknown:    "Unknown",
};

export default function EngagementBadge({ engagement, emotion, confidence }: Props) {
  const style = ENGAGEMENT_STYLES[engagement] ?? ENGAGEMENT_STYLES.unknown;

  return (
    <div className={clsx("rounded-xl border p-4 space-y-1", style)}>
      <div className="flex items-center justify-between">
        <span className="text-lg font-bold">{ENGAGEMENT_LABELS[engagement] ?? engagement}</span>
        <span className="text-xs opacity-70">{(confidence * 100).toFixed(1)}% confidence</span>
      </div>
      <p className="text-sm opacity-80 capitalize">Detected emotion: {emotion}</p>
    </div>
  );
}
