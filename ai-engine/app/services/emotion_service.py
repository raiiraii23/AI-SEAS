import numpy as np
from app.models.model_loader import get_model
from app.config import settings
from app.schemas import EmotionResult


def predict_emotion(face_roi: np.ndarray) -> EmotionResult:
    """
    Run CNN inference on a 48x48 grayscale face ROI.
    Returns EmotionResult with top emotion, confidence, engagement label,
    and full score distribution.
    """
    model = get_model()

    # Normalize and reshape to (1, 48, 48, 1)
    img = face_roi.astype("float32") / 255.0
    img = np.expand_dims(img, axis=(0, -1))  # (1, 48, 48, 1)

    predictions = model.predict(img, verbose=0)[0]  # shape: (7,)

    top_idx = int(np.argmax(predictions))
    top_emotion = settings.emotion_labels[top_idx]
    confidence = float(predictions[top_idx])
    engagement = settings.engagement_map.get(top_emotion, "neutral")

    all_scores = {
        label: float(predictions[i])
        for i, label in enumerate(settings.emotion_labels)
    }

    return EmotionResult(
        emotion=top_emotion,
        confidence=round(confidence, 4),
        engagement=engagement,
        all_scores=all_scores,
        face_detected=False,  # caller sets this to True
    )
