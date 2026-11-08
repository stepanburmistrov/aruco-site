import cv2

DICT_NAME = "DICT_4X4_250"

SQUARES_X = 5
SQUARES_Y = 7

# Physical dimensions, meters.
SQUARE_LENGTH = 0.035
MARKER_LENGTH = 0.0245

dictionary = cv2.aruco.getPredefinedDictionary(
    getattr(cv2.aruco, DICT_NAME)
)

board = cv2.aruco.CharucoBoard(
    (SQUARES_X, SQUARES_Y),
    SQUARE_LENGTH,
    MARKER_LENGTH,
    dictionary,
)

image = board.generateImage(
    (SQUARES_X * 250, SQUARES_Y * 250),
    marginSize=0,
    borderBits=1,
)
if hasattr(board, "setLegacyPattern"):
    board.setLegacyPattern(False)  # современный шаблон OpenCV 4.6+

cv2.imwrite("charuco_board.png", image)
print("Saved: charuco_board.png")
