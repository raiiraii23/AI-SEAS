import cv2
import mediapipe as mp
import numpy as np

mp_face_detection = mp.solutions.face_detection

_detector = mp_face_detection.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.6,
)

TARGET_SIZE = (48, 48)
_MIN_FACE_PX = 30
_PAD_RATIO = 0.2
_clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))


def detect_and_crop_face(frame: np.ndarray) -> tuple[np.ndarray, dict] | tuple[None, None]:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = _detector.process(rgb)

    if not results.detections:
        return None, None

    best = max(results.detections, key=lambda d: d.score[0])
    bboxC = best.location_data.relative_bounding_box
    h, w = frame.shape[:2]

    bw_px = int(bboxC.width * w)
    bh_px = int(bboxC.height * h)
    if bw_px < _MIN_FACE_PX or bh_px < _MIN_FACE_PX:
        return None, None

    pad_x = int(bw_px * _PAD_RATIO)
    pad_y = int(bh_px * _PAD_RATIO)

    x = max(0, int(bboxC.xmin * w) - pad_x)
    y = max(0, int(bboxC.ymin * h) - pad_y)
    x2 = min(w, int(bboxC.xmin * w) + bw_px + pad_x)
    y2 = min(h, int(bboxC.ymin * h) + bh_px + pad_y)

    face = frame[y:y2, x:x2]
    if face.size == 0:
        return None, None

    bbox = {
        "x": bboxC.xmin,
        "y": bboxC.ymin,
        "width": bboxC.width,
        "height": bboxC.height,
    }

    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    gray = _clahe.apply(gray)
    resized = cv2.resize(gray, TARGET_SIZE, interpolation=cv2.INTER_AREA)
    return resized, bbox
