import cv2
import numpy as np

def extractCornersFromGrid(corners):
    grid = corners.reshape(7,7,2) # Convert 1D array to 3D (grid[row][col][x,y])

    # Rotate grid until its orientation is correct (top-left square has the smallest coordinates)
    count = 0
    while count < 4:
        top_left = grid[0, 0]
        top_right = grid[6, 0]
        bottom_left = grid[0,6]

        if (top_left[0] + top_left[1] > top_right[0] + top_right[1] or 
            top_left[0] + top_left[1] > bottom_left[0] + bottom_left[1]):
            grid = np.rot90(grid)
            count += 1
        else:
            break
    
    # Calculate average distance between each square 
    x_dist = (grid[0,6]-grid[0,0])/6 # Have 8 squares, 7 inner corners, and thus 6 intervals between corners
    y_dist = (grid[6,0]-grid[0,0])/6

    # Create 9x9 array including outer coordinates
    board = np.zeros((9, 9, 2)) # Empty numpy array
    top_left = grid[0,0]-x_dist-y_dist # Start point
    for row in range(9):
        for col in range(9):
            board[row, col] = top_left + (row * y_dist) + (col * x_dist)

    return board

def detectSquares(img):
    # Run detection algorithm
    board_detected, corners = cv2.findChessboardCorners(
        img, (7, 7),
        flags=cv2.CALIB_CB_ADAPTIVE_THRESH +
            cv2.CALIB_CB_FAST_CHECK +
            cv2.CALIB_CB_NORMALIZE_IMAGE
    )

    if not board_detected:
        print("Chessboard not detected")
        return False, None

    # Display chess board
    fnl = cv2.drawChessboardCorners(img, (7, 7), corners, board_detected)
    cv2.imshow("Chessboard with Corners", fnl)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return board_detected, corners

def preprocessImage(img, border_high=15, testing=False):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    otsu_th, squares_msk = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphology to clean up small noise
    kernel = np.ones((5,5), np.uint8)
    res = cv2.morphologyEx(squares_msk, cv2.MORPH_OPEN, kernel) # Removes small white noise
    res = cv2.morphologyEx(squares_msk, cv2.MORPH_CLOSE, kernel) # Fills small black holes

    # Manual threshold to single out black border
    border_msk = cv2.inRange(blurred, 0, border_high)

    # Merge both thresholds
    if testing:
        res = np.ones_like(gray)*230 # gray canvas for testing/manual adjustment
    else: 
        res = np.ones_like(gray)*255 # white canvas for game logic
    
    res[squares_msk == 255] = 0 # Add in squares mask as black
    res[border_msk == 255] = 255 # Add in border mask as white

    # Morphology to clean up small noise
    ker_size = int(5)
    kernel = np.ones((ker_size,ker_size), np.uint8)
    res = cv2.morphologyEx(res, cv2.MORPH_OPEN, kernel) # Removes small white noise
    res = cv2.morphologyEx(res, cv2.MORPH_CLOSE, kernel) # Fills small black holes

    # cv2.imshow("Mask", squares_msk)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # cv2.imshow("Res", res)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return res

def cropImage(img, model):
    results = model(img)[0]
    
    if not results:
        print("Board not detected by model")
        return img

    # Extract location
    box = results.boxes[0]
    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2]) # convert to int

    # Crop image to board
    cropped = img[y1:y2, x1:x2]

    return cropped

def makeImageSmall(img):
    display_height = 800 
    scale = display_height / img.shape[0]
    display_width = int(img.shape[1] * scale)
    img_small = cv2.resize(img, (display_width, display_height))
    return img_small