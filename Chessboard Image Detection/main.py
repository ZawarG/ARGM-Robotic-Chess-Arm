import cv2
from chess_board import ChessBoard
from image_utils import createMask, localizeChessBoard
from debug_utils import displaySquares

def runVideoCapture():
    # Retrieve video, initialize coordinates
    cam = cv2.VideoCapture(0)
    board_coord = None

    # Run loop until board coordinates are found or until maximum attemps have been made
    attempts = 0
    max_attempts = 300
    while board_coord is None and attempts < max_attempts:
        # Read an image from the video stream
        ret, img = cam.read()
        if not ret: continue # Camera failed
        
        # Apply adjustments and retrieve image
        board_coord, img_mask = localizeChessBoard(img)

        # Increase attempt count
        attempts+=1

    if board_coord is None:
        # TODO: ask the user to apply filters
        pass

    # Create chess board object
    chess_board = ChessBoard(board_coord)
    if img_mask is not None: chess_board.updateSquares(img_mask)

    # Display chess squares for debugging
    displaySquares(chess_board.squares)

    # Game loop: checks for changes in the board and runs until the game is over
    running = True
    while running:
        ret, img = cam.read()
        if not ret: break

        # update chess board
        img_mask = createMask(img)
        outcome = chess_board.update(img_mask)
        chess_board.vis.update()

        if outcome:
            print("Game over! Winner:", outcome)
            running = False
    
    chess_board.close()
    cam.release()

def testCodeWithImage() :
    image_path = "Chessboard Image Detection/data/input/fromvid.png"
    img = cv2.imread(image_path)

    # Apply adjustments and retrieve image
    board_coord, img_mask = localizeChessBoard(img)

    print(board_coord)

    if board_coord is not None:
        # Create chess board object
        chess_board = ChessBoard(board_coord)
        chess_board.updateSquares(img_mask)

        # display for debugging
        displaySquares(chess_board.squares)

if __name__ == "__main__":
    USE_CAMERA = False

    if USE_CAMERA:
        runVideoCapture()
    else: 
        testCodeWithImage()

# TODO:
# a1, etc is always white
# a8, etc is always black
# make moves accordingly
# update outcome.winner accordingly
# HOW TO IMPLEMENT:
# Option 1: i need to know the perspective of the robot and which side of the screen it'll be on in relation
#           from there, i can check if it is on the a8 side or a1 side
# Option 2: tell the user to input