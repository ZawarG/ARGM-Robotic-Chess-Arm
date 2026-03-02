import cv2
import numpy as np

# Filter image
def applyImageAdjustments(img, sat = 5.0, con = 0.6, bright = -100, bp = 0, wp = 255, shadow = 1.6):
    # Saturation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = np.clip(s.astype(np.float32) * sat, 0, 255).astype(np.uint8)
    img = cv2.cvtColor(cv2.merge([h, s, v]), cv2.COLOR_HSV2BGR)

    # Contrast, brightness
    img = cv2.convertScaleAbs(img, alpha=con, beta=bright)

    # Black point, white point, shadows (LUT)
    # Shadow > 1.0 lifts shadows, < 1.0 darkens them
    invGamma = 1.0 / shadow

    table = np.array([
        np.clip((( (i - bp) / (wp - bp) ) ** invGamma) * 255, 0, 255) 
        if i > bp else 0 
        for i in range(256)
    ]).astype("uint8")
    
    return cv2.LUT(img, table)

# Create binary masks -- one for square, one for board outline
def createMask(img, otsu_offset=0, border_high=7, testing=False):
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
    if testing:
        res = np.ones_like(gray)*230 # gray canvas for testing/manual adjustment
    else: 
        res = np.ones_like(gray)*255 # white canvas for game logic
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
    view_window = "Chessboard View"
    cv2.namedWindow(view_window, cv2.WINDOW_NORMAL)

    # Adjust size of image
    display_height = 500 
    scale = display_height / img.shape[0]
    display_width = int(img.shape[1] * scale)
    img_small = cv2.resize(img, (display_width, display_height))

    # Only run detection every X loops to reduce lag
    loop_count = 0
    corners = None
    mask = None
    prev_pos = [50, 6, 0, 0, 255, 16, 7]
    ret = False

    createTrackbars(view_window, prev_pos)
    print("Adjust sliders until the board is detected. Press 'ENTER' to confirm or 'ESC' to cancel.")

    while True:
        loop_count+=1

        # Get current trackbar positions
        curr_pos = list(getTrackbarPos(view_window))

        # Check if anything has changed
        changed_pos = curr_pos != prev_pos

        # Only process if sliders change
        if changed_pos or not ret:
            # Enforce values
            sat, con, bright, bp, wp, shd, border_lim = enforceValues(curr_pos, prev_pos, view_window)

            # Process image
            adjusted = applyImageAdjustments(img_small, sat, con, bright, bp, wp, shd)
            mask = createMask(adjusted, border_high=border_lim, testing=True)
        
            # Attempt localization every 5 frames
            if loop_count%5 == 0:
                ret, corners = localizeChessBoard(adjusted, mask)

            # Store positions
            prev_pos = curr_pos

        # Prepare display
        display_img = adjusted.copy()
        display_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) # convert mask to format that can be displayed

        # Draw ui
        drawAndDisplay(display_img, display_mask, ret, corners, [sat,con,bright,bp,wp,shd,border_lim], display_height, view_window)

        # Interaction handling
        key = cv2.waitKey(30) & 0xFF
        if key == 13: # ENTER key
            full_corners = corners / scale
            if ret and corners is not None:
                full_corners = corners / scale
                # Rerun full adjustment (previous adjustment was with smaller image)
                final_adj = applyImageAdjustments(img, sat, con, bright, bp, wp, shd)
                final_mask = createMask(final_adj, border_high=border_lim)
                print(sat, con, bright, bp, wp, shd, border_lim)
                return reshapeCorners(full_corners), final_mask
        elif key == 27: # ESC key
            break

    print(key)
    cv2.destroyAllWindows()
    return corners, mask

