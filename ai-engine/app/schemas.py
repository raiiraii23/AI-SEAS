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


class PredictResponse(BaseModel):
    success: bool
    result: EmotionResult | None = None
    message: str = ""
