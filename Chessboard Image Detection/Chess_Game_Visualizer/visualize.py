import pygame
import chess
import chess.engine

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

    def __init__(self):

        self.board = chess.Board()

        pygame.init()
        self.screen = pygame.display.set_mode((board_pixels, board_pixels))
        pygame.display.set_caption("Chess Robot Visualizer")

        self.clock = pygame.time.Clock()

        # load images
        self.piece_images = {}
        for symbol, name in symbol_to_name.items():
            img = pygame.image.load(f'Chessboard Image Detection/Chess_Game_Visualizer/images/{name}.png')
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

        if move not in self.board.legal_moves:
            print("Illegal:", move)
            return

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

        self.board.push(move)

        pygame.time.delay(120)

    def update(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

        self.draw_board()

        pygame.display.flip()

        self.clock.tick(60)

    def run(self):

        while self.running:
            self.update()

        pygame.quit()


"""
vis = ChessVisualizer()

vis.play_move(chess.Move.from_uci("e2e4"))
vis.play_move(chess.Move.from_uci("e7e5"))
vis.play_move(chess.Move.from_uci("g1f3"))
vis.play_move(chess.Move.from_uci("b8c6"))

vis.run()

"""