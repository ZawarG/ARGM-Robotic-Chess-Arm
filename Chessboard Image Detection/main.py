import cv2
import numpy as np
import matplotlib.pyplot as plt
from chess_board import ChessBoard
from chess_square import ChessSquare
import matplotlib.patches as patches

def createMask(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # blurred = cv2.GaussianBlur(gray, (7, 7), 0) # reduce wood grain
    blurred = cv2.medianBlur(gray, 7)
    
    # create mask with manual thresholding (same as what was done with hsv)
    # lower_bound = 0      # lower value for white squares
    # upper_bound = 130    # upper value for white squares
    # msk = cv2.inRange(blurred, lower_bound, upper_bound)
    # res = 255 - msk  # invert

    # otsu thresholding (automatically finds value for threshold)
    otsu_th, msk = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    squares_msk = 255 - msk

    # manual threshold to single out black border
    border_msk = cv2.inRange(blurred, 0, 80)

    # merge otsu and manual thresholds
    res = np.ones_like(gray)*255 # white canvas
    res[squares_msk == 255] = 0 # add in black parts of otsu mask
    res[border_msk == 255] = 255 # add in black parts of squares mask

    # morphology to clean up small noise
    kernel = np.ones((5,5), np.uint8)
    res = cv2.morphologyEx(res, cv2.MORPH_OPEN, kernel) # removes small white noise
    res = cv2.morphologyEx(res, cv2.MORPH_CLOSE, kernel) # fills small black holes

    cv2.imshow('1', img)
    cv2.imshow('2', blurred)
    cv2.imshow('border', border_msk)
    cv2.imshow('final', res)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return res

def localizeChessBoard(img):
    res = createMask(img)

    ret, corners = cv2.findChessboardCorners(res, (7, 7),
                                            flags=cv2.CALIB_CB_ADAPTIVE_THRESH +
                                                cv2.CALIB_CB_FAST_CHECK +
                                                cv2.CALIB_CB_NORMALIZE_IMAGE)
    
    if ret:
        fnl = cv2.drawChessboardCorners(img, (7, 7), corners, ret)
        cv2.imshow("Chessboard with Corners", fnl)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        # corners gives 49 internal corners with (x,y) values in 1d array, convert into a 3d array (aka grid[row][col]) with (x,y) inside
        grid = corners.reshape(7,7,2)

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

        return board, res

    else:
        print("No Checkerboard Found")
        return None, res

# display each square
def displaySquares(squares):
    # create 8x8 figure
    fig, axes = plt.subplots(8, 8, figsize=(7, 7))
    
    # chessboard labels for clarity
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    
    for i in range(8):
        for j in range(8):
            ax = axes[i, j]
            
            # display cropped square
            ax.imshow(squares[i][j].image)

            # occupied
            occupied = squares[i][j].isOccupied()
            color = 'red' if occupied else 'green'  # red = occupied, green = empty
            rect = patches.Rectangle(
                (0, 0),                       # top-left corner (x, y)
                squares[i][j].image.shape[1], # width
                squares[i][j].image.shape[0], # height
                linewidth=5,
                edgecolor=color,
                facecolor='none'
            )
            ax.add_patch(rect)
            
            # add labels like 'a8', 'b8', etc.
            ax.set_title(f"{files[j]}{ranks[i]}", fontsize=8)
            
            # hide axes
            ax.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    image_path = "Chessboard Image Detection/data/input/RenderedImage.jpeg"
    img = cv2.imread(image_path)
    
    # retrieve picture
    # cam = cv2.VideoCapture(0)
    
    # initialization
    boardCoord = None
    # while boardCoord is None:
        # _, img = cam.read()
    boardCoord, img_new = localizeChessBoard(img) # find location of board

    if boardCoord is not None:

        chessBoard = ChessBoard(boardCoord) # create chess board object
        chessBoard.updateSquares(img_new)

        # display for debugging
        displaySquares(chessBoard.squares)
    
    # while True:
    #     exists, img = cam.read()
    #     if not exists: break

    #     # update chess board
    #     img_new = createMask(img)
    #     outcome = chessBoard.update(img_new)

    #     if outcome: # save or return this somehow
    #         break