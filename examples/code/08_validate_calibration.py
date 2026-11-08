"""Проверка калибровки: параметры, разрешение и живая коррекция дисторсии."""

import cv2
import numpy as np

CALIBRATION = "camera_calibration.npz"
CAMERA_INDEX = 0

data = np.load(CALIBRATION)
camera_matrix = data["camera_matrix"].astype(np.float64)
dist_coeffs = data["dist_coeffs"].astype(np.float64)
calibration_size = tuple(int(v) for v in data["image_size"])

print(f"RMS калибровки: {float(data['rms']):.4f} px")
if "per_view_errors" in data:
    errors = data["per_view_errors"].reshape(-1)
    print(f"Ошибки кадров: median={np.median(errors):.4f}, max={errors.max():.4f} px")
print("Матрица камеры:\n", camera_matrix)
print("Дисторсия:", dist_coeffs.ravel())

cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, calibration_size[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, calibration_size[1])
if not cap.isOpened():
    raise RuntimeError("Камера недоступна")

ok, frame = cap.read()
if not ok:
    raise RuntimeError("Не удалось получить кадр")

current_size = (frame.shape[1], frame.shape[0])
scale_x = current_size[0] / calibration_size[0]
scale_y = current_size[1] / calibration_size[1]
if abs(scale_x - scale_y) > 0.01:
    raise RuntimeError(
        f"Соотношение сторон изменилось: калибровка {calibration_size}, камера {current_size}"
    )

scaled_matrix = camera_matrix.copy()
scaled_matrix[0, :] *= scale_x
scaled_matrix[1, :] *= scale_y
fov_x = np.degrees(2 * np.arctan(current_size[0] / (2 * scaled_matrix[0, 0])))
fov_y = np.degrees(2 * np.arctan(current_size[1] / (2 * scaled_matrix[1, 1])))
print(f"Текущее разрешение: {current_size}; расчётный FOV: {fov_x:.1f}° × {fov_y:.1f}°")

new_matrix, roi = cv2.getOptimalNewCameraMatrix(
    scaled_matrix, dist_coeffs, current_size, 0.0, current_size
)
map_x, map_y = cv2.initUndistortRectifyMap(
    scaled_matrix, dist_coeffs, None, new_matrix, current_size, cv2.CV_32FC1
)

while True:
    ok, frame = cap.read()
    if not ok:
        break
    corrected = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)
    comparison = np.hstack([frame, corrected])
    if comparison.shape[1] > 1800:
        scale = 1800 / comparison.shape[1]
        comparison = cv2.resize(comparison, None, fx=scale, fy=scale)
    cv2.putText(comparison, "original | undistorted", (24, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.imshow("Calibration validation — ESC to exit", comparison)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
