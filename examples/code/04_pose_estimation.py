"""3D-положение ArUco относительно откалиброванной камеры на фотографии."""

import cv2
import numpy as np

from aruco_pose_utils import estimate_marker_pose, euler_xyz_degrees, load_calibration

IMAGE = "aruco_photo.jpg"
CALIBRATION = "camera_calibration.npz"
DICT_NAME = "DICT_4X4_250"

# Внешняя сторона ЧЁРНОГО квадрата, метры. Белое поле не входит.
MARKER_LENGTH = 0.060

camera_matrix, dist_coeffs = load_calibration(CALIBRATION)
image = cv2.imread(IMAGE)
if image is None:
    raise FileNotFoundError(IMAGE)

dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DICT_NAME))
detector = cv2.aruco.ArucoDetector(
    dictionary, cv2.aruco.DetectorParameters()
)
corners, ids, _ = detector.detectMarkers(image)
if ids is None:
    raise RuntimeError("Маркеры не найдены")

result = image.copy()
cv2.aruco.drawDetectedMarkers(result, corners, ids)

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
    distance = float(np.linalg.norm(tvec))
    print(
        f"ID={marker_id}  X={x:.4f}  Y={y:.4f}  Z={z:.4f} m  "
        f"distance={distance:.4f} m  XYZ angles={angles.round(2)} deg  "
        f"reprojection={error_px:.2f} px"
    )
    cv2.drawFrameAxes(
        result, camera_matrix, dist_coeffs, rvec, tvec, MARKER_LENGTH * 0.7
    )

cv2.imshow("ArUco pose", result)
cv2.waitKey(0)
cv2.destroyAllWindows()
