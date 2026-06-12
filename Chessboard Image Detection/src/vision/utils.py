import cv2
import numpy as np
import matplotlib.pyplot as plt

#  (\(\
# ( -.-)
# o_(")(")
# This file holds stateless helper functions related to computer vision

# Board warping
def getPerspectiveMatrix(source_pts, board_size=800):
    dest_pts = np.array([
        [0, 0], 
        [board_size, 0], 
        [board_size, board_size], 
        [0, board_size]
    ], dtype="float32")

    return cv2.getPerspectiveTransform(source_pts, dest_pts)

def generateGridCoordinates(board_size=800):
    # Generate 9x9 coordinates
    coords = np.zeros((9, 9, 2), dtype=np.float32)
    lin_space = np.linspace(0, board_size, 9)
    
    for row in range(9):
        for col in range(9):
            coords[row, col] = [lin_space[col], lin_space[row]]

    return coords

def warpFrame(img, M, board_size=800):
    return cv2.warpPerspective(img, M, (board_size, board_size))

def runInitialCalibration(img, source_pts, board_size=800):
    M = getPerspectiveMatrix(source_pts, board_size)
    coords = generateGridCoordinates(board_size)
    warped_img = warpFrame(img, M, board_size)

    return M, coords, warped_img

# Square extraction
def extractOuterCorners(corners):
    # Reshape 1D array to 3D grid[row][col][x,y]
    grid = corners.reshape(7,7,2)

    # Fix orientation (rotate grid until top-left square has smallest coordinates)
    count = 0
    while count < 4:
        tl = grid[0, 0]
        bl = grid[6, 0]
        tr = grid[0,6]

        if (tl[0] + tl[1] > tr[0] + tr[1] or tl[0] + tl[1] > bl[0] + bl[1]):
            grid = np.rot90(grid)
            count += 1
        else:
            break
    
    # Calculate average distance between each square (intervals between 7 corners = 6)
    x_dist = (grid[0,6]-grid[0,0])/6
    y_dist = (grid[6,0]-grid[0,0])/6

    # Retrieve four corners
    top_left = grid[0,0] - x_dist - y_dist
    top_right = grid[0,6] + x_dist - y_dist
    bottom_left = grid[6,0] - x_dist + y_dist
    bottom_right = grid[6,6] + x_dist + y_dist

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype="float32")

# Board detection
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

    return board_detected, extractOuterCorners(corners)

def preprocessImage(img, border_high=15, testing=False):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    blurred = gray

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

# Square occupancy
def adjustSquare(img, border_ratio=0.1):
    # Crop
    height, width = img.shape[:2]
    b_top_height = int(height * border_ratio)
    b_bot_height = int(height * border_ratio * 3) #  Double crop at bottom to account for how piece tops overlapping due camera angle
    b_width = int(width * border_ratio)
    img = img[b_top_height:height-b_bot_height, b_width:width-b_width] 

    # Detect average brightness and std
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    return gray

def checkOccupancy(square, profile, name, FILL_THRESH = 0.03):
    gray = adjustSquare(square)

    # Retrieve brightness offset
    start_frame_bright = profile['avg_bright']
    curr_frame_bright = profile['curr_bright']
    brightness_offset = curr_frame_bright - start_frame_bright # Accounts for exposure changes during game

    # Retrieve profile variables
    avg_sq = profile['avg_sq'] + brightness_offset
    std_sq = profile['std_sq']
    
    # Calculate z-score
    fill_z = np.abs(gray.astype(np.float32) - avg_sq) / (std_sq + 1)

    # Detect contour area and shape
    fill_ratio = detectContourArea(fill_z)

    if name=='h6':
        print(name, fill_ratio, fill_ratio>FILL_THRESH, curr_frame_bright, start_frame_bright)

    return fill_ratio > FILL_THRESH

def detectContourArea(z):
    mask = (z > 3).astype(np.uint8) * 255

    kernel = np.ones((5,5), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    kernel2 = np.ones((3,3), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel2
    )

    fill_ratio = np.count_nonzero(mask) / mask.size

    return fill_ratio

