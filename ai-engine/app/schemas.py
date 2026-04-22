from pydantic import BaseModel


class BoundingBox(BaseModel):
    x: float       # relative 0-1
    y: float
    width: float
    height: float


class EmotionResult(BaseModel):
    emotion: str
    confidence: float
    engagement: str
    all_scores: dict[str, float]
    face_detected: bool
    bbox: BoundingBox | None = None


class FaceResult(BaseModel):
    face_index: int
    bbox: BoundingBox
    emotion: str
    confidence: float
    engagement: str
    all_scores: dict[str, float]


class PredictResponse(BaseModel):
    success: bool
    results: list[FaceResult] = []
    face_count: int = 0
    message: str = ""
