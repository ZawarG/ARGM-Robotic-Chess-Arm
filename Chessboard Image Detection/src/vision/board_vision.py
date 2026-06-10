import numpy as np
import src.vision.utils as utils
from src.vision.chess_square import ChessSquare

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

        self.occupancy_buffer = []
        self.M = None

        self.warped_img = None
        self.curr_frame_bright = None

    def getSquare(self, img, row, col):
        top_left = self.coord[row, col] # top left coordinate of square
        bottom_right = self.coord[row+1,col+1] # bottom right coordinate of square
        isolated_square = img[
            int(top_left[1]):int(bottom_right[1]), 
            int(top_left[0]):int(bottom_right[0])
        ]
        return isolated_square

    def initializeBoard(self, img, M):
        self.warped_img = img
        self.M = M

        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = [8, 7, 6, 5, 4, 3, 2, 1]

        light_bright = []
        dark_bright = []
        light_std = []
        dark_std = []
        light_squares = []
        dark_squares = []
        light_contour_area = []
        dark_contour_area = []

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
                    crop_img, avg_brightness, std = utils.getSquareFeatures(square_img)

                    if square_object.is_light_square:
                        light_bright.append(avg_brightness)
                        light_std.append(std)
                        light_squares.append(crop_img)
                    else:
                        dark_bright.append(avg_brightness)
                        dark_std.append(std)
                        dark_squares.append(crop_img)

        # Convert lists to numpy arrays (prevents calculation error)
        light_bright = np.array(light_bright)
        dark_bright = np.array(dark_bright)
        light_std = np.array(light_std)
        dark_std = np.array(dark_std)
        light_squares = np.array(light_squares)
        dark_squares = np.array(dark_squares)
        light_contour_area = np.array(light_contour_area)
        dark_contour_area = np.array(dark_contour_area)

        # Calculate base profiles
        self.light_profile = {
            'avg_bright': np.mean(light_bright),
            'std_bright': max(np.std(light_bright), 1.0),
            'avg_std': np.mean(light_std),
            'std_std': max(np.std(light_std), 1.0),
            'avg_sq': np.mean(light_squares, axis=0).astype(np.uint8),
            'std_sq': np.maximum(np.std(light_squares, axis=0), 1e-7),
            # 'avg_contour_area': np.mean(),
            # 'std_contour_area': max(np.std(), 0.1)
            'start_frame_bright': np.mean(img)
        }
        self.dark_profile = {
            'avg_bright': np.mean(dark_bright), 
            'std_bright': max(np.std(dark_bright), 1.0),
            'avg_std': np.mean(dark_std),
            'std_std': max(np.std(dark_std), 1.0),
            'avg_sq': np.mean(dark_squares, axis=0).astype(np.uint8),
            'std_sq': np.maximum(np.std(dark_squares, axis=0), 1e-7),
            # 'avg_contour_area': np.mean(),
            # 'std_contour_area': max(np.std(), 0.1)
            'start_frame_bright': np.mean(img)
        }

    # Takes a raw unwarped video frame, crops and warps it, and extracts the squares
    def updateFrame(self, raw_img):
        img_small = utils.makeImageSmall(raw_img)
        img = utils.warpFrame(img_small, self.M)
        self.warped_img = img

        self.curr_frame_bright = np.mean(img)

        for row in range(8):
            for col in range(8):
                # Retrieve image
                top_left = self.coord[row, col]
                bottom_right = self.coord[row+1, col+1]
                cropped_square = img[int(top_left[1]):int(bottom_right[1]), int(top_left[0]):int(bottom_right[0])]
                
                # Update image
                self.squares[row][col].image = cropped_square

    # Retrieves current frame occupancy, appends to history, returns mode of occupancy every 10 frames
    # Otherwise, returns None
    def getStabilizedOccupancy(self, STABILITY_THRESHOLD=15):
        # current_frame_occ = [[False for _ in range(8)] for _ in range(8)]
        # for row in range(8):
        #     for col in range(8):
        #         square = self.squares[row][col]
        #         profile = self.light_profile if square.is_light_square else self.dark_profile
        #         current_frame_occ[row][col] = square.isOccupied(profile)

        current_frame_occ = self.getObservedOccupancy() # Retrieve occupancy for current frame

        self.occupancy_buffer.append(current_frame_occ) # Push to buffer

        if len(self.occupancy_buffer) < STABILITY_THRESHOLD: # We have not reached the required stable frames yet
            return None
        
        # Find mode
        array = np.array(self.occupancy_buffer)
        sum_matrix = np.sum(array, axis = 0)
        mode_matrix = (sum_matrix >= 5).tolist()

        # Flush buffer
        self.occupancy_buffer = []

        return mode_matrix

    # Retrieves current frame occupancy
    def getObservedOccupancy(self):
        observed = [[False for _ in range(8)] for _ in range(8)]
        for row in range(8):
            for col in range(8):
                square = self.squares[row][col]
                profile = self.light_profile if square.is_light_square else self.dark_profile
                observed[row][col] = square.isOccupied(profile, self.curr_frame_bright)
        
        return observed