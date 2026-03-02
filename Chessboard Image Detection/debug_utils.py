import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Display each square
def displaySquares(squares):
    # Create 8x8 figure
    fig, axes = plt.subplots(8, 8, figsize=(7, 7))
    
    # Chessboard labels for clarity
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    
    for i in range(8):
        for j in range(8):
            ax = axes[i, j]
            img = squares[i][j].image
            
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Check if image exists
            if img is None or img.size == 0:
                print(f"Empty image at {i},{j}")
                print(img.shape)
            else:
                ax.imshow(img)
                
            # Display cropped square
            ax.imshow(img)

            # Check which square is occupied and display using coloured borders
            occupied = squares[i][j].isOccupied()
            color = 'red' if occupied else 'green'

            # Place all images on figure
            rect = patches.Rectangle(
                (0, 0),                       # Top-left corner (x, y)
                squares[i][j].image.shape[1], # Width
                squares[i][j].image.shape[0], # Height
                linewidth=5,
                edgecolor=color,
                facecolor='none'
            )
            ax.add_patch(rect)
            
            # Add labels like 'a8', 'b8', etc.
            ax.set_title(f"{files[j]}{ranks[i]}", fontsize=8)
            
            # Hide axes
            ax.axis('off')

    plt.tight_layout()
    plt.show()
