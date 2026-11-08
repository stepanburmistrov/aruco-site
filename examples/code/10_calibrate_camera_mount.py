"""Привязка неподвижной камеры к системе координат стола по опорному ArUco."""

import cv2
import numpy as np

from aruco_pose_utils import (
    average_transforms,
    estimate_marker_pose,
    invert_transform,
    transform_from_pose,
)

CALIBRATION = "camera_calibration.npz"
OUTPUT_FILE = "camera_mount.npz"
CAMERA_INDEX = 0
DICT_NAME = "DICT_4X4_250"
ORIGIN_MARKER_ID = 0
ORIGIN_MARKER_LENGTH = 0.100  # сторона чёрного квадрата, метры
SAMPLES = 120
MAX_REPROJECTION_ERROR_PX = 1.5

# Система мира совпадает с опорным маркером:
# X — вдоль верхнего края вправо; Y — к верхнему краю; Z — из плоскости маркера.
calibration = np.load(CALIBRATION)
camera_matrix = calibration["camera_matrix"]
dist_coeffs = calibration["dist_coeffs"]
image_size = tuple(int(value) for value in calibration["image_size"])

dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DICT_NAME))
detector = cv2.aruco.ArucoDetector(
    dictionary, cv2.aruco.DetectorParameters()
)
cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, image_size[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, image_size[1])
if not cap.isOpened():
    raise RuntimeError("Камера недоступна")

samples = []
while len(samples) < SAMPLES:
    ok, frame = cap.read()
    if not ok:
        break
    corners, ids, _ = detector.detectMarkers(frame)
    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
        for marker_id, marker_corners in zip(ids.flatten(), corners):
            if marker_id != ORIGIN_MARKER_ID:
                continue
            pose = estimate_marker_pose(
                marker_corners,
                ORIGIN_MARKER_LENGTH,
                camera_matrix,
                dist_coeffs,
            )
            if pose is None:
                continue
            rvec, tvec, error_px = pose
            if error_px <= MAX_REPROJECTION_ERROR_PX:
                camera_from_world = transform_from_pose(rvec, tvec)
                world_from_camera = invert_transform(camera_from_world)
                samples.append(world_from_camera)
                cv2.drawFrameAxes(
                    frame,
                    camera_matrix,
                    dist_coeffs,
                    rvec,
                    tvec,
                    ORIGIN_MARKER_LENGTH * 0.7,
                )

    cv2.putText(
        frame,
        f"Origin ID {ORIGIN_MARKER_ID}: {len(samples)}/{SAMPLES}",
        (24, 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )
    cv2.imshow("Camera mount calibration — ESC to cancel", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
if len(samples) < max(30, SAMPLES // 2):
    raise RuntimeError(f"Недостаточно качественных измерений: {len(samples)}")

translations = np.stack([item[:3, 3] for item in samples])
median = np.median(translations, axis=0)
distance = np.linalg.norm(translations - median, axis=1)
threshold = max(0.005, float(np.median(distance) * 3.0))
filtered = [item for item, delta in zip(samples, distance) if delta <= threshold]
world_from_camera = average_transforms(filtered)

np.savez(
    OUTPUT_FILE,
    world_from_camera=world_from_camera,
    origin_marker_id=np.asarray(ORIGIN_MARKER_ID),
    origin_marker_length=np.asarray(ORIGIN_MARKER_LENGTH),
    samples_used=np.asarray(len(filtered)),
)
print(f"Сохранено: {OUTPUT_FILE}")
print("Положение камеры в системе опорного маркера, м:", world_from_camera[:3, 3])
