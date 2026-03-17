import os
import logging
import tensorflow as tf
from app.config import settings

logger = logging.getLogger(__name__)

_model: tf.keras.Model | None = None


def _build_dummy_model() -> tf.keras.Model:
    """
    Creates an untrained model with the correct input/output shape.
    Used automatically when no trained model is found.
    Predictions will be random — replace by running training/train.py with FER-2013.
    """
    from tensorflow.keras import layers, models as km
    model = km.Sequential([
        layers.Conv2D(32, (3, 3), padding="same", activation="relu", input_shape=(48, 48, 1)),
        layers.MaxPooling2D(2, 2),
        layers.Conv2D(64, (3, 3), padding="same", activation="relu"),
        layers.MaxPooling2D(2, 2),
        layers.Flatten(),
        layers.Dense(128, activation="relu"),
        layers.Dense(7, activation="softmax"),
    ], name="seas_emotion_cnn_dummy")
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    return model


def load_model_on_startup() -> None:
    global _model
    path = settings.model_path
    if os.path.exists(path):
        logger.info(f"Loading emotion model from {path}")
        _model = tf.keras.models.load_model(path)
        logger.info("Model loaded successfully.")
    else:
        logger.warning(
            f"No trained model found at {path}. "
            "Generating a dummy model so the service boots. "
            "Predictions will be RANDOM until you train a real model via training/train.py."
        )
        _model = _build_dummy_model()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _model.save(path)
        logger.warning(f"Dummy model saved to {path}. Replace it with a trained model.")


def get_model() -> tf.keras.Model:
    if _model is None:
        raise RuntimeError(
            "Emotion model is not loaded. "
            "Ensure the model file exists at the configured MODEL_PATH."
        )
    return _model
