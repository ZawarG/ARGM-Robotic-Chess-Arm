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
    ANIMATING_MOVE = auto()
    GAME_OVER = auto()

class ChessBoard:
    def __init__(self, coord, colour):
        self.coord = coord # list of all positions of each square in board

        # vision layer
        self.squares = [[None for _ in range(8)] for _ in range(8)] # list of chesssquare objects storing images

        # chess board
        self.board = chess.Board()
        self.human_colour = chess.WHITE

        # chess engine
        self.engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")

        # chess visualizer
        self.vis = ChessVisualizer(self.board)
        self.pending_push_move = None
        self.last_move_by_human = False

        # decide who is black/white
        self.colour = colour
        
        # game state
        if colour:
            self.state = GameState.HUMAN_MOVING
        else: 
            self.state = GameState.ROBOT_MOVING

    # dispatching FSM states
    def update(self, img):
        if img is not None:
            self.updateSquares(img)  
        
        if self.state == GameState.ANIMATING_MOVE:
            self.__handleAnimating()
        else:
            self.vis.update()

        if self.state == GameState.HUMAN_MOVING:
            self.__handleHumanMoving()
            
        elif self.state == GameState.ROBOT_MOVING:
            self.__handleRobotMoving()

        elif self.state == GameState.GAME_OVER:
            return self.__handleGameOver()

        return None

    # FSM handlers
    def __handleAnimating(self):
        finished = self.vis.animate_move_by_frame() # returns true if move over
        
        if finished and self.pending_push_move:
            # Push the move after animation
            self.board.push(self.pending_push_move)
            self.pending_push_move = None

            # Go to next FSM state
            if self.board.is_game_over():
                self.state = GameState.GAME_OVER
            else:
                # switch between human and robot
                self.state = GameState.ROBOT_MOVING if self.last_move_by_human else GameState.HUMAN_MOVING

    def __handleGameOver(self):
        outcome = self.board.outcome()

        self.close()

        if outcome.winner == None:
            winner = "Draw"
        elif outcome.winner == self.colour:
            winner =  "Player"
        else:
            winner =  "Robot"
        
        # arduino.write(bytes('winner: ' + winner + '\n', 'utf-8')) 

        return winner

    def __handleHumanMoving(self):
        changed = self.getChangedSquares()

        if not changed:
            return

        move = self.detectMove(changed)

        if move:
            print("Human played:", move)
            
            piece = self.board.piece_at(move.from_square)
            piece_symbol = piece.symbol()

            self.last_move_by_human = True
            self.pending_push_move = move  # store the move to push after animation finishes
            self.vis.start_animation(piece_symbol, move.from_square, move.to_square)
            self.state = GameState.ANIMATING_MOVE 

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
        piece = self.board.piece_at(move.from_square)
        piece_symbol = piece.symbol()
        
        self.last_move_by_human = False
        self.pending_push_move = move  # store the move to push after animation finishes
        self.vis.start_animation(piece_symbol, move.from_square, move.to_square)

        self.robotMakeMove(move) # tell robot to physically make move

        self.state = GameState.ANIMATING_MOVE 

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
        
        return None
    
    def robotMakeMove(self, move):
        from_square = move.from_square
        to_square = move.to_square

        print("This is where robot would physically make the move")

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

    def force_human_move(self, uci_move: str):
        # Simulate a human move for testing purposes.
        move = chess.Move.from_uci(uci_move)
        if move in self.board.legal_moves:
            # Update observed squares to simulate move
            test_board = self.board.copy()
            test_board.push(move)
            self.setObservedFromBoard(test_board)
            print(f"[TEST] Simulated human move: {uci_move}")
    
# TESTING CODE
"""
Verify this loop works:
Human moving ->
Robot moving ->
Human moving ->
"""
if __name__ == "__main__":
    test_human_moves = ["e2e4", "d7d5", "e4d5", "b8c6", "g1f3"]
    move_idx = 0
    cb = ChessBoard(coord=None)
    cb.setObservedFromBoard(cb.board)

    running = True
    while running:
        # Check if visualizer is still running
        if not cb.vis.running:
            break

        # Simulate human input for testing
        if cb.state == GameState.HUMAN_MOVING and move_idx < len(test_human_moves):
            # Slow down simulation so we can see it
            cb.force_human_move(test_human_moves[move_idx])
            move_idx += 1

        # Update FSM
        outcome = cb.update(None)

        # Check for game over
        if outcome:
            print(f"Game Result: {outcome}")
            running = False

    cb.vis.quit()
    cb.close()
