import numpy as np
import src.vision.utils as utils
from src.vision.chess_square import ChessSquare

#  (\(\
# ( -.-)
# o_(")(")
# This class holds the chess board's visual state.
# It contains the images for each chess square and features related to them.

class BoardVision:
    def __init__(self, coord):
        self.coord = coord # Visual positions of each square in board
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        self.light_profile = None
        self.dark_profile = None
        self.occupancy_buffer = []
        self.M = None
        self.warped_img = None
        self.bot_is_white = None
        self.white_piece_ref = None  # Reference brightness for a white piece
        self.black_piece_ref = None  # Reference brightness for a black piece

    def _getSquareImage(self, img, row, col):
        top_left = self.coord[row, col] # top left coordinate of square
        bottom_right = self.coord[row+1,col+1] # bottom right coordinate of square
        isolated_square = img[
            int(top_left[1]):int(bottom_right[1]), 
            int(top_left[0]):int(bottom_right[0])
        ]

        hsv = utils.adjustSquare(isolated_square)
        return hsv

    def initializeBoard(self, img, M):
        self.warped_img, self.M = img, M
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = [8, 7, 6, 5, 4, 3, 2, 1]

        # Extract every square once -- for orientation and profiles
        hsv_img = [[self._getSquareImage(img, r, c) for c in range(8)] for r in range(8)]

        # Determine orientation
        robot_square_hsv = np.mean([np.mean(hsv_img[r][c]) for r in (6, 7) for c in range(8)])
        opponent_square_hsv = np.mean([np.mean(hsv_img[r][c]) for r in (0, 1) for c in range(8)])
        self.bot_is_white = robot_square_hsv > opponent_square_hsv

        # Build profiles
        light_squares, dark_squares, square_means = [], [], []

        for row in range(8):
            for col in range(8):
                # Store chess coordinate
                file = files[col]
                rank = ranks[row] if self.bot_is_white else ranks[7-row]

                # Store chess square object
                square_object = ChessSquare(hsv_img[row][col], row, col, file, rank)
                self.squares[row][col] = square_object

                # Calculate average hsv values
                square_means.append(np.mean(hsv_img[row][col], axis=(0, 1)))

                # Middle rows are empty -> boolean occupancy + learn empty light/dark colour
                if row in (2, 3, 4, 5):
                    square_object.setOccupancy(False)
                    if square_object.is_light_square:
                        light_squares.append(hsv_img[row][col])
                    else:
                        dark_squares.append(hsv_img[row][col])

        # Convert lists to numpy arrays (prevents calculation error)
        light_squares = np.array(light_squares)
        dark_squares = np.array(dark_squares)
        square_means = np.array(square_means)

        # Calculate base profiles for empty squares
        self.light_profile = {
            'avg_sq': np.mean(light_squares, axis=0).astype(np.float32),
            'std_sq': np.maximum(np.std(light_squares, axis=0), 1e-7),
            'avg_hsv': np.median(square_means),
            'curr_hsv': np.median(square_means)
        }
        self.dark_profile = {
            'avg_sq': np.mean(dark_squares, axis=0).astype(np.float32),
            'std_sq': np.maximum(np.std(dark_squares, axis=0), 1e-7),
            'avg_hsv': np.median(square_means),
            'curr_hsv': np.median(square_means)
        }

        # Reference brightness for piece-colour classification
        if self.bot_is_white:
            self.white_piece_ref, self.black_piece_ref = robot_square_hsv, opponent_square_hsv
        else:
            self.white_piece_ref, self.black_piece_ref = opponent_square_hsv, robot_square_hsv

    # Classify piece colour on an occupied square by brightness, against white/black references learned at calibration
    # Same lighting offset used for occupancy is applied so fixed references stay valid as light drifts
    def classifyColour(self, hsv_img):
        offset = self.light_profile['curr_hsv'] - self.light_profile['avg_hsv']
        brightness = np.mean(hsv_img) - offset
        if abs(brightness - self.white_piece_ref) <= abs(brightness - self.black_piece_ref):
            return "White"
        return "Black"

    # Warps a raw frame (same pipeline as updateFrame) and builds the light/dark reference profiles from it. Use this to calibrate from a live/populated frame.
    def calibrate(self, raw_img, M):
        img_small = utils.makeImageSmall(raw_img)
        warped = utils.warpFrame(img_small, M)
        self.initializeBoard(warped, M)
        return self.bot_is_white

    # Takes a raw unwarped video frame, crops and warps it, and extracts the squares
    def updateFrame(self, raw_img):
        img_small = utils.makeImageSmall(raw_img)
        img = utils.warpFrame(img_small, self.M)
        self.warped_img = img

        square_means = []
        square_data = []

        for row in range(8):
            for col in range(8):
                square = self.squares[row][col]
                hsv_img = self._getSquareImage(img, row, col)

                square_data.append((square, hsv_img))
                square_means.append(np.mean(hsv_img, axis=(0, 1)))

        square_means = np.array(square_means)
        self.light_profile['curr_hsv'] = np.median(square_means)
        self.dark_profile['curr_hsv'] = np.median(square_means)

        for square, square_img in square_data:
            profile = self.light_profile if square.is_light_square else self.dark_profile
            square.updateOccupancy(square_img, profile)

            # Observed piece colour
            if square.getOccupancy():
                square.setObservedSide(self.classifyColour(square_img))
            else:
                square.setObservedSide(None)

    # Retrieves current frame occupancy, appends to history, returns mode of occupancy every 10 frames
    # Otherwise, returns None
    def getStabilizedOccupancy(self, STABILITY_THRESHOLD=17):
        current_frame_occ = self.getObservedOccupancy() # Retrieve occupancy for current frame

        self.occupancy_buffer.append(current_frame_occ) # Push to buffer

        if len(self.occupancy_buffer) < STABILITY_THRESHOLD: # We have not reached the required stable frames yet
            return None
        
        # Find mode
        array = np.array(self.occupancy_buffer)
        sum_matrix = np.sum(array, axis = 0)
        mode_matrix = (sum_matrix >= STABILITY_THRESHOLD//2).tolist()

        # Flush buffer
        self.occupancy_buffer = []

        return mode_matrix

    # Retrieves current frame occupancy
    def getObservedOccupancy(self):
        observed = [[False for _ in range(8)] for _ in range(8)]
        for row in range(8):
            for col in range(8):
                square = self.squares[row][col]
                observed[row][col] = square.getOccupancy()
        
        return observed