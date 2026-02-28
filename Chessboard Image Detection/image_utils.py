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
def createMask(img, otsu_offset=0, border_high=7):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 7)

    # Otsu thresholding (automatically finds value for threshold by separating foreground and background)
    otsu_th, msk = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    squares_msk = 255 - msk

    # Apply manual offset to Otsu if desired
    if otsu_offset != 0:
        _, msk = cv2.threshold(blurred, otsu_th + otsu_offset, 255, cv2.THRESH_BINARY)

    # Manual threshold to single out black border
    border_msk = cv2.inRange(blurred, 0, border_high)

    # Merge both thresholds
    res = np.ones_like(gray)*255 # White canvas
    res[squares_msk == 255] = 0 # Add in squares mask as black
    res[border_msk == 255] = 255 # Add in border mask as white

    # Morphology to clean up small noise
    kernel = np.ones((5,5), np.uint8)
    res = cv2.morphologyEx(res, cv2.MORPH_OPEN, kernel) # Removes small white noise
    res = cv2.morphologyEx(res, cv2.MORPH_CLOSE, kernel) # Fills small black holes

    return res

# Detect location of chess board
def localizeChessBoard(img, mask):
    # Built in method to detect chess board from binary mask
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
        
        print("Checkerboard Found")
        return ret, corners

    else:
        print("No Checkerboard Found")
        return None, None
    
def reshapeCorners(corners):
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

    return board

def adjustImageManually(img):
    window_name = "Tuning"
    cv2.namedWindow(window_name)

    # Force window to a reasonable size
    cv2.resizeWindow(window_name, 1000, 400)

    # Adjust size of image
    display_height = 500 
    scale = display_height / img.shape[0]
    display_width = int(img.shape[1] * scale)

    img_small = cv2.resize(img, (display_width, display_height))

    # Create trackbars (scaled bc they only handle integers)
    cv2.createTrackbar("Saturation x10", window_name, 10, 50, lambda x: None) 
    cv2.createTrackbar("Contrast x10", window_name, 8, 30, lambda x: None)
    cv2.createTrackbar("Brightness", window_name, 100, 255, lambda x: None) # offset by 100 to allow negative
    cv2.createTrackbar("Black Point", window_name, 40, 100, lambda x: None)
    cv2.createTrackbar("Shadow x10", window_name, 16, 50, lambda x: None)
    # cv2.createTrackbar("Mask Sens", window_name, 50, 100, lambda x: None)
    cv2.createTrackbar("Border Limit", window_name, 7, 50, lambda x: None)

    print("Adjust sliders until the board is detected. Press 'ENTER' to confirm or 'ESC' to cancel.")

    # Only run detection every X loops to reduce lag
    loop_count = 0
    coords = None
    mask = None

    while True:
        loop_count+=1
        ret = None

        # get current trackbar positions
        sat = cv2.getTrackbarPos("Saturation x10", window_name) / 10.0
        con = cv2.getTrackbarPos("Contrast x10", window_name) / 10.0
        bright = cv2.getTrackbarPos("Brightness", window_name) - 100 
        bp = cv2.getTrackbarPos("Black Point", window_name)
        shd = cv2.getTrackbarPos("Shadow x10", window_name) / 10.
        border_lim = cv2.getTrackbarPos("Border Limit", window_name)

        # Apply existing pipeline
        adjusted = applyImageAdjustments(img_small, sat, con, bright, bp, shd)
        mask = createMask(adjusted)
        display_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) # convert to format that can be displayed
        
        # Attempt localization
        if loop_count%5 == 0:
            ret, corners = localizeChessBoard(adjusted, mask)

        # Draw corners on the preview if found
        if ret:
            cv2.drawChessboardCorners(display_img, (7, 7), corners, ret)

        # status header
        status_color = (0, 255, 0) if coords is not None else (0, 0, 255)
        display_img = adjusted.copy()
        cv2.putText(display_img, "FOUND" if coords is not None else "SEARCHING", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        # adjusted image and mask displayed side-by-side for comparison
        stacked = np.hstack((display_img, display_mask))
        cv2.imshow(window_name, stacked)

        # 6. Interaction handling
        key = cv2.waitKey(1) & 0xFF
        if key == 13: # ENTER key
            full_corners = corners / scale

            return reshapeCorners(full_corners), createMask(applyImageAdjustments(img, sat, con, bright, bp), border_high=border_lim)
        elif key == 27: # ESC key
            break

    cv2.destroyWindow(window_name)
    return coords, mask

def run(img):
    # first try automatic detection with default adjustments
    img_n = applyImageAdjustments(img)
    mask = createMask(img_n)
    coords, mask = localizeChessBoard(img, mask)

    if coords is None:
        print("Auto-detection failed")
        coords, mask = adjustImageManually(img)

    return coords, mask


image_path = "Chessboard Image Detection/data/input/IMG_5605.jpeg"
img = cv2.imread(image_path)
adjustImageManually(img)