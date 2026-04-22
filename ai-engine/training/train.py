"""
Train a CNN for facial emotion recognition on FER-2013.

Usage:
    python training/train.py --train_dir data/train --test_dir data/test

The trained model is saved to models/emotion_model.h5
"""

import argparse
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, callbacks
from collections import Counter
from preprocess import load_split_dataset

NUM_CLASSES = 7
IMG_SIZE = (48, 48, 1)
MODEL_OUT = os.path.join(os.path.dirname(__file__), "..", "models", "emotion_model.h5")


def build_model() -> tf.keras.Model:
    reg = tf.keras.regularizers.l2(1e-4)
    inputs = layers.Input(shape=IMG_SIZE)

    # Block 1 — 48x48 → 24x24
    x = layers.Conv2D(64, 3, padding="same", kernel_regularizer=reg)(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Conv2D(64, 3, padding="same", kernel_regularizer=reg)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.MaxPooling2D(2)(x)
    x = layers.Dropout(0.25)(x)

    # Block 2 — 24x24 → 12x12
    x = layers.Conv2D(128, 3, padding="same", kernel_regularizer=reg)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Conv2D(128, 3, padding="same", kernel_regularizer=reg)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.MaxPooling2D(2)(x)
    x = layers.Dropout(0.25)(x)

    # Block 3 — 12x12 → 6x6
    x = layers.Conv2D(256, 3, padding="same", kernel_regularizer=reg)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Conv2D(256, 3, padding="same", kernel_regularizer=reg)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.MaxPooling2D(2)(x)
    x = layers.Dropout(0.25)(x)

    # Classifier — GAP reduces overfitting vs Flatten
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(256, kernel_regularizer=reg)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(NUM_CLASSES, activation="softmax")(x)

    return tf.keras.Model(inputs=inputs, outputs=x, name="seas_emotion_cnn")


def compute_class_weights(y: np.ndarray) -> dict[int, float]:
    counts = Counter(y)
    total = len(y)
    n_classes = len(counts)
    return {cls: total / (n_classes * count) for cls, count in counts.items()}


def train(train_dir: str, test_dir: str, epochs: int = 80, batch_size: int = 64):
    print("[INFO] Loading dataset...")
    X_train, y_train, X_test, y_test = load_split_dataset(train_dir, test_dir)
    print(f"[INFO] Train: {X_train.shape}, Test: {X_test.shape}")

    class_weights = compute_class_weights(y_train)
    print(f"[INFO] Class weights: {class_weights}")

    # Label smoothing — FER-2013 labels are noisy (~30% inter-annotator disagreement)
    y_train_cat = tf.keras.utils.to_categorical(y_train, NUM_CLASSES)
    y_test_cat = tf.keras.utils.to_categorical(y_test, NUM_CLASSES)
    smooth = 0.1
    y_train_smooth = y_train_cat * (1 - smooth) + smooth / NUM_CLASSES

    datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rotation_range=15,
        width_shift_range=0.15,
        height_shift_range=0.15,
        horizontal_flip=True,
        zoom_range=0.15,
        brightness_range=[0.8, 1.2],
        fill_mode="nearest",
    )
    datagen.fit(X_train)

    model = build_model()
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    cb = [
        callbacks.ModelCheckpoint(
            MODEL_OUT, monitor="val_accuracy", save_best_only=True, verbose=1
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6, verbose=1
        ),
        callbacks.EarlyStopping(
            monitor="val_accuracy", patience=20, restore_best_weights=True, verbose=1
        ),
    ]

    history = model.fit(
        datagen.flow(X_train, y_train_smooth, batch_size=batch_size),
        validation_data=(X_test, y_test_cat),
        epochs=epochs,
        callbacks=cb,
        class_weight=class_weights,
    )

    loss, acc = model.evaluate(X_test, y_test_cat, verbose=0)
    print(f"\n[RESULT] Test Accuracy: {acc * 100:.2f}%  |  Test Loss: {loss:.4f}")
    print(f"[INFO] Model saved to {MODEL_OUT}")
    return history


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_dir", default="data/train")
    parser.add_argument("--test_dir", default="data/test")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch_size", type=int, default=64)
    args = parser.parse_args()

    train(args.train_dir, args.test_dir, args.epochs, args.batch_size)
