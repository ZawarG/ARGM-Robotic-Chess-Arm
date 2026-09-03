import cv2
import numpy as np
from ultralytics import YOLO
from src.logic.chess_board import ChessBoard
import src.vision.geometry as geometry
import src.ui.calibration as calibration
import src.ui.controls as controls

#  (\(\
# ( -.-)
# o_(")(")
# This file runs essential functions used to detect the chess board, followed by the main game loop

def main():
    model = YOLO("Chessboard Image Detection/models/best.pt")
    cam = cv2.VideoCapture(0)

    # Localization phase
    board_detected = False
    while not board_detected:
        ret, img = cam.read()
        if not ret: continue

        board_detected, board_coord, warped_img, M = runCalibration(img, model)

    # Game phase
    # Live play: robot_enabled defaults to True, so engine/arm plays opponent.
    # Don't pass warped_img: occupancy is calibrated on the populated board when
    # the user presses 'S' (beginGame), matching the setup flow in testCode.
    game = ChessBoard(board_coord, M, robot_enabled=True)

    # Shared interactive loop (setup 'S', pause SPACE, promotion q/r/b/n + ENTER,
    # diff heatmap 'd', quit 'q')
    controls.runGameLoop(cam, game, M)

    game.close()
    cam.release()
    cv2.destroyAllWindows()

def runCalibration(img, model):
    img_small = geometry.makeImageSmall(img) # Reduce size of image
    img_cropped, (offset_x, offset_y) = geometry.cropImageToBoard(img_small, model) # Detect/crop to board using YOLO

    # Attempt automatic detection and extract corners
    img_mask = geometry.preprocessImage(img_cropped)
    board_detected, corners = geometry.detectSquares(img_mask)

    # Map corners from the tight YOLO crop back into full img_small space
    # extractOuterCorners can land outside the tight crop
    # Warping img_small with an offset ensures that perspective transform doesn't sample out-of-bounds regions
    if board_detected:
        corners = corners + np.array([offset_x, offset_y], dtype=corners.dtype)

    # Manual detection if automatic fails
    if not board_detected:
        print("Automatic detection failed. Opening manual calibration.")
        board_detected, corners = calibration.adjustImageManually(img_small)

    M, coords, warped_img = geometry.runInitialCalibration(img_small, corners)

    return board_detected, coords, warped_img, M

def testCode(model):
    video_path = "Chessboard Image Detection/data/videos/starts_occupied.mov"
    cap = cv2.VideoCapture(video_path)

    # Grab the first frame for board localization
    ret, img = cap.read()
    if not ret:
        print("Failed to read video")
        return

    # Localize the board on the EMPTY board (corner/grid detection needs it empty)
    board_detected, board_coord, warped_img, M = runCalibration(img, model)

    if board_detected is None:
        return

    # Build game but don't calibrate occupancy yet
    # Light/dark reference profiles need populated board, which user sets up next
    # robot_enabled=False —recorded-video test path, both sides are tracked visually instead of engine/arm playing opponent
    game = ChessBoard(board_coord, M, robot_enabled=False)

    # Shared interactive loop (setup 'S', pause SPACE, promotion q/r/b/n + ENTER, diff heatmap 'd', quit 'q')
    controls.runGameLoop(cap, game, M)

    game.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    USE_CAMERA = 0

    if USE_CAMERA:
        main()
    else: 
        model = YOLO("Chessboard Image Detection/models/best.pt")
        testCode(model)