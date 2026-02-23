import cv2
import numpy as np

# Filter image
def applyImageAdjustments(img, sat = 1.0, con = 0.8, bright = -20, bp = 40, shadow = 1.6):
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

# Create binary masks -- one for square, one for board outline
def createMask(img, isManual=False):
    img = applyImageAdjustments(img)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 7)

    if isManual:
        # TODO: use this to implement user filtering image for chessboard detection
        pass
    else:
        # Otsu thresholding (automatically finds value for threshold by separating foreground and background)
        otsu_th, msk = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        squares_msk = 255 - msk

    # Manual threshold to single out black border
    border_msk = cv2.inRange(blurred, 0, 7)

    # Merge both thresholds
    res = np.ones_like(gray)*255 # White canvas
    res[squares_msk == 255] = 0 # Add in squares mask as black
    res[border_msk == 255] = 255 # Add in border mask as white

    # Morphology to clean up small noise
    kernel = np.ones((5,5), np.uint8)
    res = cv2.morphologyEx(res, cv2.MORPH_OPEN, kernel) # Removes small white noise
    res = cv2.morphologyEx(res, cv2.MORPH_CLOSE, kernel) # Fills small black holes

    # Display results
    # cv2.imshow('border', border_msk)
    # cv2.imshow('squares', squares_msk)
    # cv2.imshow('final', res)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return res

# Detect location of chess board
def localizeChessBoard(img):
    mask = createMask(img)

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