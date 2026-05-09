import cv2
import os
import numpy as np
from image_utils import run, createMask
from chess_board import ChessBoard
from debug_utils import displaySquares

def test_occupancy_one_shot():
    # 1. Setup Absolute Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Update these filenames to match your local files exactly
    empty_board_path = os.path.join(script_dir, "data", "input", "EMPTY_BOARD.jpeg")
    game_board_path = os.path.join(script_dir, "data", "input", "IMG_5605.jpeg")

    # 2. Load Images
    img_empty = cv2.imread(empty_board_path)
    img_game = cv2.imread(game_board_path)

    if img_empty is None or img_game is None:
        print(f"Error: Could not find images.\nEmpty: {empty_board_path}\nGame: {game_board_path}")
        return

    # 3. Calibration Phase (Using the Empty Board)
    print("Step 1: Localizing grid on empty board...")
    # 'run' handles the image adjustments and findChessboardCorners
    coords, _ = run(img_empty)

    if coords is None:
        print("❌ Localization failed on the empty board. Corners not found.")
        return
    print("✅ Calibration successful.")

    # 4. Analysis Phase (Applying Grid to the Game Board)
    print("Step 2: Analyzing game board with pieces...")
    
    # Initialize ChessBoard with the empty-board coordinates
    # Using False for white player as a placeholder
    cb = ChessBoard(coords, False)
    
    # Create the binary mask for the game image
    game_mask = createMask(img_game)
    
    # Map the game image (or mask) onto the calibrated squares
    # We use 'img_game' here so displaySquares shows the actual pieces
    cb.updateSquares(img_game)

    # 5. Visualization
    print("Step 3: Launching debug visualizer...")
    # This calls your existing function that draws the red/green boxes
    displaySquares(cb.squares)

if __name__ == "__main__":
    test_occupancy_one_shot()