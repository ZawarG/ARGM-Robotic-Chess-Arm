import cv2
from ultralytics import YOLO
import utils
import calibration
from chess_board import ChessBoard
import debugger

def runCalibration(img, model):
    # Crop and preprocess
    img_small = utils.makeImageSmall(img)
    img_cropped = utils.cropImage(img_small, model)
    img_mask = utils.preprocessImage(img_cropped)

    # Attempt automatic detection
    board_detected, board = utils.detectSquares(img_mask) # board provides the internal corners of the board as a 1D array of tuples

    # Manual detection if automatic fails
    if not board_detected:
        print("Automatic detection failed. Opening manual calibration.")
        board_detected, corners = calibration.adjustImageManually(img_cropped)

    # Retrieve square coordinates
    corners = utils.extractCornersFromGrid(board)

    return board_detected, corners, img_cropped

def runVideoCapture():
    # Ask the user for their colour
    player_colour = calibration.askPlayerColour()

    # Retrieve video, initialize coordinates
    cam = cv2.VideoCapture(0)
    board_coord = None

    # Localization loop
    while board_coord is None:
        ret, img = cam.read() # Read an image from the video stream
        if not ret: continue # Camera failed
        
        board_detected, board_coord, img_mask = runCalibration(img, model) # Detect chessboard squares
    
    # Initialize game
    if board_coord is not None: chess_board = ChessBoard(board_coord, player_colour)
    if img_mask is not None: chess_board.updateSquares(img_mask)

    # Display chess squares for debugging
    debugger.displaySquares(chess_board.squares)

    # Game loop
    print("Game start")
    running = True
    while running:
        if not chess_board.vis.handle_events(): break # Check if visualizer is closed

        ret, img = cam.read()
        if not ret: break

        # process vision layer
        img_mask = createMask(img)

        # update fsm: logic, animation, drawing board all happens here
        outcome = chess_board.update(img_mask)
        
        # check for game end
        if outcome:
            print("Game over! Winner:", outcome)
            running = False

    # clean up
    chess_board.vis.quit() 
    chess_board.close()
    cam.release()

def testCode() :
    USE_IMAGE = 1

    if USE_IMAGE:
        image_path = "Chessboard Image Detection/data/input/IMG_5605.jpeg"
        img = cv2.imread(image_path)
    else:
        video_path = "Chessboard Image Detection/data/videos/game-1.mp4"
        cap = cv2.VideoCapture(video_path)

        # Grab the first frame for board localization
        ret, img = cap.read()
        if not ret:
            print("Failed to read video")
            return

    # Ask the user for their colour
    player_colour = calibration.askPlayerColour()

    # Detect board
    board_detected, board_coord, img_mask = runCalibration(img, model)

    # Initialize game
    if board_detected is not None:
        # Create chess board object
        chess_board = ChessBoard(board_coord, player_colour)
        chess_board.updateSquares(img_mask)

        # Display for debugging
        debugger.displaySquares(chess_board.squares)
        chess_board.close()

if __name__ == "__main__":
    model = YOLO("Chessboard Image Detection/models/best.pt")

    USE_CAMERA = False

    if USE_CAMERA:
        runVideoCapture()
    else: 
        testCode()