from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_path: str = "/app/models/emotion_model.h5"
    port: int = 8000
    # Emotion labels matching training dataset order (FER-2013)
    emotion_labels: list[str] = [
        "angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"
    ]
    # Map raw emotions to engagement states
    engagement_map: dict[str, str] = {
        "happy": "engaged",
        "surprise": "engaged",
        "neutral": "neutral",
        "fear": "confused",
        "angry": "confused",
        "sad": "disengaged",
        "disgust": "disengaged",
    }

    class Config:
        env_file = ".env"


settings = Settings()
