import cv2
import numpy as np

#  (\(\
# ( -.-)
# o_(")(")
# This file holds stateless helper functions for board geometry:
# perspective warping, grid generation, corner/board detection, and image prep

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
    from src.ui import debugger
    debugger.showOuterCorners(img, source_pts)

    M = getPerspectiveMatrix(source_pts, board_size)
    coords = generateGridCoordinates(board_size)
    warped_img = warpFrame(img, M, board_size)

    return M, coords, warped_img

# Square extraction
def orderPoints(points):
    rect = np.zeros((4, 2), dtype="float32")
    s = points.sum(axis=1)
    rect[0] = points[np.argmin(s)]   # Top-left
    rect[2] = points[np.argmax(s)]   # Bottom-right

    diff = np.diff(points, axis=1)
    rect[1] = points[np.argmin(diff)] # Top-right
    rect[3] = points[np.argmax(diff)] # Bottom-left
    return rect

def extractOuterCorners(corners):
    # Reshape 1D array to 3D grid[row][col][x,y]
    grid = corners.reshape(7,7,2)

    # Calculate average distance between each square (intervals between 7 corners = 6)
    x_dist = (grid[0,6]-grid[0,0])/6
    y_dist = (grid[6,0]-grid[0,0])/6

    # Retrieve four corners
    raw_edges = np.array([
        grid[0, 0] - x_dist - y_dist,
        grid[0, 6] + x_dist - y_dist,
        grid[6, 6] + x_dist + y_dist,
        grid[6, 0] - x_dist + y_dist
    ], dtype="float32")

    return orderPoints(raw_edges)

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
    from src.ui import debugger
    debugger.showDetectedCorners(img, corners, board_detected)

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

def cropImageToBoard(img, model):
    results = model(img)[0]

    if not results:
        print("Board not detected by model")
        return img, (0, 0)

    # annotated = results.plot()
    # cv2.imshow("YOLO Detection", annotated)
    # cv2.waitKey(1)

    # Extract location
    box = results.boxes[0]
    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2]) # convert to int

    # Crop image to board
    cropped = img[y1:y2, x1:x2]

    # Return crop origin so detected corners can be mapped back to the full (uncropped) image space
    return cropped, (x1, y1)

def makeImageSmall(img):
    display_height = 800
    scale = display_height / img.shape[0]
    display_width = int(img.shape[1] * scale)
    img_small = cv2.resize(img, (display_width, display_height))
    return img_small
