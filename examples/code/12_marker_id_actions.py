"""Пример событий по ID: действие выполняется один раз при появлении маркера."""

import time

import cv2

CAMERA_INDEX = 0
DICT_NAME = "DICT_4X4_250"
REARM_AFTER_SECONDS = 1.0


def start_robot():
    print("START: здесь можно отправить команду роботу")


def stop_robot():
    print("STOP: здесь можно остановить моторы")


def take_photo():
    print("PHOTO: здесь можно сохранить кадр")


ACTIONS = {
    0: start_robot,
    1: stop_robot,
    2: take_photo,
}

dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DICT_NAME))
detector = cv2.aruco.ArucoDetector(
    dictionary, cv2.aruco.DetectorParameters()
)
cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    raise RuntimeError("Камера недоступна")

last_seen = {}
armed = set(ACTIONS)
while True:
    ok, frame = cap.read()
    if not ok:
        break
    corners, ids, _ = detector.detectMarkers(frame)
    now = time.monotonic()
    visible = set() if ids is None else set(int(value) for value in ids.flatten())

    for marker_id in visible:
        last_seen[marker_id] = now
        if marker_id in ACTIONS and marker_id in armed:
            ACTIONS[marker_id]()
            armed.remove(marker_id)

    for marker_id in ACTIONS:
        if marker_id not in visible and now - last_seen.get(marker_id, 0.0) >= REARM_AFTER_SECONDS:
            armed.add(marker_id)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
    cv2.imshow("ArUco ID actions — ESC to exit", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
