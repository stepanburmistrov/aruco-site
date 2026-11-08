import cv2

IMAGE = "aruco_photo.jpg"
DICT_NAME = "DICT_4X4_250"

image = cv2.imread(IMAGE)
if image is None:
    raise FileNotFoundError(IMAGE)

dictionary = cv2.aruco.getPredefinedDictionary(
    getattr(cv2.aruco, DICT_NAME)
)

parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(dictionary, parameters)

corners, ids, rejected = detector.detectMarkers(image)

result = image.copy()

if ids is not None:
    cv2.aruco.drawDetectedMarkers(result, corners, ids)
    print("Detected IDs:", ids.flatten().tolist())
else:
    print("No markers detected")

cv2.imshow("ArUco detection", result)
cv2.waitKey(0)
cv2.destroyAllWindows()
