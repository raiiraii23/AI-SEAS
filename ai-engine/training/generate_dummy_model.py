"""
Generates a dummy (untrained) model with the correct input/output shape.
Use this to boot the system for UI/integration testing before real training.
Predictions will be random — replace with the real model after training.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tensorflow as tf
from tensorflow.keras import layers, models

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "emotion_model.h5")

model = models.Sequential([
    layers.Conv2D(32, (3, 3), padding="same", activation="relu", input_shape=(48, 48, 1)),
    layers.MaxPooling2D(2, 2),
    layers.Conv2D(64, (3, 3), padding="same", activation="relu"),
    layers.MaxPooling2D(2, 2),
    layers.Flatten(),
    layers.Dense(128, activation="relu"),
    layers.Dense(7, activation="softmax"),
], name="seas_emotion_cnn_dummy")

model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
model.save(OUT_PATH)
print(f"Dummy model saved to: {OUT_PATH}")
print("NOTE: This model is untrained. Run training/train.py with FER-2013 for real predictions.")
