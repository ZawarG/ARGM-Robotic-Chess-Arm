class ChessSquare:
    def __init__(self, image, row, col):
        self.image = image
        self.row = row
        self.col = col

        # initialize piece info
        self.occupied = False
        self.piece = None
        self.color = None # 1 for them, 0 for us

    def getFENValue(self):
        if not self.occupied:
            return 0
        
        if self.colour == 0:
            return self.piece.upper()
        else:
            return self.piece