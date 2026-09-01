import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
import src.vision.utils as utils

#  (\(\
# ( -.-)
# o_(")(")
# This file contains calibration functions, used to either manually determine the location of the board or the player colour

def adjustImageManually(img):
    window_name = "Board Calibration"
    cv2.namedWindow(window_name)

    # Window dimensions
    WIN_W = 1000
    WIN_H = 800
    HEADER_H = 100  # Fixed space for two lines of text

    # Calculate scale to fit image in window
    available_h = WIN_H - HEADER_H
    scale = min(WIN_W / img.shape[1], available_h / img.shape[0])

    # Resize image for display
    new_w = int(img.shape[1] * scale)
    new_h = int(img.shape[0] * scale)
    img_display = cv2.resize(img, (new_w, new_h))

    points = []
    selected_id = -1

    def mouse_callback(event, x, y, flags, params):
        nonlocal points, selected_id

        if event == cv2.EVENT_LBUTTONDOWN:
            # Check if clicking near an existing point to edit it
            for i, p in enumerate(points):
                if np.linalg.norm(np.array([x, y]) - np.array(p)) < 15:
                    selected_id = i
                    return
            
            # If not editing and we have fewer than 4 points, add a new one
            if len(points) < 4:
                points.append([x, y])

        elif event == cv2.EVENT_MOUSEMOVE:
            # Move selected point
            if selected_id != -1:
                points[selected_id] = [x, y]

        elif event == cv2.EVENT_LBUTTONUP:
            selected_id = -1

        elif event == cv2.EVENT_RBUTTONDOWN:
            # Right click to delete closest point
            for i, p in enumerate(points):
                if np.linalg.norm(np.array([x, y]) - np.array(p)) < 15:
                    points.pop(i)
                    break

    cv2.setMouseCallback(window_name, mouse_callback)

    while True:
        canvas = np.zeros((WIN_H, WIN_W, 3), dtype=np.uint8)

        # Center image in canvas
        x_offset = (WIN_W - new_w) // 2
        canvas[HEADER_H : HEADER_H + new_h, x_offset : x_offset + new_w] = img_display

        # Instructions text
        line1 = "Click 4 corners | Drag to adjust | Right click to remove"
        line2 = "ENTER: Confirm | Q: Abort"

        for i, text in enumerate([line1, line2]):
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            tx = 20
            ty = 40 + (i * 35) # Spacing between lines
            cv2.putText(canvas, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        # Draw points
        for i, p in enumerate(points):
            draw_x = int(p[0])
            draw_y = int(p[1])
            cv2.circle(canvas, (draw_x, draw_y), 6, (0, 255, 0), -1)

        # Draw a polygon if we have 4 points to show the current board area
        if len(points) == 4:
            pts_array = utils.orderPoints(np.array(points))
            cv2.polylines(canvas, [pts_array.astype(np.int32)], True, (0, 255, 255), 2)

        cv2.imshow(window_name, canvas)

        key = cv2.waitKey(1) & 0xFF
        if key == 13: # Enter Key
            if len(points) == 4:
                break
            else:
                print("Please select exactly 4 points before pressing Enter.")
        elif key == ord('q'): # Quit/Abort
            cv2.destroyWindow(window_name)
            return False, None
        
    cv2.destroyWindow(window_name)
    
    # Sort and adjust points before returning
    final_pts = utils.orderPoints(np.array(points)) 
    final_pts[:, 1] -= HEADER_H
    final_pts[:, 0] -= x_offset

    return True, final_pts/scale

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