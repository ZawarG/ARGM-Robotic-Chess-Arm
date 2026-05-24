import numpy as np
import src.vision.utils as utils
from src.vision.chess_square import ChessSquare

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

        light_vals = []
        dark_vals = []

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
                    _, avg_brightness = utils.getSquareBrightness(square_img)
                    if square_object.is_light_square:
                        light_vals.append(avg_brightness)
                    else:
                        dark_vals.append(avg_brightness)

        # Calculate base profiles
        self.light_profile = {'mean': np.mean(light_vals), 'std': max(np.std(light_vals), 2.0)}
        self.dark_profile = {'mean': np.mean(dark_vals), 'std': max(np.std(dark_vals), 2.0)}

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