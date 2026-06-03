import numpy as np
import src.vision.utils as utils
from src.vision.chess_square import ChessSquare
import cv2

#  (\(\
# ( -.-)
# o_(")(")
# This class holds the chess board's visual state.
# It contains the images for each chess square and features related to them.

class BoardVision:
    def __init__(self, coord, bot_is_white):
        self.coord = coord # Visual positions of each square in board
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        
        self.light_profile = None
        self.dark_profile = None

        self.bot_is_white = bot_is_white

    def getSquare(self, img, row, col):
        top_left = self.coord[row, col] # top left coordinate of square
        bottom_right = self.coord[row+1,col+1] # bottom right coordinate of square
        isolated_square = img[
            int(top_left[1]):int(bottom_right[1]), 
            int(top_left[0]):int(bottom_right[0])
        ]
        return isolated_square

    def initializeBoard(self, img):
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = [8, 7, 6, 5, 4, 3, 2, 1]

        light_bright = []
        dark_bright = []
        light_std = []
        dark_std = []

        for row in range(8):
            for col in range(8):
                # Store chess coordinate
                file = files[col]
                rank = ranks[row] if self.bot_is_white else ranks[7-row]

                # Retrieve chess square
                square_img = self.getSquare(img, row, col)
                square_object = ChessSquare(square_img, row, col, file, rank)
                self.squares[row][col] = square_object

                # Calculate base light/dark colour
                if row in [2, 3, 4, 5]:
                    _, avg_brightness, std = utils.getSquareFeatures(square_img)
                    if square_object.is_light_square:
                        light_bright.append(avg_brightness)
                        light_std.append(std)
                    else:
                        dark_bright.append(avg_brightness)
                        dark_std.append(std)

        # Convert lists to numpy arrays (prevents calculation error)
        light_bright = np.array(light_bright)
        dark_bright = np.array(dark_bright)
        light_std = np.array(light_std)
        dark_std = np.array(dark_std)

        # Calculate base profiles
        self.light_profile = {
            'avg_bright': np.mean(light_bright), 
            'std_bright': max(np.std(light_bright), 2.0),
            # 'max_std': max(light_std),
            'avg_std': np.mean(light_std),
            'std_std': max(np.std(light_std), 2.0)
        }
        self.dark_profile = {
            'avg_bright': np.mean(dark_bright), 
            'std_bright': max(np.std(dark_bright), 2.0),
            # 'max_std': max(dark_std),
            'avg_std': np.mean(dark_std),
            'std_std': max(np.std(dark_std), 2.0)
        }

    def updateFrame(self, img):
        for row in range(8):
            for col in range(8):
                # Retrieve image
                top_left = self.coord[row, col]
                bottom_right = self.coord[row+1, col+1]
                cropped_square = img[int(top_left[1]):int(bottom_right[1]), int(top_left[0]):int(bottom_right[0])]
                
                # Update image
                self.squares[row][col].image = cropped_square

    def getObservedOccupancy(self):
        observed = [[False for _ in range(8)] for _ in range(8)]
        for row in range(8):
            for col in range(8):
                square = self.squares[row][col]
                profile = self.light_profile if square.is_light_square else self.dark_profile
                observed[row][col] = square.isOccupied(profile)
        
        return observed