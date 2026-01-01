# IMPORTANT NOTE
# Since grid will not move during game unless smth weird happens, I can detect the grid coordinates once
# Then I can crop into an isolated 8x8 grid
# During each turn, check for a move and run the corresponding function to analyze

import cv2
import numpy as np

image_path = "Chessboard Image Detection/data/input/test.jpg"
img = cv2.imread(image_path)
cv2.imshow("img", img)

def localize_chess_board(img):
    #binary mask
    lwr = np.array([0, 0, 143]) # lower bound for colours
    upr = np.array([179, 61, 252]) # upper bound for colours
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) 
    msk = cv2.inRange(hsv, lwr, upr) # colours within range converted to white, outside to black

    #dilation morphology
    krn = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 30))
    dlt = cv2.dilate(msk, krn, iterations=5)
    cv2.imshow("dilation", dlt)

    #bit AND operation
    res = 255 - cv2.bitwise_and(dlt, msk)

    #cv2 find chessboard (finds a checkboard pattern)
    res = np.uint8(res)
    ret, corners = cv2.findChessboardCorners(res, (7, 7),
                                            flags=cv2.CALIB_CB_ADAPTIVE_THRESH +
                                                cv2.CALIB_CB_FAST_CHECK +
                                                cv2.CALIB_CB_NORMALIZE_IMAGE)
    if ret:
        fnl = cv2.drawChessboardCorners(img, (7, 7), corners, ret)
        cv2.imshow("Chessboard with Corners", fnl)

        """#might come in useful in the future
        inter_x_dist = corners[1].tolist()[0][0]-corners[0].tolist()[0][0]
        inter_y_dist = corners[8].tolist()[0][1]-corners[0].tolist()[0][1]"""
        return corners

    else:
        print("No Checkerboard Found")
        return

corners = localize_chess_board(img) # corners gives 49 internal corners with (x,y) values in 1d array
# print(corners)

# 2. warp image to get perfect square
def get_warped_board(img, corners):
    grid = corners.reshape(7, 7, 2) # convert corners into a 3d array (aka grid[row][col]) with (x,y) inside

    # calculating inter_x and inter_y dist here
    # we have 8 squares, 7 inner corners, and thus 6 intervals between corners
    # finding average to reduce error
    x_dist = (grid[0,6]-grid[0,0])/6
    y_dist = (grid[6,0]-grid[0,0])/6

    # find 4 outer corners
    top_left = grid[0,0]-x_dist-y_dist
    top_right = grid[0,6]+x_dist-y_dist
    bottom_left = grid[6,0]-x_dist+y_dist
    bottom_right = grid[6,6]+x_dist+y_dist

    # warp image to board
    points = np.array([bottom_right, bottom_left, top_left, top_right], dtype="float32")
    destination = np.array([[0,0],[800,0],[800,800],[0,800]], dtype="float32")
    trans_matrix = cv2.getPerspectiveTransform(points, destination)
    warped_board = cv2.warpPerspective(img, trans_matrix, (800,800)); # each square 100x100 px

    return warped_board

warped_board = get_warped_board(img, corners)
cv2.imshow("warped board", warped_board)

# 3. extract squares from warped board
squares = []
for row in range(8):
    for col in range(8):
        # Slice the warped image: [y_start:y_end, x_start:x_end]
        square = warped_board[row*100:(row+1)*100, col*100:(col+1)*100]
        squares.append(square)

# 3. piece detection and classification
cv2.waitKey(0)
cv2.destroyAllWindows()