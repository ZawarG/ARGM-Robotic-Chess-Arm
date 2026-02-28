import cv2
from chess_board import ChessBoard
from image_utils import run, createMask
from debug_utils import displaySquares

def runVideoCapture():
    # Retrieve video, initialize coordinates
    cam = cv2.VideoCapture(0)
    board_coord = None

    # Localization loop
    while board_coord is None:
        # Read an image from the video stream
        ret, img = cam.read()
        if not ret: continue # Camera failed
        
        # Apply adjustments and retrieve image
        board_coord, img_mask = run(img)
    
    # Chess board object initialization
    if board_coord is not None: chess_board = ChessBoard(board_coord)
    if img_mask is not None: chess_board.updateSquares(img_mask)

    # Display chess squares for debugging
    displaySquares(chess_board.squares)

    # Game loop
    print("Game start")
    running = True
    while running:
        if not chess_board.vis.handle_events(): break # check if visualizer is closed

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

def testCodeWithImage() :
    image_path = "Chessboard Image Detection/data/input/fromvid.png"
    img = cv2.imread(image_path)

    # img_n = applyImageAdjustments(img)
    # mask = createMask(img_n)

    # cv2.imshow("original", img)
    # cv2.imshow("adjusted", img_n)
    # cv2.imshow("mask", mask)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # board_coord, img_mask = localizeChessBoard(img, mask)

    board_coord, img_mask = run()

    if board_coord is not None:
        # Create chess board object
        chess_board = ChessBoard(board_coord)
        chess_board.updateSquares(img_mask)

        # Display for debugging
        displaySquares(chess_board.squares)
        chess_board.close()

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