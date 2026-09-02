import serial
import chess, chess.engine
from enum import Enum, auto
from src.vision.board_vision import BoardVision
from src.ui.visualize import ChessVisualizer
from src.hardware.robot import RobotController

#  (\(\
# ( -.-)
# o_(")(")
# Chess board class adjusted to track the moves of two players (for testing)
# Also added: calibration phase

class GameState(Enum):
    WAITING_FOR_START = auto() # Waiting until board occupancy matches initial game occupancy
    HUMAN_MOVING = auto()
    ROBOT_MOVING = auto()
    ANIMATING_MOVE = auto()
    GAME_OVER = auto()
    WAITING_FOR_MOVE = auto()

class ChessBoard:
    def __init__(self, coord, M, warped_img=None):
        # Initialize components
        self.vision = BoardVision(coord)
        self.M = M

        # Occupancy profiles only make sense once the pieces are on the board.
        # If a warped frame is supplied up front, calibrate now (single-image test path). 
        # Otherwise defer until beginGame() is called, i.e. after the user has set up the pieces and pressed the start key.
        self.started = False
        if warped_img is not None:
            self.vision.initializeBoard(warped_img, M)
            self.started = True

        self.board = chess.Board()
        self.engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
        # self.robot = RobotController()
        self.visualizer = ChessVisualizer(self.board)

        # State management
        self.bot_is_white = None
        # self.state = GameState.ROBOT_MOVING if self.bot_is_white else GameState.HUMAN_MOVING
        self.state = GameState.WAITING_FOR_MOVE
        self.pending_push_move = None
        self.last_move_by_human = False

    # Calibrate occupancy profiles from the current (populated) frame, then start play.
    # Call this once the pieces are set up, e.g. on a keypress.
    def beginGame(self, raw_img):
        self.bot_is_white = self.vision.calibrate(raw_img, self.M)
        self.started = True

    # FSM state updater
    def update(self, img):
        if img is not None:
            self.vision.updateFrame(img)
        
        # Visualizer rendering
        if self.state == GameState.ANIMATING_MOVE:
            self.__handleAnimating()
        else:
            self.visualizer.update()

        # Game set up phase
        if self.state == GameState.WAITING_FOR_START:
            self.__handleWaitingForStart()

        # Standard game loop
        if self.state == GameState.WAITING_FOR_MOVE:
            self.__handleTrackBoard()
        if self.state == GameState.HUMAN_MOVING:
            self.__handleHumanMoving()
        elif self.state == GameState.ROBOT_MOVING:
            self.__handleRobotMoving()
        elif self.state == GameState.GAME_OVER:
            return self.__handleGameOver()

        return None

    # FSM handlers
    def __handleAnimating(self):
        finished = self.visualizer.animate_move_by_frame() # returns true if move over
        
        if finished and self.pending_push_move:
            # Push the move after animation
            self.board.push(self.pending_push_move)
            self.pending_push_move = None

            # Go to next FSM state
            if self.board.is_game_over():
                self.state = GameState.GAME_OVER
            else:
                self.state = GameState.WAITING_FOR_MOVE
                # switch between human and robot
                # self.state = GameState.ROBOT_MOVING if self.last_move_by_human else GameState.HUMAN_MOVING

    def __handleTrackBoard(self):
        stabilized_observed = self.vision.getStabilizedOccupancy()

        if stabilized_observed is None:
            return

        changed = self.getChangedSquares(stabilized_observed)
        if not changed:
            return

        move = self.detectMove(changed)
        print(move)

        if move:
            # Determine who made the move based on the engine's current turn
            current_turn = "White" if self.board.turn == chess.WHITE else "Black"
            print(f"Detected move ({current_turn}): {move}")
            
            self.pending_push_move = move  
            piece = self.board.piece_at(move.from_square)
            self.visualizer.start_animation(piece.symbol(), move.from_square, move.to_square)
            self.state = GameState.ANIMATING_MOVE 
        else:
            # Mid-move or noise, stay tracking
            self.state = GameState.WAITING_FOR_MOVE

    def __handleWaitingForStart(self):
        stabilized_observed = self.vision.getStabilizedOccupancy()
        
        # Wait until feed stabilizes
        if stabilized_observed is None:
            return
        
        # Check if board is at initial state (changed will be empty)
        changed = self.getChangedSquares(stabilized_observed)

        if not changed:
            # Transition to the first turn
            if self.bot_is_white:
                self.state = GameState.ROBOT_MOVING
            else:
                self.state = GameState.WAITING_FOR_MOVE

    def __handleHumanMoving(self):
        stabilized_observed = self.vision.getStabilizedOccupancy()

        # Only look for human moves if stabilized
        if stabilized_observed is None:
            return

        # Check for differences
        changed = self.getChangedSquares(stabilized_observed)
        if not changed:
            return

        # Turn differences into a legal chess move
        move = self.detectMove(changed)

        if move:
            print("Human played:", move)
            
            self.last_move_by_human = True
            self.pending_push_move = move  # store the move to push after animation finishes
            piece = self.board.piece_at(move.from_square)
            self.visualizer.start_animation(piece.symbol(), move.from_square, move.to_square)
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
        # self.robot.movePiece(move.from_square, move.to_square)
        
        self.last_move_by_human = False
        self.pending_push_move = move  # store the move to push after animation finishes
        piece = self.board.piece_at(move.from_square)
        self.visualizer.start_animation(piece.symbol(), move.from_square, move.to_square)
        self.state = GameState.ANIMATING_MOVE 

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

    # Changed squares -> legal chess move
    def detectMove(self, changed):
        if len(changed) == 0: # No move
            return None
        if len(changed) > 4: # Impossible (likely a hand is covering the board)
            return None
        
        print([chess.square_name(s) for s in changed])
        
        possible_moves = []
        observed_squares = set(changed)
        
        for move in self.board.legal_moves:
            # Only squares whose occupancy changes should appear in changed
            # The from square always becomes empty
            # The to square could have gone from empty-occupied or occupied-occupied
            move_squares = {move.from_square}

            print(move, move_squares)

            # en passent: 
            # pawn lands on an empty square (so to flips)
            # captured pawn sits on a separate square that becomes empty
            if self.board.is_en_passant(move):
                captured_square = chess.square(chess.square_file(move.to_square), 
                                                chess.square_rank(move.from_square))
                move_squares.add(move.to_square)
                move_squares.add(captured_square)
            # normal capture: 
            # destination was already occupied and stays occupie
            # its occupancy does not change. do not expect it in change
            elif self.board.is_capture(move):
                pass
            # regular move: 
            # destination goes from empty to occupied
            else:
                move_squares.add(move.to_square)

            # castling:
            # rook moves between two squares that both flip
            if self.board.is_castling(move):
                rank = chess.square_rank(move.from_square)
                if move.to_square > move.from_square: # kingside
                    rook_from = chess.square(7, rank) # rook origin
                    rook_to   = chess.square(5, rank) # rook destination
                else:  # queenside
                    rook_from = chess.square(0, rank) # rook origin
                    rook_to   = chess.square(3, rank) # rook destination
                move_squares.add(rook_from)
                move_squares.add(rook_to)
            
            # ! What to do for promotion? -- user input
            if move_squares <= observed_squares:
                possible_moves.append(move)
        
        print('possible moves', possible_moves)

        if possible_moves:
            for move in possible_moves:
                if move.promotion == chess.QUEEN: # if pawn promotion, default to queen
                    move_to_play = move
                    break
            else:
                move_to_play = possible_moves[0] # otherwise, pick first legal match

            return move_to_play
        
        return None
    
    # Retrieve occupancy from chess engine
    def getEngineOccupancy(self):
        occ = [[False for _ in range(8)] for _ in range(8)]
        
        for visual_row in self.vision.squares:
            for square_obj in visual_row:
                row, col = square_obj.coord
                square_file_rank = square_obj.name
                
                chess_square = chess.parse_square(square_file_rank)

                if self.board.piece_at(chess_square):
                    occ[row][col] = True

        return occ

    # Retrieve expected piece colours from chess engine (source of truth)
    def getEngineSides(self):
        sides = [[None for _ in range(8)] for _ in range(8)]

        for visual_row in self.vision.squares:
            for square_obj in visual_row:
                row, col = square_obj.coord
                piece = self.board.piece_at(chess.parse_square(square_obj.name))

                if piece is not None:
                    sides[row][col] = "White" if piece.color == chess.WHITE else "Black"

        return sides

    # Detect changes
    def getChangedSquares(self, stabilized_observed):
        engine_occ = self.getEngineOccupancy()

        changed = []

        for row in range(8):
            for col in range(8):
                if stabilized_observed[row][col] != engine_occ[row][col]:
                    changed.append(chess.parse_square(self.vision.squares[row][col].name))

        return changed
    
    def close(self):
        self.engine.quit()
        self.visualizer.quit()