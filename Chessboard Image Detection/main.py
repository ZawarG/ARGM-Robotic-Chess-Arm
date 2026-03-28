import cv2
import tkinter as tk
from tkinter import ttk
from chess_board import ChessBoard
from image_utils import run, createMask
from debug_utils import displaySquares

def askPlayerColour():
    # Ask player if they are white or black
    result = [None] # True for player = black and False for player = white

    root = tk.Tk()
    root.title("Color Selection")
    root.resizable(False, False)

    # Center the window on screen
    window_width, window_height = 400, 300
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Styles and colour
    root.configure(bg="#1a1a2e")
    style = ttk.Style(root)
    style.theme_use("clam")

    tk.Label(root, text="Choose Your Side", font=("Georgia", 16, "bold"), bg="#1a1a2e", fg="#e0d5c5",).pack(pady=(24, 4))

    tk.Label(root, text="Which color are you playing as?", font=("Georgia", 10), bg="#1a1a2e", fg="#9a9ab0",).pack(pady=(0, 18))

    btn_frame = tk.Frame(root, bg="#1a1a2e")
    btn_frame.pack()

    def choose(colour: bool):
        result[0] = colour
        root.destroy()

    # White button
    white_btn = tk.Button(btn_frame, text="♔ White", width=10, font=("Georgia", 12, "bold"), bg="#2c2c3e", fg="#e0d5c5", activebackground="#3d3d55", activeforeground="#ffffff", relief="flat", cursor="hand2", command=lambda: choose(False),)
    white_btn.grid(row=0, column=0, padx=14, ipady=6)

    # Black button
    black_btn = tk.Button(btn_frame, text="♚ Black", width=10, font=("Georgia", 12, "bold"), bg="#f0ede0", fg="#1a1a2e", activebackground="#ffffff", activeforeground="#1a1a2e", relief="flat", cursor="hand2", command=lambda: choose(True),)
    black_btn.grid(row=0, column=1, padx=14, ipady=6)

    # If user closes window without choosing, default to player being white
    root.protocol("WM_DELETE_WINDOW", lambda: choose(False))

    root.mainloop()
    return result[0]

def runVideoCapture():
    # Ask the user for their colour
    player_colour = askPlayerColour()

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
    if board_coord is not None: chess_board = ChessBoard(board_coord, player_colour)
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
    # Ask the user for their colour
    player_colour = askPlayerColour()

    image_path = "Chessboard Image Detection/data/input/IMG_5605.jpeg"
    img = cv2.imread(image_path)

    board_coord, img_mask = run(img)

    if board_coord is not None:
        # Create chess board object
        chess_board = ChessBoard(board_coord, player_colour)
        chess_board.updateSquares(img)

        # Display for debugging
        displaySquares(chess_board.squares)
        chess_board.close()

if __name__ == "__main__":
    USE_CAMERA = False

    if USE_CAMERA:
        runVideoCapture()
    else: 
        testCodeWithImage()