class ChessSquare: # responsibile for vision aspect
    def __init__(self, image, row, col):
        self.image = image
        self.row = row
        self.col = col

        # initialize piece info
        self.occupied = False # from image analysis

        # frame history
        self.history = []
        self.history_size = 5
        
    def cropCenter(self, border_ratio = 0.2): # avoids error in isOccupied since colours from adjacent squares may be showing
        height, width = self.image.shape[:2]
        b_height = int(height * border_ratio)
        b_width = int(width * border_ratio)
        return self.image[b_height:height-b_height, b_width:width-b_width]

    def isOccupied(self):
        center = self.cropCenter()

        # standard deviation threshold to detect if square is occupied
        current_occ = center.std() > 20

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