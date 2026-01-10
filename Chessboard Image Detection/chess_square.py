import cv2
import numpy as np

class ChessSquare: # responsibile for vision aspect
    def __init__(self, image, row, col):
        self.image = image
        self.row = row
        self.col = col

        # initialize piece info
        self.occupied = False # from image analysis
        
    def cropCenter(self, border_ratio = 0.2): # avoids error in isOccupied since colours from adjacent squares may be showing
        height, width = self.image.shape
        b_height = int(height * border_ratio)
        b_width = int(width * border_ratio)
        return self.image[b_height:height-b_height, b_width:width-b_width]

    def isOccupied(self):
        center = self.cropCenter()

        # # check for unique colours, if more than one, then there exists a piece
        # thresh_ratio = 0.1
        # unique_colours = np.unique(center)
        # return len(unique_colours) > 1
    
        # standard deviation can look past the case where there is some noise
        return center.std() > 15