# IMPORTANT NOTE
# Since grid will not move during game unless smth weird happens, I can detect the grid coordinates once
# Then I can crop into an isolated 8x8 grid
# During each turn, check for a move and run the corresponding function to analyze

import cv2
import numpy as np
import matplotlib.pyplot as plt

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

        """#might come in useful in the future -- using this just taking average instead for error reduction
        inter_x_dist = corners[1].tolist()[0][0]-corners[0].tolist()[0][0]
        inter_y_dist = corners[8].tolist()[0][1]-corners[0].tolist()[0][1]"""

        return corners

    else:
        print("No Checkerboard Found")
        return

corners = localize_chess_board(img) 

# 2. extract squares
def get_squares(img, corners):
    # corners gives 49 internal corners with (x,y) values in 1d array, convert into a 3d array (aka grid[row][col]) with (x,y) inside
    grid = corners.reshape(7, 7, 2)

    # calculating inter_x and inter_y dist here
    # we have 8 squares, 7 inner corners, and thus 6 intervals between corners
    # finding average to reduce error
    x_dist = (grid[0,6]-grid[0,0])/6
    y_dist = (grid[6,0]-grid[0,0])/6

    # create 9x9 array to include outer coordinates
    board = np.zeros((9, 9, 2)) #empty array
    top_left = grid[0,0]-x_dist-y_dist # start point
    for row in range(9):
        for col in range(9):
            board[row, col] = top_left + (row * y_dist) + (col * x_dist)

    # extract list of squares as images
    squares = []
    for row in range(8):
        for col in range(8):
            top_left = board[row, col]
            bottom_right = board[row+1, col+1]

            cropped_square = img[int(top_left[1]):int(bottom_right[1]), int(top_left[0]):int(bottom_right[0])]
            squares.append(cropped_square)

    return squares

squares = get_squares(img, corners)

# to display each square
def display_squares(squares):
    # create 8x8 figure
    fig, axes = plt.subplots(8, 8, figsize=(10, 10))
    
    # chessboard labels for clarity
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    
    for i in range(8):
        for j in range(8):
            index = i * 8 + j
            ax = axes[i, j]
            
            # display cropped square
            ax.imshow(squares[index])
            
            # add labels like 'a8', 'b8', etc.
            ax.set_title(f"{files[j]}{ranks[i]}", fontsize=8)
            
            # hide axes
            ax.axis('off')

    plt.tight_layout()
    plt.show()

display_squares(squares)

# 3. piece detection and classification
cv2.waitKey(0)
cv2.destroyAllWindows()