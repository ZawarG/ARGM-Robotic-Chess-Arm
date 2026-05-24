import serial
import chess, chess.engine
from enum import Enum, auto
from src.vision.board_vision import BoardVision
from src.ui.visualize import ChessVisualizer
from src.hardware.robot import RobotController

"""
The entire chessboard is an object. 
This class handles the game engine/finite state machine.
"""

class GameState(Enum):
    HUMAN_MOVING = auto()
    ROBOT_MOVING = auto()
    ANIMATING_MOVE = auto()
    GAME_OVER = auto()

class ChessBoard:
    def __init__(self, coord, bot_is_white):
        # Initialize components
        self.vision = BoardVision(coord, bot_is_white)
        self.board = chess.Board()
        self.engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
        # self.vis = ChessVisualizer(self.board)
        # self.robot = RobotController()

        # State management
        self.state = GameState.ROBOT_MOVING if bot_is_white else GameState.HUMAN_MOVING
        self.pending_push_move = None
        self.last_move_by_human = False
        
    # FSM state updater
    def update(self, img):
        if img is not None:
            self.vision.updateFrame(img)
        
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
        elif outcome.winner == self.bot_is_white: # outcome.winner is true if it's 
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
            
            self.last_move_by_human = True
            self.pending_push_move = move  # store the move to push after animation finishes
            piece = self.board.piece_at(move.from_square)
            self.vis.start_animation(piece.symbol(), move.from_square, move.to_square)
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

        print("Robot played:", move)
        self.robot.movePiece(move.from_square, move.to_square)
        
        self.last_move_by_human = False
        self.pending_push_move = move  # store the move to push after animation finishes
        piece = self.board.piece_at(move.from_square)
        self.vis.start_animation(piece.symbol(), move.from_square, move.to_square)
        self.state = GameState.ANIMATING_MOVE 

    # Changed squares -> legal chess move
    def detectMove(self, changed):
        if len(changed) == 0: # No move
            return None
        
        possible_moves = []
        observed_squares = set(changed)
        
        for move in self.board.legal_moves:
            from_row, from_col = 7 - (move.from_square // 8), move.from_square % 8
            to_row, to_col = 7 - (move.to_square // 8), move.to_square % 8
            move_squares = {(from_row, from_col), (to_row, to_col)}

            # en passent
            if self.board.is_en_passant(move):
                move_squares.add((from_row, to_col))
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
    
    # Detect changes
    def getChangedSquares(self):
        observed = self.vision.getObservedOccupancy()
        engine_occ = self.getEngineOccupancy()

        changed = []

        for row in range(8):
            for col in range(8):
                if observed[row][col] != engine_occ[row][col]:
                    changed.append((row, col))

        return changed
    
    def close(self):
        self.engine.quit()
        # self.vis.quit()