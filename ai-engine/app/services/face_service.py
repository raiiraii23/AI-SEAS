import cv2
import mediapipe as mp
import numpy as np

mp_face_detection = mp.solutions.face_detection

_detector = mp_face_detection.FaceDetection(
    model_selection=0,  # short-range model (< 2m, suitable for webcam)
    min_detection_confidence=0.5,
)

TARGET_SIZE = (48, 48)  # FER-2013 input size


def detect_and_crop_face(frame: np.ndarray) -> tuple[np.ndarray, dict] | tuple[None, None]:
    """
    Detect the largest face in the frame using MediaPipe and return
    a grayscale 48x48 ROI suitable for CNN inference plus the relative bbox.
    Returns (None, None) if no face is detected.
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = _detector.process(rgb)

    if not results.detections:
        return None, None

    # Pick the detection with the highest confidence
    best = max(results.detections, key=lambda d: d.score[0])
    bboxC = best.location_data.relative_bounding_box
    h, w = frame.shape[:2]

    x = max(0, int(bboxC.xmin * w))
    y = max(0, int(bboxC.ymin * h))
    bw = min(int(bboxC.width * w), w - x)
    bh = min(int(bboxC.height * h), h - y)

    face = frame[y : y + bh, x : x + bw]
    if face.size == 0:
        return None, None

    bbox = {
        "x": bboxC.xmin,
        "y": bboxC.ymin,
        "width": bboxC.width,
        "height": bboxC.height,
    }

    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, TARGET_SIZE, interpolation=cv2.INTER_AREA)
    return resized, bbox
