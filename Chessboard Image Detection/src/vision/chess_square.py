import src.vision.utils as utils

#  (\(\
# ( -.-)
# o_(")(")
# Each square in the chess board is its own object.
# This class handles the vision aspect of the game. 
# Specifically, each square's occupancy is checked

class ChessSquare: # responsibile for vision aspect
    def __init__(self, image, row, col, file, rank):
        self.image = image

        self.coord = (row, col)
        file_int = ord(file) - 96
        self.name = f"{file}{rank}"
        self.is_light_square = (file_int+rank) % 2 # 0 for dark, 1 for light

        # initialize piece info
        self.occupied = False # from image analysis

    def setReference(self, value):
        self.base_profile = value
        
    def isOccupied(self, profile):
        return utils.checkOccupancy(self.image, self.is_light_square, profile)