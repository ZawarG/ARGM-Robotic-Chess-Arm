import cv2
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
    # Crop and preprocess
    img_small = utils.makeImageSmall(img)
    img_cropped = utils.cropImage(img_small, model)
    img_mask = utils.preprocessImage(img_cropped)

    # Attempt automatic detection
    board_detected, corners = utils.detectSquares(img_mask) 

    # Manual detection if automatic fails
    if not board_detected:
        print("Automatic detection failed. Opening manual calibration.")
        board_detected, corners = calibration.adjustImageManually(img_small)
        img_cropped = img_small

    warped_img, coords = utils.getWarpedBoard(img_cropped, corners)

    return board_detected, coords, warped_img

def testCode() :
    USE_IMAGE = 1

    if USE_IMAGE:
        image_path = "Chessboard Image Detection/data/input/IMG_0302.jpg"
        img = cv2.imread(image_path)
    else:
        video_path = "Chessboard Image Detection/data/videos/game.mp4"
        cap = cv2.VideoCapture(video_path)

        # Grab the first frame for board localization
        ret, img = cap.read()
        if not ret:
            print("Failed to read video")
            return

    # Ask the user for their colour
    # player_colour = calibration.askPlayerColour()
    playerIsBlack = True # Player is black

    # Detect board
    board_detected, board_coord, warped_img = runCalibration(img, model)

    # Initialize game
    if board_detected is not None:
        # Create chess board object
        game = ChessBoard(board_coord, playerIsBlack)
        game.vision.initializeBoard(warped_img)

        # Display for debugging
        debugger.displaySquares(game.vision)
        game.close()

if __name__ == "__main__":
    USE_CAMERA = 0

    if USE_CAMERA:
        main()
    else: 
        model = YOLO("Chessboard Image Detection/models/best.pt")
        testCode()