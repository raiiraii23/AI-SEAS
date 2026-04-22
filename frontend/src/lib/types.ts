export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface FaceResult {
  face_index: number;
  bbox: BoundingBox;
  emotion: string;
  confidence: number;
  engagement: string;
  all_scores: Record<string, number>;
}

export interface LogEntry {
  face_index: number;
  emotion: string;
  confidence: number;
  engagement: string;
  timestamp: number;
}
