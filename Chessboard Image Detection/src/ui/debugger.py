import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from src.vision import utils

#  (\(\
# ( -.-)
# o_(")(")
# This file displays all 64 squares of the chess board in a 8x8 grid, used for debugging
# Each square is surrounded by either a red (occupied) or green (empty) border

# Draws a red (occupied) or green (empty) for each square on top of the warped image
def drawOccupancyOverlay(board_vision):
    """
    Draws the grid lines and occupancy status on the warped board image.
    
    :param img: A copy of the current warped frame (e.g., 800x800).
    :param coords: The 9x9 numpy array of grid intersection points.
    :param board_vision: Optional. Pass game.vision to dynamically show 
                         Green (Empty) or Red (Occupied) states.
    :return: The annotated image frame.
    """

    img = board_vision.warped_img
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
                    profile = board_vision.light_profile if square.is_light_square else board_vision.dark_profile
                    
                    # Call the occupancy check function from your utils/square logic
                    is_occupied = square.isOccupied(profile) 
                    
                    # BGR Colors: Red if occupied, Green if empty
                    color = (0, 0, 255) if is_occupied else (0, 255, 0)
                    
                    # Draw a solid circle at the center of the square
                    cv2.circle(img, center_pt, 8, color, -1)
                    
                    # Optional: Overlay text showing the chess notation (e.g., "e4")
                    label = square.name
                    cv2.putText(img, label, (center_x - 10, center_y + 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    return img


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
            
            # 1. Handle Image
            img = square.image
            if img is None or img.size == 0:
                ax.axis('off')
                continue
                
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            ax.imshow(img_rgb)

            # Get std
            gray, bright_val, std_val = utils.getSquareFeatures(img)

            # 2. Sync Occupancy Detection
            # We determine which profile to pass based on the square's color
            profile = light_prof if square.is_light_square else dark_prof
            
            # Call isOccupied using the synced profiles
            occupied = square.isOccupied(profile)
            color = 'red' if occupied else 'green'

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

            # Display std, bright
            ax.text(
                0.5,
                0.08,
                (
                    f"STD: {std_val:.2f}\n" 
                    f"B: {bright_val:.1f}"
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

    
    # light_std = (light_prof.get('max_std'))
    # dark_std = (dark_prof.get('max_std'))
    light_avgstd= (light_prof.get('avg_std'))
    dark_avgstd = (dark_prof.get('avg_std'))
    light_std = (light_prof.get('std_std'))
    dark_std = (dark_prof.get('std_std'))
    light_bright= (light_prof.get('avg_bright'))
    dark_bright = (dark_prof.get('avg_bright'))
    light_bstd = (light_prof.get('std_bright'))
    dark_bstd = (dark_prof.get('std_bright'))

    plt.figtext(
        0.5,
        0.02,
        (
            f"Light std min: {(light_avgstd):.2f}    |    Dark std min: {(dark_avgstd):.2f}\n"
            f"Light std max: {(light_avgstd*1.8):.2f}    |    Dark std max: {(dark_avgstd+dark_std*1.8):.2f}\n"
            # f"Light profile std: {light_std:.2f}    |    Dark profile std: {dark_std:.2f}\n"
            f"Light brightness min: {(light_bright-2*light_bstd):.2f}    |    Dark brightness min: {(dark_bright-dark_bstd):.2f}\n"
            f"Light brightness max: {(light_bright+2*light_bstd):.2f}    |    Dark brightness max: {(dark_bright+dark_bstd):.2f}"
        ),
        ha='center',
        fontsize=12
    )

    plt.tight_layout(rect=[0, 0.12, 1, 1])
    plt.show()

