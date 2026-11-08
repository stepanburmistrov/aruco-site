"""Общие функции для точной 3D-позиции ArUco в OpenCV."""

from pathlib import Path

import cv2
import numpy as np


def load_calibration(path="camera_calibration.npz"):
    data = np.load(Path(path))
    return data["camera_matrix"], data["dist_coeffs"]


def marker_object_points(marker_length):
    """Углы квадрата в порядке OpenCV: TL, TR, BR, BL."""
    half = marker_length / 2.0
    return np.array(
        [
            [-half, half, 0.0],
            [half, half, 0.0],
            [half, -half, 0.0],
            [-half, -half, 0.0],
        ],
        dtype=np.float32,
    )


def estimate_marker_pose(corners, marker_length, camera_matrix, dist_coeffs):
    object_points = marker_object_points(marker_length)
    image_points = np.asarray(corners, dtype=np.float32).reshape(4, 2)
    ok, rvec, tvec = cv2.solvePnP(
        object_points,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_IPPE_SQUARE,
    )
    if not ok or float(tvec.reshape(3)[2]) <= 0:
        return None

    projected, _ = cv2.projectPoints(
        object_points, rvec, tvec, camera_matrix, dist_coeffs
    )
    error_px = float(
        np.sqrt(np.mean(np.sum((projected.reshape(4, 2) - image_points) ** 2, axis=1)))
    )
    return rvec, tvec, error_px


def transform_from_pose(rvec, tvec):
    rotation, _ = cv2.Rodrigues(rvec)
    transform = np.eye(4, dtype=np.float64)
    transform[:3, :3] = rotation
    transform[:3, 3] = np.asarray(tvec, dtype=np.float64).reshape(3)
    return transform


def invert_transform(transform):
    rotation = transform[:3, :3]
    translation = transform[:3, 3]
    result = np.eye(4, dtype=np.float64)
    result[:3, :3] = rotation.T
    result[:3, 3] = -rotation.T @ translation
    return result


def average_transforms(transforms):
    """Среднее положение и ближайшая корректная матрица вращения."""
    translations = np.stack([item[:3, 3] for item in transforms])
    rotation_mean = np.mean([item[:3, :3] for item in transforms], axis=0)
    u, _, vt = np.linalg.svd(rotation_mean)
    rotation = u @ vt
    if np.linalg.det(rotation) < 0:
        u[:, -1] *= -1
        rotation = u @ vt
    result = np.eye(4, dtype=np.float64)
    result[:3, :3] = rotation
    result[:3, 3] = translations.mean(axis=0)
    return result


def euler_xyz_degrees(rotation):
    """Углы XYZ для удобного вывода; матрица остаётся основным результатом."""
    sy = np.hypot(rotation[0, 0], rotation[1, 0])
    if sy > 1e-9:
        x = np.arctan2(rotation[2, 1], rotation[2, 2])
        y = np.arctan2(-rotation[2, 0], sy)
        z = np.arctan2(rotation[1, 0], rotation[0, 0])
    else:
        x = np.arctan2(-rotation[1, 2], rotation[1, 1])
        y = np.arctan2(-rotation[2, 0], sy)
        z = 0.0
    return np.degrees([x, y, z])
