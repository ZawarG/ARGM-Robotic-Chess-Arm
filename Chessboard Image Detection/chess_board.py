from chess_square import ChessSquare
import chess

class ChessBoard:
    def __init__(self, coord):
        self.coord = coord # list of all positions of each square in board

        # vision layer
        self.squares = [[None for _ in range(8)] for _ in range(8)] # create list of chesssquare objects storing images
        self.prev_occ = [[False for _ in range(8)] for _ in range(8)] # previous move's square occupancy
        self.initPrevOcc()

        # chess board
        self.board = chess.Board()
    
    # update images for each square
    def updateSquares(self, img):
        for row in range(8):
            for col in range(8):
                top_left = self.coord[row, col]
                bottom_right = self.coord[row+1, col+1]

                cropped_square = img[int(top_left[1]):int(bottom_right[1]), int(top_left[0]):int(bottom_right[0])]
                
                if self.squares[row][col] is None:
                    square_object = ChessSquare(cropped_square, row, col)
                    self.squares[row][col] = square_object
                else:
                    self.squares[row][col].image = cropped_square

    # check if images (squares) are occupied with a piece or not, and return any changes made to the chess piece locations
    def detectChanges(self):
        curr_occ = [[self.squares[row][col].isOccupied() for col in range(8)] for row in range(8)]
        changed = []
        
        for row in range(8):
            for col in range(8):
                if curr_occ[row][col] != self.prev_occ[row][col]:
                    changed.append((row,col))

        self.prev_occ = curr_occ
        return changed
    
    def toUCI(self, row, col):
        file = "abcdefgh"[col]
        rank = str(8-row)
        return file + rank

    # apply initial chess state
    def initPrevOcc(self):
        for row in [0,1,6,7]:
            for col in range(8):
                self.prev_occ[row][col] = True