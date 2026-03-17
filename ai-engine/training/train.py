"""
Train a CNN for facial emotion recognition on FER-2013.

Usage:
    python training/train.py --train_dir data/train --test_dir data/test

The trained model is saved to models/emotion_model.h5
"""

import argparse
import os
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from preprocess import load_split_dataset

NUM_CLASSES = 7
IMG_SIZE = (48, 48, 1)
MODEL_OUT = os.path.join(os.path.dirname(__file__), "..", "models", "emotion_model.h5")


def build_model() -> tf.keras.Model:
    """
    Custom CNN architecture for 48x48 grayscale emotion recognition.
    Inspired by VGG-style blocks with batch normalization and dropout.
    """
    model = models.Sequential([
        # Block 1
        layers.Conv2D(32, (3, 3), padding="same", input_shape=IMG_SIZE),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.Conv2D(32, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Block 2
        layers.Conv2D(64, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.Conv2D(64, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Block 3
        layers.Conv2D(128, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.Conv2D(128, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Classifier
        layers.Flatten(),
        layers.Dense(256),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.Dropout(0.5),
        layers.Dense(NUM_CLASSES, activation="softmax"),
    ], name="seas_emotion_cnn")

    return model


def train(train_dir: str, test_dir: str, epochs: int = 60, batch_size: int = 64):
    print("[INFO] Loading dataset...")
    X_train, y_train, X_test, y_test = load_split_dataset(train_dir, test_dir)
    print(f"[INFO] Train: {X_train.shape}, Test: {X_test.shape}")

    y_train_cat = tf.keras.utils.to_categorical(y_train, NUM_CLASSES)
    y_test_cat = tf.keras.utils.to_categorical(y_test, NUM_CLASSES)

    # Data augmentation
    datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.1,
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
            monitor="val_accuracy", patience=15, restore_best_weights=True, verbose=1
        ),
    ]

    history = model.fit(
        datagen.flow(X_train, y_train_cat, batch_size=batch_size),
        validation_data=(X_test, y_test_cat),
        epochs=epochs,
        callbacks=cb,
    )

    loss, acc = model.evaluate(X_test, y_test_cat, verbose=0)
    print(f"\n[RESULT] Test Accuracy: {acc * 100:.2f}%  |  Test Loss: {loss:.4f}")
    print(f"[INFO] Model saved to {MODEL_OUT}")
    return history


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_dir", default="data/train")
    parser.add_argument("--test_dir", default="data/test")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch_size", type=int, default=64)
    args = parser.parse_args()

    train(args.train_dir, args.test_dir, args.epochs, args.batch_size)
