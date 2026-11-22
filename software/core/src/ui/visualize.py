import pygame
import chess
from PIL import Image
from pathlib import Path

#  (\(\
# ( -.-)
# o_(")(")
# This class visualizes the real-life chess game in an online screen with live updates

square_size = 80
board_pixels = square_size * 8

LIGHT = (235, 235, 208)
DARK = (119, 148, 85)

symbol_to_name = {
    'P': 'white-pawn',
    'N': 'white-knight',
    'B': 'white-bishop',
    'R': 'white-rook',
    'Q': 'white-queen',
    'K': 'white-king',
    'p': 'black-pawn',
    'n': 'black-knight',
    'b': 'black-bishop',
    'r': 'black-rook',
    'q': 'black-queen',
    'k': 'black-king'
}

class ChessVisualizer:

    def __init__(self, board):
        self.board = board

        self.animating_move = None

        pygame.init()
        self.screen = pygame.display.set_mode((board_pixels, board_pixels))
        pygame.display.set_caption("Chess Robot Visualizer")

        self.clock = pygame.time.Clock()

        self.piece_images = {}

        # absolute path logic
        script_dir = Path(__file__).resolve().parent
        image_dir = script_dir.parent.parent / 'data' / 'game-visualizer-images'

        for symbol, name in symbol_to_name.items():
            img_path = image_dir / f'{name}.png'

            if not img_path.exists():
                raise FileNotFoundError(f"Could not find piece image: {img_path}")

            try:
                pil_img = Image.open(img_path).convert("RGBA")
                size = pil_img.size
                data = pil_img.tobytes()

                py_img = pygame.image.fromstring(data, size, "RGBA")
                img = pygame.transform.scale(py_img, (square_size, square_size))
                self.piece_images[name] = img
            except Exception as e:
                print(f"Failed to load or process image {name}: {e}")

            if not Path.exists(img_path):
                raise FileNotFoundError(f"Could not find piece image: {img_path}")
            
            # print(f'Chessboard Image Detection/data/game-visualizer-images/{name}.png')
            # img = pygame.image.load(img_path)
            img = pygame.transform.scale(img, (square_size, square_size))
            self.piece_images[name] = img

        self.running = True

    def draw_board(self, exclude_square=None):

        for r in range(8):
            for c in range(8):

                color = LIGHT if (r+c)%2==0 else DARK

                pygame.draw.rect(
                    self.screen,
                    color,
                    pygame.Rect(
                        c*square_size,
                        r*square_size,
                        square_size,
                        square_size
                    )
                )

                square = chess.square(c, 7-r)

                if square == exclude_square:
                    continue

                piece = self.board.piece_at(square)

                if piece:

                    name = symbol_to_name[piece.symbol()]

                    self.screen.blit(
                        self.piece_images[name],
                        (c*square_size, r*square_size)
                    )

    def animate_move(self, piece_symbol, start_sq, end_sq):

        start_r = 7 - (start_sq // 8)
        start_c = start_sq % 8

        end_r = 7 - (end_sq // 8)
        end_c = end_sq % 8

        start_px = (start_c*square_size, start_r*square_size)
        end_px = (end_c*square_size, end_r*square_size)

        frames = 20

        for f in range(frames):

            t = f/frames

            x = start_px[0] + (end_px[0]-start_px[0])*t
            y = start_px[1] + (end_px[1]-start_px[1])*t

            self.draw_board(exclude_square=start_sq)

            name = symbol_to_name[piece_symbol]

            self.screen.blit(self.piece_images[name], (x,y))

            pygame.display.flip()

            self.clock.tick(60)

    def play_move(self, move):

        # this is already checked in chess_board before calling play_move
        # if move not in self.board.legal_moves:
        #     print("Illegal:", move)
        #     return

        piece = self.board.piece_at(move.from_square)
        piece_symbol = piece.symbol()

        self.animate_move(piece_symbol, move.from_square, move.to_square)

        if self.board.is_castling(move):

            rank = chess.square_rank(move.from_square)

            if chess.square_file(move.to_square) == 6:
                rook_from = chess.square(7, rank)
                rook_to = chess.square(5, rank)
            else:
                rook_from = chess.square(0, rank)
                rook_to = chess.square(3, rank)

            rook = self.board.piece_at(rook_from)

            self.animate_move(
                rook.symbol(),
                rook_from,
                rook_to
            )

        pygame.time.delay(120)

    def update(self):

        self.handle_events() 

        self.draw_board()

        pygame.display.flip()

        self.clock.tick(60)

    def run(self):

        while self.running:
            self.update()

        pygame.quit()

        # tells the engine to start animating for a total of total_frames
    def start_animation(self, piece_symbol, start_sq, end_sq, total_frames = 20):
        self.animating_move = (piece_symbol, start_sq, end_sq, 0, total_frames)

    def animate_move_by_frame(self):
        if self.animating_move is None: 
            return True

        piece_symbol, start_sq, end_sq, frame, total_frames = self.animating_move

        # compute position
        start_r = 7 - (start_sq // 8)
        start_c = start_sq % 8

        end_r = 7 - (end_sq // 8)
        end_c = end_sq % 8

        start_px = (start_c*square_size, start_r*square_size)
        end_px = (end_c*square_size, end_r*square_size)

        x = start_px[0] + (end_px[0]-start_px[0])*(frame/total_frames)
        y = start_px[1] + (end_px[1]-start_px[1])*(frame/total_frames)

        self.handle_events() 

        self.draw_board(exclude_square=start_sq)

        name = symbol_to_name[piece_symbol]

        self.screen.blit(self.piece_images[name], (x,y))

        pygame.display.flip()
        self.clock.tick(60)

        frame += 1
        if frame >= total_frames:
            self.animating_move = None
            return True
        else:
            self.animating_move = (piece_symbol, start_sq, end_sq, frame, total_frames)
            return False

    def quit(self):
        pygame.display.quit()
        pygame.quit()

    def handle_events(self):
        # handle pygame quit
        # return false if window close
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
        return self.running
    

# vis = ChessVisualizer(chess.Board())

# vis.play_move(chess.Move.from_uci("e2e4"))
# vis.play_move(chess.Move.from_uci("e7e5"))
# vis.play_move(chess.Move.from_uci("g1f3"))
# vis.play_move(chess.Move.from_uci("b8c6"))

# vis.run()

# testing
if __name__ == "__main__":
    # Initialize board
    board = chess.Board()

    # Initialize visualizer
    vis = ChessVisualizer(board)

    # Define some test moves
    test_moves = [
        chess.Move.from_uci("e2e4"),
        chess.Move.from_uci("e7e5"),
        chess.Move.from_uci("g1f3"),
        chess.Move.from_uci("b8c6")
    ]

    current_move_index = 0
    animating = False

    running = True
    while running and vis.running:
        vis.handle_events()

        if not animating and current_move_index < len(test_moves):
            # Start animating next move
            move = test_moves[current_move_index]
            piece = board.piece_at(move.from_square)
            vis.start_animation(piece.symbol(), move.from_square, move.to_square)
            animating = True

        if animating:
            # Animate one frame
            finished = vis.animate_move_by_frame()
            if finished:
                board.push(test_moves[current_move_index])
                current_move_index += 1
                animating = False

        else:
            vis.update()

    pygame.quit()