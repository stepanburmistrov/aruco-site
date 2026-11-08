"""Съёмка разнообразных кадров ChArUco для калибровки камеры."""

from pathlib import Path
import time

import cv2
import numpy as np

CAMERA_INDEX = 0
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
OUTPUT_DIR = Path("calibration_images")

DICT_NAME = "DICT_4X4_250"
SQUARES_X = 5
SQUARES_Y = 7
SQUARE_LENGTH = 0.0350  # метры
MARKER_LENGTH = 0.0245  # метры

AUTO_CAPTURE = True
MIN_CHARUCO_CORNERS = 12
MIN_SHARPNESS = 80.0
MIN_SECONDS_BETWEEN_SAVES = 1.2
MIN_VIEW_DIFFERENCE = 0.07

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DICT_NAME))
board = cv2.aruco.CharucoBoard(
    (SQUARES_X, SQUARES_Y), SQUARE_LENGTH, MARKER_LENGTH, dictionary
)
if hasattr(board, "setLegacyPattern"):
    board.setLegacyPattern(False)
detector = cv2.aruco.CharucoDetector(board)

cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
if not cap.isOpened():
    raise RuntimeError("Камера недоступна")

last_saved_at = 0.0
last_descriptor = None
saved = len(list(OUTPUT_DIR.glob("frame_*.png")))


def view_descriptor(corners, frame_shape):
    points = corners.reshape(-1, 2)
    height, width = frame_shape[:2]
    center = points.mean(axis=0) / np.array([width, height])
    span = np.ptp(points, axis=0) / np.array([width, height])
    return np.r_[center, span]


while True:
    ok, frame = cap.read()
    if not ok:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    charuco_corners, charuco_ids, marker_corners, marker_ids = detector.detectBoard(
        frame
    )
    corner_count = 0 if charuco_ids is None else len(charuco_ids)
    valid = corner_count >= MIN_CHARUCO_CORNERS and sharpness >= MIN_SHARPNESS

    preview = frame.copy()
    if marker_ids is not None:
        cv2.aruco.drawDetectedMarkers(preview, marker_corners, marker_ids)
    if charuco_ids is not None:
        cv2.aruco.drawDetectedCornersCharuco(
            preview, charuco_corners, charuco_ids, (0, 255, 0)
        )

    descriptor = None
    different = True
    if charuco_corners is not None:
        descriptor = view_descriptor(charuco_corners, frame.shape)
        if last_descriptor is not None:
            different = np.linalg.norm(descriptor - last_descriptor) >= MIN_VIEW_DIFFERENCE

    now = time.monotonic()
    auto_save = (
        AUTO_CAPTURE
        and valid
        and different
        and now - last_saved_at >= MIN_SECONDS_BETWEEN_SAVES
    )
    color = (0, 220, 0) if valid else (0, 80, 255)
    cv2.putText(
        preview,
        f"saved={saved} corners={corner_count} sharpness={sharpness:.0f}",
        (24, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        preview,
        "SPACE: save   ESC: exit",
        (24, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.imshow("ChArUco calibration capture", preview)

    key = cv2.waitKey(1) & 0xFF
    manual_save = key == ord(" ") and valid
    if auto_save or manual_save:
        saved += 1
        path = OUTPUT_DIR / f"frame_{saved:03d}.png"
        cv2.imwrite(str(path), frame)
        last_saved_at = now
        last_descriptor = descriptor
        print(f"Сохранён {path} — углов: {corner_count}, резкость: {sharpness:.0f}")

    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()
