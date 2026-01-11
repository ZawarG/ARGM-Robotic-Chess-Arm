from chess_square import ChessSquare
import chess, chess.engine
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
        self.human_colour = chess.BLACK

        # chess engine
        self.engine = chess.engine.SimpleEngine.popen_uci("stockfish")

        # used to decide if a move has been made before detecting moves
        self.board_changed = False
        self.stable_frames = 0
        self.stable_thresh = 30 # 30 frames ~= 1 second

        # for move determination
        self.ignore_vision = False # ignore motion detection during robot's turn
        self.robot_move_pending = False

    # this is what the main function will run in its while loop
    def update(self, img):
        self.updateSquares(img)

        # human move
        move = self.checkIfStable()
        if move:
            print("human played:", move)
            self.robot_move_pending = True
            return
        
        # robot move
        if self.board.turn != self.human_colour:
            self.playRobotMove()
            self.robot_move_pending = False
            return
    
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
        
        possible_moves = []
        
        for move in self.board.legal_moves:
            from_row, from_col = 7 - (move.from_square // 8), move.from_square % 8
            to_row, to_col = 7 - (move.to_square // 8), move.to_square % 8
            
            observed_squares = set(changed)
            move_squares = {(from_row, from_col), (to_row, to_col)}

            # en passent
            if move.is_en_passant():
                cap_row = from_row
                cap_col = to_col
                move_squares.add((cap_row, cap_col))
            # castling
            if move.is_castling():
                if move.to_square > move.from_square:  # kingside
                    move_squares.add((from_row, from_col + 3))  # rook origin
                    move_squares.add((from_row, from_col + 1))  # rook destination
                else:  # queenside
                    move_squares.add((from_row, from_col - 4))  # rook origin
                    move_squares.add((from_row, from_col - 1))  # rook destination
            # could be promotion
            if observed_squares == move_squares:
                possible_moves.append(move)
        
        if possible_moves:
            move_to_play = possible_moves[0]  # if multiple, pick first legal match
            self.board.push(move_to_play)
            self.prev_occ = [row.copy() for row in self.curr_occ]
            return move_to_play
    
    # check if board has been stable long enough to consider a move complete
    def checkIfStable(self):
        if self.ignore_vision:
            return None
        if self.board.turn != self.human_colour:
            return None

        changed = self.detectChanges()

        if changed: # board is currently changing
            self.board_changed = True
            self.stable_frames = 0 # there have been no frames yet where the board is stable at this position
            return None
        
        if self.board_changed:
            # board is not changing
            self.stable_frames += 1
            if self.board_changed:  # previously detected a change
                if self.stable_frames >= self.stable_thresh:
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

    # robot decides what to play from stockfish engine
    def playRobotMove(self):
        if self.ignore_vision:
            return
        
        self.ignore_vision = True

        # ask engine for best move
        result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
        move = result.move

        print("Robot played:", move)

        
        self.board.push(move) # update chess state

        # robot.execute(move) # physically move robot

        # After robot finishes moving:
        self.endRobotMove()

    def endRobotMove(self):
        self.prev_occ = [[sq.isOccupied() for sq in row] for row in self.squares]
        self.curr_occ = [row.copy() for row in self.prev_occ]
        self.board_changed = False
        self.stable_frames = 0
        self.ignore_vision = False