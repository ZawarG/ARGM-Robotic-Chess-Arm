import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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
            
            # 4. Use internal naming (e.g., 'a8', 'h1')
            ax.set_title(square.coord, fontsize=9, color='blue')
            ax.axis('off')

    plt.tight_layout()
    plt.show()

