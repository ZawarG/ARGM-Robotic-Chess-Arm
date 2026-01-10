from chess_square import ChessSquare
import chess
import time

class ChessBoard:
    def __init__(self, coord):
        self.coord = coord # list of all positions of each square in board

        # vision layer
        self.squares = [[None for _ in range(8)] for _ in range(8)] # create list of chesssquare objects storing images
        self.prev_occ = [[False for _ in range(8)] for _ in range(8)] # previous move's square occupancy
        self.curr_occ = [[False for _ in range(8)] for _ in range(8)] # current move's square occupancy
        self.initOcc()

        # chess board
        self.board = chess.Board()

        # used to decide if a move has been made before detecting moves
        self.board_changed = False
        self.stable_frames = 0
        self.stable_thresh = 30 # 30 frames ~= 1 second
    
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

        self.curr_occ = curr_occ # update current, but do not update previous until sure that the next move has been made
        return changed
    
    # detect FSM changes and push to python-chess
    def detectMove(self):
        changed = self.detectChanges()

        if len(changed) == 0: # no move
            return None
        elif len(changed) == 2: # regular move
            sq1, sq2 = changed

            if self.prev_occ[sq1[0]][sq1[1]]: #if it is true, then this piece is the destination (previously full, now empty)
                origin, dest, = sq1, sq2
            else:
                origin, dest = sq2, sq1
        elif len(changed) == 4: # castling
            origin, dest = None, None
            for sq in changed:
                if self.prev_occ[sq[0]][sq[1]] and not self.curr_occ[sq[0]][sq[1]]:
                    origin = sq
                if not self.prev_occ[sq[0]][sq[1]] and self.curr_occ[sq[0]][sq[1]]:
                    dest = sq
        elif len(changed) == 3: # en passant
            # not sure
            # also not sure how to detect pawn upgrades with what we are currently working with
            print("Complex or unrecognizable move")
            return None
        else:
            print("Complex or unrecognizable move")
            return None

        # convert to uci format for python-chess to update
        uciMove = self.toUCI(*origin) + self.toUCI(*dest)
        if uciMove in [m.uci() for m in self.board.legal_moves]:
            self.board.push_uci(uciMove)
            self.prev_occ = [row.copy() for row in self.curr_occ] # update prev_occ now that board is settled and logic is worked through
        else:
            print("Illegal or unrecognized move")
    
    # check if board has been stable long enough to consider a move complete
    def checkIfStable(self):
        changed = self.detectChanges()

        if changed: # board is currently changing
            self.board_changed = True
            self.stable_frames = 0 # there have been no frames yet where the board is stable at this position
        else:
            # board is not changing
            self.stable_frames += 1
            if self.board_changed:  # previously detected a change
                if self.stable_frames >= 30:
                    self.board_changed = False # board has been stable long enough
                    return self.detectMove() # detect and execute move
        return None
    
    # convert (row, col) to file-rank
    def toUCI(self, row, col):
        file = "abcdefgh"[col]
        rank = str(8-row)
        return file + rank

    # ------ this should not be needed, but i'm keeping it while working with a static image
    # apply initial chess state
    def initOcc(self):
        for row in [0,1,6,7]:
            for col in range(8):
                self.prev_occ[row][col] = True
                self.curr_occ[row][col] = True