import numpy as np
import tensorflow as tf
from app.models.model_loader import get_model
from app.config import settings
from app.schemas import EmotionResult


def predict_emotions(face_rois: list[np.ndarray]) -> list[EmotionResult]:
    """Run a single batched inference for all face ROIs."""
    if not face_rois:
        return []

    model = get_model()

    # Stack into (N, 48, 48, 1) batch
    batch = np.stack([f.astype("float32") / 255.0 for f in face_rois])
    batch = batch[..., np.newaxis]

    # Single forward pass for all faces
    predictions = model(tf.constant(batch), training=False).numpy()

    results = []
    for preds in predictions:
        top_idx = int(np.argmax(preds))
        top_emotion = settings.emotion_labels[top_idx]
        confidence = float(preds[top_idx])
        engagement = settings.engagement_map.get(top_emotion, "neutral")

        all_scores = {
            label: round(float(preds[i]), 4)
            for i, label in enumerate(settings.emotion_labels)
        }

        results.append(EmotionResult(
            emotion=top_emotion,
            confidence=round(confidence, 4),
            engagement=engagement,
            all_scores=all_scores,
            face_detected=True,
        ))

    return results


def predict_emotion(face_roi: np.ndarray) -> EmotionResult:
    """Single-face wrapper kept for compatibility."""
    return predict_emotions([face_roi])[0]
