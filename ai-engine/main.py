from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.routes import emotion
from app.models.model_loader import load_model_on_startup
from app.services.rtsp_stream import init_rtsp_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model_on_startup()
    rtsp_url = os.getenv("RTSP_URL", "rtsp://admin:Raiiraii23!@192.168.8.101:554/stream1")
    init_rtsp_manager(rtsp_url)
    yield


app = FastAPI(
    title="SEAS AI Engine",
    description="Facial Emotion Recognition API for Student Engagement Analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(emotion.router, prefix="/emotion", tags=["Emotion"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "seas-ai-engine"}
