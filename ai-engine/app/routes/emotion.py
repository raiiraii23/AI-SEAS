from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import numpy as np
import cv2
import asyncio

from app.schemas import PredictResponse, EmotionResult, BoundingBox
from app.services.face_service import detect_and_crop_face
from app.services.emotion_service import predict_emotion
from app.services.rtsp_stream import get_rtsp_manager

router = APIRouter()


@router.get("/status")
async def stream_status():
    """Check if RTSP stream is connected."""
    manager = get_rtsp_manager()
    if not manager:
        return {"connected": False, "error": "Stream manager not initialized"}
    return {
        "connected": manager.is_connected(),
        "has_frames": manager.get_frame() is not None,
        "rtsp_url": "***redacted***",
    }


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


@router.get("/stream")
async def video_stream():
    """Stream RTSP video as MJPEG for browser display."""
    boundary = b"--frame"

    async def frame_generator():
        manager = get_rtsp_manager()
        if not manager:
            yield b"--frame\r\nContent-Type: text/plain\r\nContent-Length: 21\r\n\r\nRTSP stream not ready\r\n"
            return

        last_frame = None
        while True:
            frame_bytes = manager.get_frame()
            if frame_bytes is None:
                await asyncio.sleep(0.05)
                continue

            if frame_bytes is last_frame:
                await asyncio.sleep(0.01)
                continue
            last_frame = frame_bytes

            yield (
                boundary + b"\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(frame_bytes)).encode() + b"\r\n\r\n"
                + frame_bytes + b"\r\n"
            )
            await asyncio.sleep(0.01)

    return StreamingResponse(
        frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame"
    )
