"""
Preprocessing utilities for the FER-2013 dataset.

Expected dataset structure:
    data/
        train/
            angry/   disgust/   fear/   happy/   neutral/   sad/   surprise/
        test/
            angry/   disgust/   fear/   happy/   neutral/   sad/   surprise/

Download FER-2013 from Kaggle:
    kaggle datasets download -d msambare/fer2013
"""

import os
import numpy as np
import cv2
from sklearn.model_selection import train_test_split

EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
IMG_SIZE = (48, 48)


def load_dataset(data_dir: str) -> tuple[np.ndarray, np.ndarray]:
    images, labels = [], []

    for label_idx, emotion in enumerate(EMOTION_LABELS):
        folder = os.path.join(data_dir, emotion)
        if not os.path.isdir(folder):
            print(f"[Warning] Missing folder: {folder}")
            continue

        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            img = cv2.imread(fpath, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            img = cv2.resize(img, IMG_SIZE)
            images.append(img)
            labels.append(label_idx)

    X = np.array(images, dtype="float32") / 255.0
    X = np.expand_dims(X, -1)  # (N, 48, 48, 1)
    y = np.array(labels, dtype="int32")
    return X, y


def load_split_dataset(
    train_dir: str, test_dir: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    X_train, y_train = load_dataset(train_dir)
    X_test, y_test = load_dataset(test_dir)
    return X_train, y_train, X_test, y_test
