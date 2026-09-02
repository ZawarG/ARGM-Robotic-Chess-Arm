import cv2
import numpy as np
from ultralytics import YOLO
from src.logic.chess_board import ChessBoard
import src.vision.utils as utils
import src.ui.calibration as calibration
import src.ui.debugger as debugger

#  (\(\
# ( -.-)
# o_(")(")
# This file runs essential functions used to detect the chess board, followed by the main game loop

def main():
    model = YOLO("Chessboard Image Detection/models/best.pt")
    cam = cv2.VideoCapture(0)

    player_is_black = calibration.askPlayerColour()

    # Localization phase
    board_detected = False
    while not board_detected:
        ret, img = cam.read()
        if not ret: continue

        board_detected, board_coord, warped_img = runCalibration(img, model)

    # Game phase
    game = ChessBoard(board_coord, player_is_black)
    game.vision.initializeBoard(warped_img)
    
    while True:
        ret, img = cam.read()
        if not ret: break
        
        # Process vision and game logic
        winner = game.update(img)
        if winner is not None:
            print(winner)
            break
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    game.close()
    cam.release()

def runCalibration(img, model):
    img_small = utils.makeImageSmall(img) # Reduce size of image
    img_cropped, (offset_x, offset_y) = utils.cropImageToBoard(img_small, model) # Detect/crop to board using YOLO

    # Attempt automatic detection and extract corners
    img_mask = utils.preprocessImage(img_cropped)
    board_detected, corners = utils.detectSquares(img_mask)

    # Map corners from the tight YOLO crop back into full img_small space.
    # extractOuterCorners can land outside the tight crop
    # Warping img_small with an offset ensures that perspective transform doesn't sample out-of-bounds regions.
    if board_detected:
        corners = corners + np.array([offset_x, offset_y], dtype=corners.dtype)

    # Manual detection if automatic fails
    if not board_detected:
        print("Automatic detection failed. Opening manual calibration.")
        board_detected, corners = calibration.adjustImageManually(img_small)

    M, coords, warped_img = utils.runInitialCalibration(img_small, corners)

    return board_detected, coords, warped_img, M

def testCode(model) :
    USE_IMAGE = 0

    if USE_IMAGE:
        image_path = "Chessboard Image Detection/data/input/IMG_0302.jpg"
        img = cv2.imread(image_path)

        # Detect board
        board_detected, board_coord, warped_img, M = runCalibration(img, model)

        if not board_detected:
            return
        
        # Initialize game (single image: calibrate immediately from this frame)
        game = ChessBoard(board_coord, M, warped_img=warped_img)

        debugger.displaySquares(game.vision)

    else:
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

        # Build the game, but don't calibrate occupancy yet
        # The light/dark reference profiles need the populated board, which the user sets up next
        game = ChessBoard(board_coord, M)

        paused = False

        while True:
            # If not paused, capture a new frame
            if not paused:
                ret, img = cap.read()
                if not ret:
                    break

            if not game.started:
                # Setup phase: 
                # Show the live warped feed so the user can place the pieces
                # Press 'S' to calibrate from this frame and start.
                warped = utils.warpFrame(utils.makeImageSmall(img), M)
                live_display = warped.copy()
                cv2.putText(live_display, "Set up pieces, then press S to start",
                            (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            else:
                # Game phase: update engine, then draw the occupancy overlay
                if not paused:
                    winner = game.update(img)
                    if winner is not None:
                        print("game over")

                live_display = debugger.drawOccupancyOverlay(game.vision)

            # Show live video window
            cv2.imshow("Live Chess Matrix Tracker", live_display)

            # Intercept keyboard keys
            key = cv2.waitKey(1) & 0xFF

            if key == ord('s') and not game.started:  # 'S' calibrates + starts the game
                game.beginGame(img)  # uses the CURRENT frame (pieces in place)
                print("Game started")

            elif key == ord(' '):  # SPACEBAR toggles pause/play
                paused = not paused
                print("Status:", "PAUSED" if paused else "PLAYING")

            elif key == ord('q'):  # 'Q' quits the stream
                break

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