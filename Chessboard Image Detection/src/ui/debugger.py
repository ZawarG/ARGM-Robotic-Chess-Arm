import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from src.vision import utils

#  (\(\
# ( -.-)
# o_(")(")
# This file displays all 64 squares of the chess board in a 8x8 grid, used for debugging
# Each square is surrounded by either a red (occupied) or green (empty) border

# Display each square
def displaySquares(vision):
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
            ax.set_title(square.coord, fontsize=9, color='blue')
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
            f"Light std min: {(light_avgstd-light_std):.2f}    |    Dark std min: {(dark_avgstd-dark_std):.2f}\n"
            f"Light std max: {(light_avgstd+light_std):.2f}    |    Dark std max: {(dark_avgstd+dark_std):.2f}\n"
            # f"Light profile std: {light_std:.2f}    |    Dark profile std: {dark_std:.2f}\n"
            f"Light brightness min: {(light_bright-2*light_bstd):.2f}    |    Dark brightness min: {(dark_bright-dark_bstd):.2f}\n"
            f"Light brightness max: {(light_bright+2*light_bstd):.2f}    |    Dark brightness max: {(dark_bright+dark_bstd):.2f}"
        ),
        ha='center',
        fontsize=12
    )

    plt.tight_layout(rect=[0, 0.12, 1, 1])
    plt.show()

