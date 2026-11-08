"""Живые X/Y/Z и ориентация каждого ArUco относительно камеры."""

import time

import cv2
import numpy as np

from aruco_pose_utils import estimate_marker_pose, euler_xyz_degrees

CALIBRATION = "camera_calibration.npz"
CAMERA_INDEX = 0
DICT_NAME = "DICT_4X4_250"
MARKER_LENGTH = 0.060  # сторона чёрного квадрата, метры
PRINT_PERIOD = 0.5

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

last_print = 0.0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    if (frame.shape[1], frame.shape[0]) != image_size:
        raise RuntimeError(
            f"Камера дала {frame.shape[1]}×{frame.shape[0]}, "
            f"а калибровка выполнена для {image_size[0]}×{image_size[1]}"
        )

    corners, ids, _ = detector.detectMarkers(frame)
    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
        rows = []
        for marker_id, marker_corners in zip(ids.flatten(), corners):
            pose = estimate_marker_pose(
                marker_corners, MARKER_LENGTH, camera_matrix, dist_coeffs
            )
            if pose is None:
                continue
            rvec, tvec, error_px = pose
            rotation, _ = cv2.Rodrigues(rvec)
            angles = euler_xyz_degrees(rotation)
            x, y, z = tvec.reshape(3)
            rows.append((marker_id, x, y, z, angles, error_px))
            cv2.drawFrameAxes(
                frame,
                camera_matrix,
                dist_coeffs,
                rvec,
                tvec,
                MARKER_LENGTH * 0.7,
            )
            center = marker_corners.reshape(4, 2).mean(axis=0).astype(int)
            cv2.putText(
                frame,
                f"ID {marker_id}: {z:.3f} m",
                tuple(center),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

        now = time.monotonic()
        if rows and now - last_print >= PRINT_PERIOD:
            for marker_id, x, y, z, angles, error_px in rows:
                print(
                    f"ID={marker_id:3d}  X={x:+.4f}  Y={y:+.4f}  Z={z:+.4f} m  "
                    f"roll/pitch/yaw={angles.round(1)}°  err={error_px:.2f}px"
                )
            last_print = now

    cv2.imshow("ArUco 3D — ESC to exit", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
