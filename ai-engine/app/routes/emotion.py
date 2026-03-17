from fastapi import APIRouter, File, UploadFile, HTTPException
import numpy as np
import cv2

from app.schemas import PredictResponse, EmotionResult, BoundingBox
from app.services.face_service import detect_and_crop_face
from app.services.emotion_service import predict_emotion

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode image.")

    face_roi, bbox_dict = detect_and_crop_face(frame)
    if face_roi is None:
        return PredictResponse(
            success=False,
            result=EmotionResult(
                emotion="unknown",
                confidence=0.0,
                engagement="unknown",
                all_scores={},
                face_detected=False,
            ),
            message="No face detected in the image.",
        )

    result = predict_emotion(face_roi)
    result.face_detected = True
    result.bbox = BoundingBox(**bbox_dict)

    return PredictResponse(success=True, result=result)
