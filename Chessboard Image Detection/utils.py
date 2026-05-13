import cv2
import numpy as np

def getWarpedBoard(img, source_pts, board_size=800):
    dest_pts = np.array([
        [0, 0], 
        [board_size, 0], 
        [board_size, board_size], 
        [0, board_size]
    ], dtype="float32")

    # Perspective transform matrix
    M = cv2.getPerspectiveTransform(source_pts, dest_pts)

    warped_img = cv2.warpPerspective(img, M, (board_size, board_size))

    cv2.imshow("warped", warped_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Generate 9x9 coordinates
    coords = np.zeros((9, 9, 2), dtype=np.float32)
    lin_space = np.linspace(0, board_size, 9)
    
    for row in range(9):
        for col in range(9):
            coords[row, col] = [lin_space[col], lin_space[row]]


    return warped_img, coords

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

def checkOccupancy(img, is_light, coord, border_ratio=0.2):
    # Crop
    height, width = img.shape[:2]
    b_height = int(height * border_ratio)
    b_width = int(width * border_ratio)
    img = img[b_height:height-b_height, b_width:width-b_width]

    # Detect average brightness
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray)

    print(avg_brightness, coord, is_light)
    # cv2.imshow("gray", gray)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # Compare brightness to square type (contrasting piece and square)
    if is_light:
        # Dark on light square
        if avg_brightness < 150:
            return True
    else:
        # Light on dark square
        if avg_brightness > 160:
            return True
        
    # Similar colour piece and square
    if gray.std() > 25: 
        return True

    return False