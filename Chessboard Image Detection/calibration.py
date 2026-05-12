import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
from utils import preprocessImage, detectSquares

def filterImage(img, sat=0.1, con=0.1, bright=0, bp=0, wp=255, shadow=0.1):
    # Saturation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v, = cv2.split(hsv)
    s = np.clip(s.astype(np.float32) * sat, 0, 255).astype(np.uint8)
    img = cv2.cvtColor(cv2.merge([h, s, v]), cv2.COLOR_HSV2BGR)

    # LUT
    i = np.arange(256, dtype=np.float32)

    # Contrast, brightness
    lut_base = i * con + bright

    # Shadow
    diff = max(float(wp - bp), 1.0)
    inv_gamma = 1.0 / max(shadow, 0.01)
    
    table_vals = np.power(np.clip((lut_base - bp) / diff, 0, 1), inv_gamma) * 255
    table = np.clip(table_vals, 0, 255).astype("uint8")
    return cv2.LUT(img, table)

def getTrackbarParams(window):
    return [
        cv2.getTrackbarPos("Saturation x10", window) / 10.0,
        cv2.getTrackbarPos("Contrast x10", window) / 10.0,
        cv2.getTrackbarPos("Brightness", window) - 100,
        cv2.getTrackbarPos("Black Point", window),
        cv2.getTrackbarPos("White Point", window),
        max(cv2.getTrackbarPos("Shadow x10", window), 1) / 10.0,
        cv2.getTrackbarPos("Border Limit", window)
    ]

def adjustImageManually(img):
    window = "Chessboard View"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)

    # Initial neutral values
    cv2.createTrackbar("Saturation x10", window, 10, 50, lambda x: None)
    cv2.createTrackbar("Contrast x10", window, 10, 30, lambda x: None)
    cv2.createTrackbar("Brightness", window, 100, 200, lambda x: None)
    cv2.createTrackbar("Black Point", window, 0, 255, lambda x: None)
    cv2.createTrackbar("White Point", window, 255, 255, lambda x: None)
    cv2.createTrackbar("Shadow x10", window, 10, 50, lambda x: None)
    cv2.createTrackbar("Border Limit", window, 7, 50, lambda x: None)

    corners, mask, ret = None, None, False
    prev_params = []

    while True:
        curr_params = getTrackbarParams(window)
        
        # Only re-process if sliders moved
        if curr_params != prev_params:
            s, c, br, bp, wp, sh, bdr = curr_params

            # Auto-correct BP/WP overlap
            if bp >= wp: 
                bp = wp - 1
                cv2.setTrackbarPos("Black Point", window, bp)

            adjusted = filterImage(img, s, c, br, bp, wp, sh)
            mask = preprocessImage(adjusted, border_high=bdr, testing=True)
            
            # Detect on the mask
            board_detected, corners = detectSquares(mask)
            prev_params = curr_params
            
        # UI Composition
        disp_img = adjusted.copy()
        if ret: cv2.drawChessboardCorners(disp_img, (7, 7), corners, ret)
        
        # Create a side-by-side view (Original/Adjusted | Mask)
        disp_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        divider = np.zeros((img.shape[0], 5, 3), dtype=np.uint8) + 180
        stacked = np.hstack((disp_img, divider, disp_mask))
        
        cv2.imshow(window, stacked)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 13 and ret: # ENTER
            # Upscale corners to original image size
            return board_detected, corners, mask
        elif key == 27: # ESC
            break

    cv2.destroyAllWindows()
    return None, None

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