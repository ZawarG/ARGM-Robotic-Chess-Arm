import cv2
import numpy as np
from chess_board import ChessBoard

import csv

# for visualization
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Filter image
def applyImageAdjustments(img, sat, con, bright, bp, shadow):
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
def determineImageSettings(img, attempts):
    # Define how much to iterate by for filtration values
    img_step = .2

    # Define ranges for image filtration
    saturations = np.arange(1, 2, img_step)
    contrasts = np.arange(.8, 2, img_step)
    brightnesses = np.arange(-20, 20, 2)
    black_points = np.arange(0, 40, 2)
    shadows = np.arange(.8, 2, img_step)

    # saturations = [1.0, 1.5, 2.0]
    # contrasts = [0.8, 1.0, 1.3]
    # brightnesses = [-20, 0, 20]
    # black_points = [0, 20, 40] # important for border
    # shadows = [0.8, 1.2, 1.6]

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
                        adjusted = applyImageAdjustments(img, sat, con, bright, bp, shadow)

                        # Iterate through all board threshold settings
                        for board_lower, board_upper in board_ranges:
                            for border_lower, border_upper in border_ranges:

                                # Create mask
                                mask = createMask(adjusted, board_lower, board_upper, border_lower, border_upper)

                                # Attempt to detect board
                                board_coord, img_new = localizeChessBoard(img, mask)

                                print(attempts)

                                # Return successful values
                                if board_coord is not None:
                                    print('appending')
                                    with open("Chessboard Image Detection/data/output/imagevalues.csv", 'a', newline='') as csvfile:
                                        # Create a CSV writer object
                                        csv_writer = csv.writer(csvfile)
                                        
                                        # Write all rows at once
                                        csv_writer.writerow([board_lower, board_upper, border_lower, border_upper, sat, con, bright, bp, shadow])
                                    return board_coord, img_new
                                    
                                    # list.append([board_lower, board_upper, border_lower, border_upper, saturations, contrasts, brightnesses, black_points, shadows])
    # return list
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
        # cv2.imshow("Chessboard with Corners", fnl)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        print("found")
        
        # Retrieve chess square corners as a 1d array of tuples (x,y) containing 49 values (internal corners)
        grid = corners.reshape(7,7,2)

        # Rotate grid until its orientation is correct (top-left square first)
        count = 0
        while ((grid[0,0][1] > grid[6,0][1] or grid[0,0][0] > grid[0,6][0]) and count<4):
            grid = np.rot90(grid)
            count+=1

        # Convert chess square corners to a 3d array including the outer coordinates -- grid[row][col][x,y]
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
    # Create 8x8 figure
    fig, axes = plt.subplots(8, 8, figsize=(7, 7))
    
    # Chessboard labels for clarity
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    
    for i in range(8):
        for j in range(8):
            ax = axes[i, j]
            img = squares[i][j].image
            
            # Check if image exists
            if img is None or img.size == 0:
                print(f"Empty image at {i},{j}")
                print(img.shape)
            else:
                ax.imshow(img)
                
            # Display cropped square
            ax.imshow(img)

            # Check which square is occupied and display using coloured borders
            occupied = squares[i][j].isOccupied()
            color = 'red' if occupied else 'green'

            # Place all images on figure
            rect = patches.Rectangle(
                (0, 0),                       # Top-left corner (x, y)
                squares[i][j].image.shape[1], # Width
                squares[i][j].image.shape[0], # Height
                linewidth=5,
                edgecolor=color,
                facecolor='none'
            )
            ax.add_patch(rect)
            
            # Add labels like 'a8', 'b8', etc.
            ax.set_title(f"{files[j]}{ranks[i]}", fontsize=8)
            
            # Hide axes
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

        cv2.imshow('img', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Retrieve and apply optimal adjustment values
        board_coord, img_new, board_lower, board_upper, border_lower, border_upper = determineImageSettings(img, attempts)
        print(attempts)
        print(board_coord)
        
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
        img_new = createMask(img, board_lower, board_upper, border_lower, border_upper)
        outcome = chess_board.update(img_new)

        if outcome:
            break

def testCodeWithImage() :
    with open("Chessboard Image Detection/data/output/imagevalues.csv", 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=
            ["Board Lower", 
            "Board Upper", 
            "Border Lower", 
            "Border Upper", 
            "Saturation", 
            "Contrast", 
            "Brightness", 
            "Black Point", 
            "Shadows"]
        )
        writer.writeheader()

    for i in range(5605, 5612):
        image_path = "Chessboard Image Detection/data/input/IMG_" + str(i) + ".jpeg"
        img = cv2.imread(image_path)

        # Retrieve and apply optimal adjustment values
        board_coord, img_new = determineImageSettings(img, i)

        # print(board_coord)

        # if board_coord is not None:
        #     # Create chess board object
        #     chess_board = ChessBoard(board_coord)
        #     chess_board.updateSquares(img_new)

        #     # display for debugging
        #     displaySquares(chess_board.squares)

if __name__ == "__main__":
    USE_CAMERA = False

    if USE_CAMERA:
        runVideoCapture()
    else: 
        testCodeWithImage()

# TODO:
# a1, etc is always white
# a2, etc is always black
# make moves accordingly