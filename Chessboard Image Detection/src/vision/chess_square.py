import src.vision.utils as utils

"""
Each square in the chess board is its own object.
This class handles the vision aspect of the game. Specifically, each square's occupancy is checked
"""
class ChessSquare: # responsibile for vision aspect
    def __init__(self, image, row, col, file, rank):
        self.image = image

        file_int = ord(file) - 96
        self.coord = f"{file}{rank}"
        self.is_light_square = (file_int+rank) % 2 # 0 for dark, 1 for light

        # initialize piece info
        self.occupied = False # from image analysis

        # frame history
        self.history = []
        self.history_size = 5

    def setReference(self, value):
        self.base_profile = value
        
    def isOccupied(self, profile):
        current_occ = utils.checkOccupancy(self.image, self.is_light_square, profile)

        # add to history
        self.history.append(current_occ)

        # keep only last 5 frames
        if len(self.history) > self.history_size:
            self.history.pop(0)

        # # take value that occurs more
        # if len(self.history) == self.history_size:
        #     true_count = sum(self.history) # true = 1, false = 0
        #     false_count = self.history_size - true_count
        #     self.occupied = true_count > false_count # majority wins
        # else:
        #     # not enough history yet
        #     current_occ = self.occupied

        # for testing
        if len(self.history) < self.history_size:
            self.occupied = current_occ
        else:
            true_count = sum(self.history)
            self.occupied = true_count > (self.history_size // 2)

        return self.occupied