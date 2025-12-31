# IMPORTANT NOTE
# Since grid will not move during game unless smth weird happens, I can detect the grid coordinates once
# Then I can crop into an isolated 8x8 grid
# During each turn, check for a move and run the corresponding function to analyze

import cv2
import numpy as np
import matplotlib.pyplot as plt

def localize_chess_board(image_path):
    # load
    img = cv2.imread(image_path)

    # grayscale and rgb
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # blur
    blur = cv2.GaussianBlur(gray, (3, 3), 0)

    # otsu threshold
    threshold, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # canny edge detection
    edges = cv2.Canny(gray, 20, 255)

    cv2.imshow("blur", blur)
    cv2.imshow("otsu", otsu)
    cv2.imshow("canny", edges)
    # plt.figure(figsize=(9,7))
    # plt.imshow(otsu)

    # dilation

    # hough line transform

    # dilation

    # filter contours

    # perspective transform

    # divide into 64 squares

localize_chess_board("Chessboard Image Detection/data/input/image.png")
# plt.axis("off")
# plt.show()
cv2.waitKey(0)
cv2.destroyAllWindows()


# 2. board square mapping

# 3. piece detection and classification
