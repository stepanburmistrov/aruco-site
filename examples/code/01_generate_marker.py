import cv2

DICT_NAME = "DICT_4X4_250"
MARKER_ID = 17
SIZE_PX = 1000

dictionary = cv2.aruco.getPredefinedDictionary(
    getattr(cv2.aruco, DICT_NAME)
)

marker = cv2.aruco.generateImageMarker(
    dictionary,
    MARKER_ID,
    SIZE_PX,
    borderBits=1,
)

filename = f"{DICT_NAME}_ID_{MARKER_ID}.png"
cv2.imwrite(filename, marker)
print("Saved:", filename)
