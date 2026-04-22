import numpy as np
import tensorflow as tf
from app.models.model_loader import get_model
from app.config import settings
from app.schemas import EmotionResult


def predict_emotion(face_roi: np.ndarray) -> EmotionResult:
    model = get_model()

    img = face_roi.astype("float32") / 255.0
    img = np.expand_dims(img, axis=(0, -1))

    # Direct call is ~10-50x faster than model.predict() for single images
    predictions = model(tf.constant(img), training=False)[0].numpy()

    top_idx = int(np.argmax(predictions))
    top_emotion = settings.emotion_labels[top_idx]
    confidence = float(predictions[top_idx])
    engagement = settings.engagement_map.get(top_emotion, "neutral")

    all_scores = {
        label: round(float(predictions[i]), 4)
        for i, label in enumerate(settings.emotion_labels)
    }

    return EmotionResult(
        emotion=top_emotion,
        confidence=round(confidence, 4),
        engagement=engagement,
        all_scores=all_scores,
        face_detected=False,
    )
