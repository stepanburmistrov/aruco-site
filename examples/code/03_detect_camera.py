import cv2

CAMERA_INDEX = 0
DICT_NAME = "DICT_4X4_250"

dictionary = cv2.aruco.getPredefinedDictionary(
    getattr(cv2.aruco, DICT_NAME)
)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(dictionary, parameters)

cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    raise RuntimeError("Camera is not available")

while True:
    ok, frame = cap.read()
    if not ok:
        break

    corners, ids, rejected = detector.detectMarkers(frame)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        for marker_id, marker_corners in zip(ids.flatten(), corners):
            pts = marker_corners[0]
            center = pts.mean(axis=0)
            cv2.putText(
                frame,
                f"ID {marker_id}",
                tuple(center.astype(int)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

    cv2.imshow("ArUco camera", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