def drawAndDisplay(img, mask, ret, corners, parameters, height, window):
    # Draw corners on the preview if found
    if ret:
        cv2.drawChessboardCorners(img, (7, 7), corners, ret)

    # Update status text
    status_text = "CALIBRATED: Type ENTER to confirm" if ret else "SCANNING..."
    status_colour = (0, 255, 100) if ret else (0, 100, 255) # green or orange

    # Overlays to display text
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (img.shape[1], 40), (40, 40, 40), -1)
    cv2.rectangle(overlay, (0, img.shape[0]-30), (img.shape[1], img.shape[0]), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)

    overlay = mask.copy()
    cv2.rectangle(overlay, (0, 0), (mask.shape[1], 40), (40, 40, 40), -1)
    cv2.addWeighted(overlay, 0.6, mask, 0.4, 0, mask)
    
    # Add status
    cv2.putText(img, f"{status_text}", (15, 27), 
                cv2.FONT_HERSHEY_DUPLEX, 0.7, status_colour, 1, cv2.LINE_AA)
    
    # Add small parameter text at bottom
    values_txt = f"SAT:{parameters[0]} | CON:{parameters[1]} | BRT:{parameters[2]} | BP:{parameters[3]} | WP:{parameters[4]} | SHD:{parameters[5]} | BRDR:{parameters[6]}"
    cv2.putText(img, values_txt, (10, img.shape[0]-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.37, (200, 200, 200), 1, cv2.LINE_AA)
    
    # Add label for mask side
    cv2.putText(mask, "BINARY MASK", (10, 27), 
                cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Add divider between images
    divider = np.zeros((height, 5, 3), dtype=np.uint8) + 180
    stacked = np.hstack((img, divider, mask))

    # Display
    cv2.imshow(window, stacked)
    
def createTrackbars(window_name, prev):
    # Create trackbars (scaled bc they only handle integers)
    cv2.createTrackbar("Saturation x10", window_name, prev[0], 50, lambda x: None) 
    cv2.createTrackbar("Contrast x10", window_name, prev[1], 30, lambda x: None)
    cv2.createTrackbar("Brightness", window_name, prev[2], 255, lambda x: None) # offset by 100 to allow negative
    cv2.createTrackbar("Black Point", window_name, prev[3], 100, lambda x: None)
    cv2.createTrackbar("White Point", window_name, prev[4], 255, lambda x: None)
    cv2.createTrackbar("Shadow x10", window_name, prev[5], 50, lambda x: None)
    cv2.createTrackbar("Border Limit", window_name, prev[6], 50, lambda x: None)

def getTrackbarPos(window_name):
    sat = cv2.getTrackbarPos("Saturation x10", window_name)
    con = cv2.getTrackbarPos("Contrast x10", window_name)
    bright = cv2.getTrackbarPos("Brightness", window_name) - 100 
    bp = cv2.getTrackbarPos("Black Point", window_name)
    wp = cv2.getTrackbarPos("White Point", window_name)
    shd = cv2.getTrackbarPos("Shadow x10", window_name)
    border_lim = cv2.getTrackbarPos("Border Limit", window_name)

    return sat, con, bright, bp, wp, shd, border_lim

def enforceValues(curr_pos, prev_pos, view_window):
    sat, con, bright, bp, wp, shd, border_lim = curr_pos

    # Enforce that con, bp, wp, shd greater than their min values
    con = max(con, 1) # minimum 0.1
    bp = max(bp, 0) # minimum 0
    wp = max(wp, 0) # minimum 0
    shd = max(shd, 1) # minimum 0.1

    # Enforce that wp > bp
    if bp >= wp:
        if bp != prev_pos[3]: # black point was moved
            wp = min(bp+1, 255)
            cv2.setTrackbarPos("White Point", view_window, wp)
        elif wp != prev_pos[4]:
            bp = max(wp - 1, 0) # Push BP backward
            cv2.setTrackbarPos("Black Point", view_window, bp)

    # Divide needed values by 10
    if sat != 0: sat=sat/10.0
    con=con/10.0
    shd=shd/10.0

    return sat, con, bright, bp, wp, shd, border_lim

def run(img):
    # first try automatic detection with default adjustments
    img_n = applyImageAdjustments(img)
    mask = createMask(img_n)
    ret, coords = localizeChessBoard(img, mask)
    corners = reshapeCorners(coords) 

    if coords is None:
        print("Auto-detection failed")
        coords, mask = adjustImageManually(img)

    return corners, mask

if __name__ == "__main__":
    image_path = "Chessboard Image Detection/data/input/IMG_5605.jpeg"
    img = cv2.imread(image_path)
    adjustImageManually(img)