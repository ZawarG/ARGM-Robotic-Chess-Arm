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
def getSquareFeatures(img, border_ratio=0.1):
    # Crop
    height, width = img.shape[:2]
    b_top_height = int(height * border_ratio)
    b_bot_height = int(height * border_ratio * 2) #  Double crop at bottom to account for how piece tops overlapping due camera angle
    b_width = int(width * border_ratio / 2) # Half crop on sides
    img = img[b_top_height:height-b_bot_height, b_width:width-b_width] 

    # cv2.imshow("crop", img)
    # cv2.waitKey(0)

    # Detect average brightness and std
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray)
    std = gray.std()

    return gray, avg_brightness, std

def checkOccupancy(square, is_light, profile, curr_frame_bright):
    triggered = False

    gray, avg_brightness, std = getSquareFeatures(square)

    # Retrieve brightness offset
    start_frame_bright = profile['start_frame_bright']
    brightness_offset = curr_frame_bright - start_frame_bright # Accounts for exposure changes during game

    # Retrieve profile variables
    avg_bright = profile['avg_bright'] + brightness_offset
    std_bright = profile['std_bright']
    avg_std = profile['avg_std']
    std_std = profile['std_std']
    avg_sq = profile['avg_sq'] + brightness_offset
    std_sq = profile['std_sq']
    
    # # Calculate z-scores
    # brightness_z = (avg_bright - avg_brightness) / std_bright
    # texture_z = (std - avg_std) / std_std
    fill_z = np.abs(gray.astype(np.float32) - avg_sq) / (std_sq + 1)

    # # Check if z scores are within correct range
    # bright_trigger = brightness_z < 2
    # texture_trigger = texture_z > 3
    # triggered = bright_trigger or texture_trigger

    # Brightness check (is square significantly lighter/darker than empty avg)
    if is_light:
        # Light square
        if avg_brightness < avg_bright - (2*std_bright):
            triggered = True
    else:
        # Dark square
        if avg_brightness > avg_bright + (2*std_bright):
            triggered = True
        
    # Texture/contrast check
    if std > avg_std + 1.8 * std_std:
        triggered = True

    # Detect contour area and shape
    fill_ratio = detectContourArea(gray, fill_z)

    return fill_ratio > 0.05

    return triggered

def detectContourArea(square, z):
    # diff = cv2.absdiff(square, avg_sq) # first find which pixels changed compared to the empty square

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

    # overlay = cv2.cvtColor(square, cv2.COLOR_GRAY2RGB)

    # print(mask.shape, overlay.shape)

    # overlay[mask > 0] = [255, 0, 0]

    # fig, ax = plt.subplots(1, 3, figsize=(12, 4))

    # ax[0].imshow(square, cmap='gray')
    # ax[0].set_title("Square")

    # ax[1].imshow(mask, cmap='gray')
    # ax[1].set_title(f"Mask\nFill={fill_ratio:.3f}")

    # ax[2].imshow(overlay)
    # ax[2].set_title("Foreground Overlay")

    # for a in ax:
    #     a.axis('off')

    # plt.tight_layout()
    # plt.show()

    return fill_ratio

    # _, mask = cv2.threshold( # threshold the difference image (this basically removes the background before we detect)
    #     diff,
    #     30,      # threshold value
    #     255,
    #     cv2.THRESH_BINARY
    # )

    # contours, _ = cv2.findContours(
    #     mask,
    #     cv2.RETR_EXTERNAL,
    #     cv2.CHAIN_APPROX_SIMPLE
    # )

    # areas = [cv2.contourArea(cnt) for cnt in contours]

    # largest_area = max(areas) if areas else 0

    # print("Largest contour area:", largest_area)

    # square_area = square.shape[0] * square.shape[1]

    # fill_ratio = largest_area / square_area

    # print(fill_ratio)

    # debug = cv2.cvtColor(square, cv2.COLOR_GRAY2BGR)

    # cv2.drawContours(
    #     debug,
    #     contours,
    #     -1,
    #     (0, 255, 0),
    #     2
    # )

    # cv2.imshow("Contours", debug)

    # cv2.waitKey(0)

