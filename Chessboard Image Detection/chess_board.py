from chess_square import ChessSquare
import chess, chess.engine
from enum import Enum, auto
import serial

# Replace 'COM4' with your Arduino's port (e.g., '/dev/ttyUSB0')
# Ensure the baud rate matches the one in your Arduino code
# arduino = serial.Serial(port='COM4', baudrate=115200, timeout=.1)

class GameState(Enum):
    WAITING_FOR_HUMAN = auto()
    HUMAN_MOVING = auto()
    ROBOT_THINKING = auto()
    ROBOT_MOVING = auto()
    GAME_OVER = auto()

class ChessBoard:
    def __init__(self, coord):
        self.coord = coord # list of all positions of each square in board

        # vision layer
        self.squares = [[None for _ in range(8)] for _ in range(8)] # list of chesssquare objects storing images
        self.prev_occ = [[False for _ in range(8)] for _ in range(8)] # previous move's square occupancy
        self.initOcc()

        # chess board
        self.board = chess.Board()
        self.human_colour = chess.WHITE

        # chess engine
        self.engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")

        # FSM variables
        self.stable_frames = 0
        self.stable_thresh = 5 # 30 frames ~= 1 second

        # game state
        self.state = GameState.WAITING_FOR_HUMAN

    # this is what the main function will run in its while loop, it is just dispatching FSM states
    def update(self, img):
        self.updateSquares(img)

        if self.state == GameState.WAITING_FOR_HUMAN:
            self.__handleWaitingForHuman()

        elif self.state == GameState.HUMAN_MOVING:
            self.__handleHumanMoving()

        elif self.state == GameState.ROBOT_THINKING:
            self.__handleRobotThinking()

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

    def __handleWaitingForHuman(self):
        changed = self.detectChanges() # Check if any square occupancy has changed

        if len(changed) > 0:
            # Track current/possible move
            self.pending_changes = set(changed)
            self.stable_frames = 0
            self.state = GameState.HUMAN_MOVING

    # def __handleWaitingForHuman(self):
    #     observed = self.getObservedOccupancy()

    #     matching_moves = []

    #     # Iterate through possible moves from the engine
    #     # If the possible move matches the occupancy observed, then append it to a list
    #     for move in self.board.legal_moves:
    #         temp_board = self.board.copy()
    #         temp_board.push(move)

    #         expected = self.getBoardOccupancy(temp_board)

    #         if observed == expected:
    #             matching_moves.append(move)

    #     # If there is only one possible move, we update the engine
    #     if len(matching_moves) == 1:
    #         move = matching_moves[0]
    #         print("Human played:", move)
    #         self.board.push(move)

    #         if self.board.is_game_over():
    #             self.state = GameState.GAME_OVER
    #         else:
    #             self.state = GameState.ROBOT_THINKING
    
    def __handleHumanMoving(self):
        changed = self.detectChanges()

        if changed: # board is currently changing
            # keep collecting all changed squares while occupancy is unstable
            self.pending_changes.update(changed)
            self.stable_frames = 0 # there have been no frames yet where the board is stable at this position
            return

        # no changes this frame: potentially stable
        self.stable_frames += 1

        if self.stable_frames < self.stable_thresh: 
            return
            
        # board has been stable long enough
        move = self.detectMove(list(self.pending_changes))

        if move:
            print("Human played:", move)
            self.board.push(move)

            if self.board.is_game_over(): # check for game over
                self.state = GameState.GAME_OVER
            else:
                self.state = GameState.ROBOT_THINKING
        else: 
            # invalid move, it was likely due to hand moving or lighting glitch
            self.state = GameState.WAITING_FOR_HUMAN

        self.pending_changes.clear()
        self.stable_frames = 0
    
    def __handleRobotThinking(self):
        result = self.engine.play(
            self.board, 
            chess.engine.Limit(time=0.1)
        )
        self.pending_robot_move = result.move
        self.state = GameState.ROBOT_MOVING

    def __handleRobotMoving(self):
        move = self.pending_robot_move
        print("Robot played:", move)

        self.board.push(move) # apply best move to board

        self.makeMove(move) # tell robot to physically make move

        self.endRobotMove() # reset variables after robot finished moving

        if self.board.is_game_over(): # check for game over
            self.state = GameState.GAME_OVER
        else:
            self.state = GameState.WAITING_FOR_HUMAN
    
    def endRobotMove(self):
        self.pending_robot_move = None
        self.prev_occ = [[sq.isOccupied() for sq in row] for row in self.squares]
        self.curr_occ = [row.copy() for row in self.prev_occ]
        self.stable_frames = 0

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
            for move in possible_moves:
                if move.promotion == chess.QUEEN: # if pawn promotion, default to queen
                    move_to_play = move
                    break
            else:
                move_to_play = possible_moves[0] #otherwise, pick first legal match

            self.prev_occ = [row.copy() for row in self.curr_occ]
            return move_to_play
    
    def makeMove(self, move):
        from_square = move.from_uci()
        to_square = move.to_uci()

        # arduino.write(bytes('from: ' + from_square + ' to: ' + to_square + '\n', 'utf-8')) 

    def close(self):
        self.engine.quit()

    # Retrieve occupancy from chess engine
    def getEngineOcc(self):
        occ = [[False for _ in range(8)] for _ in range(8)]
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                row = 7 - (square // 8)
                col = square % 8
                occ[row][col] = True
                
        return occ
    
    # Retrieve occupancy observed on real board
    def getObservedOcc(self):
        return [[self.squares[row][col].isOccupied() for col in range(8)]
            for row in range(8)]

    # ------ this should not be needed, but i'm keeping it while working with a static image
    # apply initial chess state
    def initOcc(self):
        for row in [0,1,6,7]:
            for col in range(8):
                self.prev_occ[row][col] = True
                self.curr_occ[row][col] = True