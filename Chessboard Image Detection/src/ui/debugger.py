import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from src.vision import occupancy
from src.vision import geometry
import numpy as np

#  (\(\
# ( -.-)
# o_(")(")
# This file displays all 64 squares of the chess board in a 8x8 grid, used for debugging
# Each square is surrounded by either a red (occupied) or green (empty) border

# Shows raw frame with four detected outer corners numbered.
# Used during calibration to confirm board corners were found correctly
def showOuterCorners(img, source_pts):
    debug = img.copy()

    for i, p in enumerate(source_pts.astype(int)):
        cv2.circle(debug, tuple(p), 8, (0, 0, 255), -1)
        cv2.putText(debug, str(i), tuple(p), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255, 0, 0), 2)

    cv2.imshow("Outer corners", debug)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Shows 7x7 inner corners found by findChessboardCorners.
# Used during calibration to confirm chessboard grid was detected
def showDetectedCorners(img, corners, board_detected):
    fnl = cv2.drawChessboardCorners(img, (7, 7), corners, board_detected)
    cv2.imshow("Chessboard with Corners", fnl)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Setup-phase overlay: warps the raw frame and prompts the user to place pieces.
# Shown until the game starts so pieces can be positioned on the live feed.
def drawSetupOverlay(img, M):
    warped = geometry.warpFrame(geometry.makeImageSmall(img), M)
    live_display = warped.copy()
    cv2.putText(live_display, "Set up pieces, then press S to start",
                (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    return live_display

# Promotion prompt drawn on top of the occupancy overlay: vision saw a pawn
# promote but can't tell into what, so the user picks the piece.
def drawPromotionOverlay(live_display, game):
    names = {'q': 'Queen', 'r': 'Rook', 'b': 'Bishop', 'n': 'Knight'}
    sel = game.promotion_selection
    cv2.putText(live_display, "Promotion: [Q]ueen [R]ook [B]ishop k[N]ight",
                (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(live_display, f"Selected: {names[sel]}  -  press ENTER to confirm",
                (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return live_display

# Draws a red (occupied) or green (empty) for each square on top of the warped image
def drawOccupancyOverlay(board_vision):
    img = board_vision.warped_img.copy()
    cv2.imshow('img', img)
    coords = board_vision.coord

    # 1. Draw the 9x9 Grid Lines
    # Loop through rows and columns to connect the intersection points
    for i in range(9):
        # Draw horizontal lines: connect (row i, col 0) to (row i, col 8)
        pt_start_h = tuple(coords[i, 0].astype(int))
        pt_end_h = tuple(coords[i, 8].astype(int))
        cv2.line(img, pt_start_h, pt_end_h, (255, 0, 0), 2) # Blue lines

        # Draw vertical lines: connect (row 0, col i) to (row 8, col i)
        pt_start_v = tuple(coords[0, i].astype(int))
        pt_end_v = tuple(coords[8, i].astype(int))
        cv2.line(img, pt_start_v, pt_end_v, (255, 0, 0), 2) # Blue lines

    # 2. Draw Occupancy Status Indicators (If vision data is provided)
    if board_vision is not None:
        for row in range(8):
            for col in range(8):
                # Get corner coordinates of the current square
                top_left = coords[row, col]
                bottom_right = coords[row + 1, col + 1]
                
                # Calculate the center point of the square to place our indicator
                center_x = int((top_left[0] + bottom_right[0]) / 2)
                center_y = int((top_left[1] + bottom_right[1]) / 2)
                center_pt = (center_x, center_y)

                # Check if the square object exists and see if it's occupied
                square = board_vision.squares[row][col]
                if square is not None:
                    # Call the occupancy check function from your utils/square logic
                    is_occupied = square.getOccupancy() 

                    profile = board_vision.light_profile if square.is_light_square else board_vision.dark_profile
                    z_euclidean = occupancy.computeFillZ(square.image, profile)

                    fill = occupancy.detectContourArea(z_euclidean, None, show=False)
                    
                    # BGR Colors: Red if occupied, Green if empty
                    color = (0, 0, 255) if is_occupied else (0, 255, 0)
                    
                    # Draw a solid circle at the center of the square
                    cv2.circle(img, center_pt, 8, color, -1)
                    
                    # Overlay name, occupancy fill, and image-subtraction diff
                    # (diff vs the last confirmed board state -> spikes on captures)
                    diff = square.difference(board_vision.getLightingOffset())
                    label = f"{square.name} f{fill:.2f} d{diff:.0f}"
                    cv2.putText(img, label, (center_x - 10, center_y + 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    return img


# Display per-square image-subtraction diff for whole board.
# Each cell shows current square (piece side by side with the reference is summarised by the diff map underneath) and diff heatmap, titled with scalar score
def displayDifferences(vision, threshold=None):
    v_offset = vision.getLightingOffset()

    # Collect diff maps + scores so heatmaps can share one colour scale
    diff_maps = [[None] * 8 for _ in range(8)]
    scores = [[0.0] * 8 for _ in range(8)]
    vmax = 1.0
    for i in range(8):
        for j in range(8):
            square = vision.squares[i][j]
            if square is None:
                continue
            dmap = square.differenceMap(v_offset)
            diff_maps[i][j] = dmap
            if dmap is not None:
                scores[i][j] = float(np.mean(dmap))
                vmax = max(vmax, float(dmap.max()))

    fig, axes = plt.subplots(8, 8, figsize=(6, 6))
    fig.suptitle(f"Per-square HSV diff vs reference (offset={v_offset:.1f})", fontsize=11)

    for i in range(8):
        for j in range(8):
            ax = axes[i, j]
            ax.axis('off')
            square = vision.squares[i][j]
            dmap = diff_maps[i][j]
            if square is None or dmap is None:
                continue

            ax.imshow(dmap, cmap='inferno', vmin=0, vmax=vmax)

            score = scores[i][j]
            over = threshold is not None and score >= threshold
            ax.set_title(f"{square.name} {score:.0f}", fontsize=8,
                         color=('red' if over else 'black'))

    plt.tight_layout()
    plt.show()


# Display each square on matplotlib
def displaySquares(vision):
    stabilized_matrix = None
    for _ in range(10):
        stabilized_matrix = vision.getStabilizedOccupancy()

    # Create 8x8 figure
    fig, axes = plt.subplots(8, 8, figsize=(7, 7))
    
    light_prof = vision.light_profile
    dark_prof = vision.dark_profile

    for i in range(8):
        for j in range(8):
            ax = axes[i, j]
            square = vision.squares[i][j]
            
            img = square.image
            if img is None or img.size == 0:
                ax.axis('off')
                continue
                
            img_rgb = cv2.cvtColor(img, cv2.COLOR_HSV2RGB)
            ax.imshow(img_rgb)

            profile = light_prof if square.is_light_square else dark_prof
            occupied = square.getOccupancy()
            color = 'red' if occupied else 'green'

            z = occupancy.computeFillZ(img, profile)
            fill = occupancy.detectContourArea(z, None, show=False)

            # 3. Visual Feedback
            rect = patches.Rectangle(
                (0, 0),
                img.shape[1],
                img.shape[0],
                linewidth=4,
                edgecolor=color,
                facecolor='none'
            )
            ax.add_patch(rect)

            # Display features
            ax.text(
                0.5,
                0.08,
                (
                    f"F:{fill:.2f}"
                ),
                transform=ax.transAxes,
                ha='center',
                va='center',
                fontsize=6,
                color='white',
                bbox=dict(
                    facecolor='black',
                    alpha=0.7,
                    pad=1
                )
            )
            
            # 4. Use internal naming (e.g., 'a8', 'h1')
            ax.set_title(square.name, fontsize=9, color='blue')
            ax.axis('off')

    plt.tight_layout()
    plt.show()

