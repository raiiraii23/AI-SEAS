from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import numpy as np
import cv2
import asyncio

from app.schemas import PredictResponse, FaceResult, BoundingBox
from app.services.face_service import detect_and_crop_faces
from app.services.emotion_service import predict_emotions
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

    face_list = detect_and_crop_faces(frame)
    if not face_list:
        return PredictResponse(success=False, face_count=0, message="No faces detected.")

    rois   = [roi  for roi,  _    in face_list]
    bboxes = [bbox for _,    bbox in face_list]

    emotion_results = predict_emotions(rois)

    results = [
        FaceResult(
            face_index=i,
            bbox=BoundingBox(**bboxes[i]),
            emotion=emotion_results[i].emotion,
            confidence=emotion_results[i].confidence,
            engagement=emotion_results[i].engagement,
            all_scores=emotion_results[i].all_scores,
        )
        for i in range(len(face_list))
    ]

    return PredictResponse(success=True, results=results, face_count=len(results))


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
