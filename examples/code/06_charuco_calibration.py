"""Калибровка камеры по набору фотографий ChArUco."""

from pathlib import Path

import cv2
import numpy as np

IMAGE_DIR = Path("calibration_images")
OUTPUT_FILE = "camera_calibration.npz"

DICT_NAME = "DICT_4X4_250"
SQUARES_X = 5
SQUARES_Y = 7
SQUARE_LENGTH = 0.0350  # измеренная сторона клетки, метры
MARKER_LENGTH = 0.0245  # измеренная сторона чёрного маркера, метры
MIN_CORNERS_PER_IMAGE = 12
MIN_IMAGES = 12
USE_RATIONAL_MODEL = False

dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DICT_NAME))
board = cv2.aruco.CharucoBoard(
    (SQUARES_X, SQUARES_Y), SQUARE_LENGTH, MARKER_LENGTH, dictionary
)
if hasattr(board, "setLegacyPattern"):
    board.setLegacyPattern(False)
detector = cv2.aruco.CharucoDetector(board)

object_points_all = []
image_points_all = []
used_images = []
image_size = None

paths = sorted(
    path
    for path in IMAGE_DIR.iterdir()
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
) if IMAGE_DIR.exists() else []

for path in paths:
    image = cv2.imread(str(path))
    if image is None:
        continue

    current_size = (image.shape[1], image.shape[0])
    if image_size is None:
        image_size = current_size
    elif current_size != image_size:
        print(f"Пропуск {path.name}: другое разрешение {current_size}")
        continue

    charuco_corners, charuco_ids, _, _ = detector.detectBoard(image)
    if charuco_ids is None or len(charuco_ids) < MIN_CORNERS_PER_IMAGE:
        print(f"Пропуск {path.name}: найдено мало углов")
        continue

    object_points, image_points = board.matchImagePoints(
        charuco_corners, charuco_ids
    )
    object_points_all.append(object_points)
    image_points_all.append(image_points)
    used_images.append(path.name)
    print(f"Используется {path.name}: углов {len(charuco_ids)}")

if image_size is None or len(object_points_all) < MIN_IMAGES:
    raise RuntimeError(
        f"Нужно не менее {MIN_IMAGES} разнообразных успешных кадров; "
        f"сейчас {len(object_points_all)}"
    )

flags = cv2.CALIB_RATIONAL_MODEL if USE_RATIONAL_MODEL else 0
(
    rms,
    camera_matrix,
    dist_coeffs,
    rvecs,
    tvecs,
    std_intrinsics,
    std_extrinsics,
    per_view_errors,
) = cv2.calibrateCameraExtended(
    object_points_all,
    image_points_all,
    image_size,
    None,
    None,
    flags=flags,
)

per_view_errors = per_view_errors.reshape(-1)
print(f"\nRMS: {rms:.4f} px")
print(f"Средняя ошибка кадра: {per_view_errors.mean():.4f} px")
print(f"Худший кадр: {used_images[int(np.argmax(per_view_errors))]} — {per_view_errors.max():.4f} px")
print("Матрица камеры:\n", camera_matrix)
print("Коэффициенты дисторсии:\n", dist_coeffs.ravel())

np.savez(
    OUTPUT_FILE,
    camera_matrix=camera_matrix,
    dist_coeffs=dist_coeffs,
    image_size=np.asarray(image_size, dtype=np.int32),
    rms=np.asarray(rms),
    per_view_errors=per_view_errors,
    used_images=np.asarray(used_images),
    dictionary=np.asarray(DICT_NAME),
    squares=np.asarray([SQUARES_X, SQUARES_Y], dtype=np.int32),
    square_length=np.asarray(SQUARE_LENGTH),
    marker_length=np.asarray(MARKER_LENGTH),
    std_intrinsics=std_intrinsics,
    std_extrinsics=std_extrinsics,
)
print(f"\nСохранено: {OUTPUT_FILE}")
