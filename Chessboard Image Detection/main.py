import cv2
import requests
import numpy as np
from chess_board import ChessBoard
from chess_square import ChessSquare

# for visualization
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Filter image
def apply_adjustments(img, sat, con, bright, bp, shadow):
    # Saturation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = np.clip(s.astype(np.float32) * sat, 0, 255).astype(np.uint8)
    img = cv2.cvtColor(cv2.merge([h, s, v]), cv2.COLOR_HSV2BGR)

    # Contrast, brightness
    img = cv2.convertScaleAbs(img, alpha=con, beta=bright)

    # Black point, shadows (LUT)
    # Shadow > 1.0 lifts shadows, < 1.0 darkens them
    invGamma = 1.0 / shadow
    table = np.array([
        np.clip((( (i - bp) / (255 - bp) ) ** invGamma) * 255, 0, 255) 
        if i > bp else 0 
        for i in range(256)
    ]).astype("uint8")
    
    return cv2.LUT(img, table)

# Find perfect image filter and threshold settings for board detection
def testimgsettings(img):
    # Define ranges for image filtration
    saturations = [1.0, 1.5, 2.0]
    contrasts = [0.8, 1.0, 1.3]
    brightnesses = [-20, 0, 20]
    black_points = [0, 20, 40] # important for border
    shadows = [0.8, 1.2, 1.6]

    # Define how much to iterate by for threshold values
    step = 16

    # Define list of possible thresholds
    board_ranges = [
        (low, high)
        for low in range(0, 256, step)
        for high in range(low + step, 256, step)
    ]

    border_ranges = [
        (low, high)
        for low in range(0, 256, step)
        for high in range(low + step, 256, step)
    ]

    # Iterate through all image filter settings
    for sat in saturations:
        for con in contrasts:
            for bright in brightnesses:
                for bp in black_points:
                    for shadow in shadows:
                        
                        # Apply image filters
                        adjusted = apply_adjustments(img, sat, con, bright, bp, shadow)

                        # Iterate through all board threshold settings
                        for board_lower, board_upper in board_ranges:
                            for border_lower, border_upper in border_ranges:

                                # Create mask
                                mask = createMask(adjusted, board_lower, board_upper, border_lower, border_upper)

                                # Attempt to detect board
                                boardCoord, img_new = localizeChessBoard(img, mask)

                                # Return successful values
                                if boardCoord is not None:
                                    return (
                                        sat, con, bright, bp, shadow,
                                        board_lower, board_upper,
                                        border_lower, border_upper
                                    )
    return None

# Create binary masks -- one for square, one for board outline
def createMask(img, board_lwr, board_upr, border_lwr, border_upr):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # blurred = cv2.GaussianBlur(gray, (7, 7), 0) # reduce wood grain
    blurred = cv2.medianBlur(gray, 7) # Blur to reduce wood grain

    # Single out board squares and border with given thresholds
    squares_msk = cv2.inRange(blurred, board_lwr, board_upr)
    border_msk = cv2.inRange(blurred, border_lwr, border_upr)

    # Merge both thresholds
    res = np.ones_like(gray)*255 # White canvas
    res[squares_msk == 255] = 0 # Add in squares mask as black
    res[border_msk == 255] = 255 # Add in border mask as white

    # Morphology to clean up small noise
    kernel = np.ones((5,5), np.uint8)
    res = cv2.morphologyEx(res, cv2.MORPH_OPEN, kernel) # removes small white noise
    res = cv2.morphologyEx(res, cv2.MORPH_CLOSE, kernel) # fills small black holes

    # Display results
    # cv2.imshow('border', border_msk)
    # cv2.imshow('squares', squares_msk)
    # cv2.imshow('final', res)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return res

# Detect location of chess board
def localizeChessBoard(img, mask):
    # Build in method to detect chess board from binary mask
    ret, corners = cv2.findChessboardCorners(
        mask, (7, 7),
        flags=cv2.CALIB_CB_ADAPTIVE_THRESH +
            cv2.CALIB_CB_FAST_CHECK +
            cv2.CALIB_CB_NORMALIZE_IMAGE
    )
    
    if ret:
        # Detect and display chess board
        fnl = cv2.drawChessboardCorners(img, (7, 7), corners, ret)
        cv2.imshow("Chessboard with Corners", fnl)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Retrieve chess square corners as a 1d array of tuples (x,y) containing 49 values (internal corners)
        grid = corners.reshape(7,7,2)

        # Convert chess square corners to a 3d array including the outer coordinates -- grid[row][col] with (x,y)
        # Calculate average distance between each square
        # We have 8 squares, 7 inner corners, and thus 6 intervals between corners
        x_dist = (grid[0,6]-grid[0,0])/6
        y_dist = (grid[6,0]-grid[0,0])/6

        # Create 9x9 array including outer coordinates
        board = np.zeros((9, 9, 2)) # Empty numpy array
        top_left = grid[0,0]-x_dist-y_dist # Start point
        for row in range(9):
            for col in range(9):
                board[row, col] = top_left + (row * y_dist) + (col * x_dist)

        print("Checkerboard Found")
        return board, mask

    else:
        print("No Checkerboard Found")
        return None, mask

# Display each square
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

def runVideoCapture():
    # Retrieve video
    cam = cv2.VideoCapture(0)
    
    # Define variables
    board_coord = None
    max_attempts = 300
    attempts = 0

    # Run loop until board coordinates are found or until maximum attemps have been made
    while board_coord is None and attempts < max_attempts:
        # Read an image from the video stream
        ret, img = cam.read()

        if not ret: continue # Camera failed
        
        # Retrieve optimal adjustment values
        sat, con, bright, bp, shadow, status, board_lower, board_upper, border_lower, border_upper = testimgsettings(img)
        # Adjust image with given filter values
        adjusted_img = apply_adjustments(img, sat, con, bright, bp, shadow, status)
        # Create binary mask with given threshold values
        mask = createMask(adjusted_img, board_lower, board_upper, border_lower, border_upper)
        # Find location of board using mask
        board_coord, img_new = localizeChessBoard(img, mask)
        
        # Increase attempt count
        attempts+=1

        # Display result
        cv2.imshow("Camera", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return

    # Create chess board object with coordinates found
    chess_board = ChessBoard(board_coord)
    chess_board.updateSquares(img_new)

    # Display chess squares for debugging
    displaySquares(chess_board.squares)
    
    # Game loop: checks for changes in the board and runs until the game state is complete
    while True:
        exists, img = cam.read()
        if not exists: break

        # update chess board
        img_new = createMask(img)
        outcome = chess_board.update(img_new)

        if outcome:
            break

def testCodeWithImage() :
    image_path = "Chessboard Image Detection/data/input/fromvid.png"
    img = cv2.imread(image_path)

    # Retrieve optimal adjustment values
    sat, con, bright, bp, shadow, board_lower, board_upper, border_lower, border_upper = testimgsettings(img)
    # Adjust image with given filter values
    adjusted_img = apply_adjustments(img, sat, con, bright, bp, shadow)
    # Create binary mask with given threshold values
    mask = createMask(adjusted_img, board_lower, board_upper, border_lower, border_upper)
    # Find location of board using mask
    board_coord, img_new = localizeChessBoard(img, mask)

    print(board_coord)
    if board_coord is not None:
        chess_board = ChessBoard(board_coord) # create chess board object
        chess_board.updateSquares(img_new)

        # display for debugging
        displaySquares(chess_board.squares)

if __name__ == "__main__":
    USE_CAMERA = False

    if USE_CAMERA:
        runVideoCapture()
    else: 
        testCodeWithImage()