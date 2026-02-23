from chess_square import ChessSquare
from visualize import ChessVisualizer
import chess, chess.engine
from enum import Enum, auto
import serial

# Replace 'COM4' with your Arduino's port (e.g., '/dev/ttyUSB0')
# Ensure the baud rate matches the one in your Arduino code
# arduino = serial.Serial(port='COM4', baudrate=115200, timeout=.1)

class GameState(Enum):
    HUMAN_MOVING = auto()
    ROBOT_MOVING = auto()
    GAME_OVER = auto()

class ChessBoard:
    def __init__(self, coord):
        self.coord = coord # list of all positions of each square in board

        # vision layer
        self.squares = [[None for _ in range(8)] for _ in range(8)] # list of chesssquare objects storing images

        # chess board
        self.board = chess.Board()
        self.human_colour = chess.WHITE

        # chess engine
        self.engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")

        # chess visualizer
        self.vis = ChessVisualizer()

        # game state
        self.state = GameState.HUMAN_MOVING

    # dispatching FSM states
    def update(self, img):
        if img is not None:
            self.updateSquares(img)

        if self.state == GameState.HUMAN_MOVING:
            self.__handleHumanMoving()

        elif self.state == GameState.ROBOT_MOVING:
            self.__handleRobotMoving()

        elif self.state == GameState.GAME_OVER:
            self.__handleGameOver()

    # FSM handlers
    def __handleGameOver(self):
        outcome = self.board.outcome()

        self.close()

        if outcome.winner == True:
            winner =  "Player"
        elif outcome.winner == False:
            winner =  "Robot"
        else:
            winner = "Draw"
        
        # arduino.write(bytes('winner: ' + winner + '\n', 'utf-8')) 

        return winner

    def __handleHumanMoving(self):
        changed = self.getChangedSquares()

        if not changed:
            return

        move = self.detectMove(changed)

        if move:
            print("Human played:", move)
            self.vis.play_move(move)
            self.vis.run()
            self.board.push(move)

            if self.board.is_game_over():
                self.state = GameState.GAME_OVER
            else:
                self.state = GameState.ROBOT_MOVING
        else:
            # still mid move or noise
            self.state = GameState.HUMAN_MOVING
    
    def __handleRobotMoving(self):
        result = self.engine.play(
            self.board, 
            chess.engine.Limit(time=0.1)
        )
        move = result.move
        
        # Make move
        print("Robot played:", move)
        self.board.push(move)
        self.vis.play_move(chess.Move.from_uci(move))
        self.vis.run()
        self.makeMove(move) # tell robot to physically make move

        if self.board.is_game_over(): # check for game over
            self.state = GameState.GAME_OVER
        else:
            self.state = GameState.WAITING_FOR_HUMAN

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

    # changed squares -> legal chess move
    def detectMove(self, changed):
        if len(changed) == 0: # no move
            return None
        
        possible_moves = []
        
        for move in self.board.legal_moves:
            from_row, from_col = 7 - (move.from_square // 8), move.from_square % 8
            to_row, to_col = 7 - (move.to_square // 8), move.to_square % 8
            
            observed_squares = set(changed)
            move_squares = {(from_row, from_col), (to_row, to_col)}

            # en passent
            if self.board.is_en_passant(move):
                cap_row = from_row
                cap_col = to_col
                move_squares.add((cap_row, cap_col))
            # castling
            if self.board.is_castling(move):
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
            for move in possible_moves:
                if move.promotion == chess.QUEEN: # if pawn promotion, default to queen
                    move_to_play = move
                    break
            else:
                move_to_play = possible_moves[0] #otherwise, pick first legal match

            return move_to_play
        else: 
            return None
    
    def makeMove(self, move):
        from_square = move.from_uci()
        to_square = move.to_uci()

        # arduino.write(bytes('from: ' + from_square + ' to: ' + to_square + '\n', 'utf-8')) 

    def close(self):
        self.engine.quit()

    # Retrieve occupancy from chess engine
    def getEngineOccupancy(self):
        occ = [[False for _ in range(8)] for _ in range(8)]
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                row = 7 - (square // 8)
                col = square % 8
                occ[row][col] = True
                
        return occ
    
    # Retrieve occupancy observed on real board
    def getObservedOccupancy(self):
        # return [[self.squares[row][col].isOccupied() for col in range(8)] for row in range(8)]
        return self.test_observed
    
    # Detect changes
    def getChangedSquares(self):
        observed = self.getObservedOccupancy()
        engine_occ = self.getEngineOccupancy()

        changed = []

        for row in range(8):
            for col in range(8):
                if observed[row][col] != engine_occ[row][col]:
                    changed.append((row, col))

        return changed
    
    # FOR TESTING ----
    def setObservedFromBoard(self, board):
        self.test_observed = [[False]*8 for _ in range(8)]
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                row = 7 - (square // 8)
                col = square % 8
                self.test_observed[row][col] = True

    

cb = ChessBoard(coord=None)

# Simulate initial board view
cb.setObservedFromBoard(cb.board)

# Simulate human playing e2e4
test_board = cb.board.copy()
test_board.push(chess.Move.from_uci("e2e4"))

cb.setObservedFromBoard(test_board)

# Run update
cb.update(None)