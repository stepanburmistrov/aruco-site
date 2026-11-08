"""ROS 2: публикация PoseStamped выбранного ArUco в camera_optical_frame."""

import cv2
import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node

from aruco_pose_utils import estimate_marker_pose

CALIBRATION = "camera_calibration.npz"
CAMERA_INDEX = 0
DICT_NAME = "DICT_4X4_250"
TARGET_ID = 17
MARKER_LENGTH = 0.060
TOPIC = "/aruco/pose"


def quaternion_from_rotation(rotation):
    q = np.empty(4, dtype=np.float64)  # x, y, z, w
    trace = np.trace(rotation)
    if trace > 0:
        s = np.sqrt(trace + 1.0) * 2
        q[:] = [
            (rotation[2, 1] - rotation[1, 2]) / s,
            (rotation[0, 2] - rotation[2, 0]) / s,
            (rotation[1, 0] - rotation[0, 1]) / s,
            0.25 * s,
        ]
    else:
        index = int(np.argmax(np.diag(rotation)))
        if index == 0:
            s = np.sqrt(1.0 + rotation[0, 0] - rotation[1, 1] - rotation[2, 2]) * 2
            q[:] = [0.25 * s, (rotation[0, 1] + rotation[1, 0]) / s, (rotation[0, 2] + rotation[2, 0]) / s, (rotation[2, 1] - rotation[1, 2]) / s]
        elif index == 1:
            s = np.sqrt(1.0 + rotation[1, 1] - rotation[0, 0] - rotation[2, 2]) * 2
            q[:] = [(rotation[0, 1] + rotation[1, 0]) / s, 0.25 * s, (rotation[1, 2] + rotation[2, 1]) / s, (rotation[0, 2] - rotation[2, 0]) / s]
        else:
            s = np.sqrt(1.0 + rotation[2, 2] - rotation[0, 0] - rotation[1, 1]) * 2
            q[:] = [(rotation[0, 2] + rotation[2, 0]) / s, (rotation[1, 2] + rotation[2, 1]) / s, 0.25 * s, (rotation[1, 0] - rotation[0, 1]) / s]
    return q / np.linalg.norm(q)


class ArucoPosePublisher(Node):
    def __init__(self):
        super().__init__("aruco_pose_publisher")
        calibration = np.load(CALIBRATION)
        self.camera_matrix = calibration["camera_matrix"]
        self.dist_coeffs = calibration["dist_coeffs"]
        image_size = tuple(int(value) for value in calibration["image_size"])
        dictionary = cv2.aruco.getPredefinedDictionary(
            getattr(cv2.aruco, DICT_NAME)
        )
        self.detector = cv2.aruco.ArucoDetector(
            dictionary, cv2.aruco.DetectorParameters()
        )
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, image_size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, image_size[1])
        if not self.cap.isOpened():
            raise RuntimeError("Камера недоступна")
        self.publisher = self.create_publisher(PoseStamped, TOPIC, 10)
        self.timer = self.create_timer(1.0 / 30.0, self.update)

    def update(self):
        ok, frame = self.cap.read()
        if not ok:
            return
        corners, ids, _ = self.detector.detectMarkers(frame)
        if ids is None:
            return
        for marker_id, marker_corners in zip(ids.flatten(), corners):
            if int(marker_id) != TARGET_ID:
                continue
            pose = estimate_marker_pose(
                marker_corners,
                MARKER_LENGTH,
                self.camera_matrix,
                self.dist_coeffs,
            )
            if pose is None:
                return
            rvec, tvec, _ = pose
            rotation, _ = cv2.Rodrigues(rvec)
            quaternion = quaternion_from_rotation(rotation)
            x, y, z = tvec.reshape(3)
            message = PoseStamped()
            message.header.stamp = self.get_clock().now().to_msg()
            message.header.frame_id = "camera_optical_frame"
            message.pose.position.x = float(x)
            message.pose.position.y = float(y)
            message.pose.position.z = float(z)
            message.pose.orientation.x = float(quaternion[0])
            message.pose.orientation.y = float(quaternion[1])
            message.pose.orientation.z = float(quaternion[2])
            message.pose.orientation.w = float(quaternion[3])
            self.publisher.publish(message)
            return

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main():
    rclpy.init()
    node = ArucoPosePublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
