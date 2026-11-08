"""3D-позиция ArUco в координатах стола/стенда, а не камеры."""

import time

import cv2
import numpy as np

from aruco_pose_utils import (
    estimate_marker_pose,
    euler_xyz_degrees,
    transform_from_pose,
)

CALIBRATION = "camera_calibration.npz"
CAMERA_MOUNT = "camera_mount.npz"
CAMERA_INDEX = 0
DICT_NAME = "DICT_4X4_250"
DEFAULT_MARKER_LENGTH = 0.060
MARKER_LENGTHS = {0: 0.100}  # при разных размерах: ID -> метры
MAX_REPROJECTION_ERROR_PX = 2.0
PRINT_PERIOD = 0.5

calibration = np.load(CALIBRATION)
camera_matrix = calibration["camera_matrix"]
dist_coeffs = calibration["dist_coeffs"]
image_size = tuple(int(value) for value in calibration["image_size"])
world_from_camera = np.load(CAMERA_MOUNT)["world_from_camera"]

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
    corners, ids, _ = detector.detectMarkers(frame)
    output_rows = []
    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
        for marker_id, marker_corners in zip(ids.flatten(), corners):
            marker_length = MARKER_LENGTHS.get(
                int(marker_id), DEFAULT_MARKER_LENGTH
            )
            pose = estimate_marker_pose(
                marker_corners, marker_length, camera_matrix, dist_coeffs
            )
            if pose is None:
                continue
            rvec, tvec, error_px = pose
            if error_px > MAX_REPROJECTION_ERROR_PX:
                continue

            camera_from_marker = transform_from_pose(rvec, tvec)
            world_from_marker = world_from_camera @ camera_from_marker
            position = world_from_marker[:3, 3]
            angles = euler_xyz_degrees(world_from_marker[:3, :3])
            output_rows.append((int(marker_id), position, angles, error_px))

            cv2.drawFrameAxes(
                frame,
                camera_matrix,
                dist_coeffs,
                rvec,
                tvec,
                marker_length * 0.7,
            )
            center = marker_corners.reshape(4, 2).mean(axis=0).astype(int)
            cv2.putText(
                frame,
                f"ID {marker_id}: W=({position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f})",
                tuple(center),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

    now = time.monotonic()
    if output_rows and now - last_print >= PRINT_PERIOD:
        for marker_id, position, angles, error_px in output_rows:
            print(
                f"ID={marker_id:3d}  world XYZ={position.round(4)} m  "
                f"world angles={angles.round(1)}°  err={error_px:.2f}px"
            )
        last_print = now

    cv2.imshow("ArUco in world coordinates — ESC to exit", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
