# IMPORTANT NOTE
# Since grid will not move during game unless smth weird happens, I can detect the grid coordinates once
# Then I can crop into an isolated 8x8 grid
# During each turn, check for a move and run the corresponding function to analyze

import cv2
import numpy as np

img = cv2.imread("Chessboard Image Detection/data/input/board2.png")

if img is None:
    raise ValueError("Image not found")

# 1. board localization (identify outline: large quadrilateral)
# grayscale
grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
grayscale = cv2.medianBlur(grayscale, 5); # blur reduces background noise
# gaussian blur replaced by median: cv2.GaussianBlur(grayscale, (13, 13), 0) # blur to reduce noise before thresholding
# option to normalize lighting here gray = cv2.equalizeHist(gray)
cv2.imshow("Gray", grayscale)

# convert grayscale to binary (b&w) using adaptive thresholding
bnw = cv2.adaptiveThreshold(
    grayscale,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY_INV,
    blockSize=27, # should be slightly smaller than square size in pixels. if too much noise, increase
    C=13 # increase to ignore background noise
)

cv2.imshow("bnw", bnw)

# morphological cleanup to remove small blobs and repair broken lines in chess board
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)) 
closed = cv2.morphologyEx(bnw, cv2.MORPH_CLOSE, kernel)

# vertical kernal isolates vertical lines, horizontal for horizontal lines
vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
vertical = cv2.morphologyEx(closed, cv2.MORPH_OPEN, vertical_kernel)

horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
horizontal = cv2.morphologyEx(closed, cv2.MORPH_OPEN, horizontal_kernel)

cv2.imshow("Vertical Lines", vertical)
cv2.imshow("Horizontal Lines", horizontal)

# directional dilation to stretch lines aka fill in gaps
v_smear_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 10))
vertical_dilated = cv2.dilate(vertical, v_smear_kernel, iterations=2)

cv2.imshow("Verticaldilated Lines", vertical_dilated)

# put vertical and horizontal lines together using hough lines
lines_v = cv2.HoughLinesP(vertical_dilated, 1, np.pi/180, threshold=50, minLineLength=50, maxLineGap=50) 
lines_h = cv2.HoughLinesP(horizontal, 1, np.pi/180, threshold=50, minLineLength=50, maxLineGap=70)

overlay = img.copy()

if lines_v is not None:
    for line in lines_v:
        x1, y1, x2, y2 = line[0]
        cv2.line(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
# if lines_h is not None:
#     for line in lines_h:
#         x1, y1, x2, y2 = line[0]
#         cv2.line(overlay, (x1, y1), (x2, y2), (255, 0, 0), 2)

cv2.imshow("Hough grid", overlay)

# 2. board square mapping

# 3. piece detection and classification

cv2.waitKey(0)
cv2.destroyAllWindows()