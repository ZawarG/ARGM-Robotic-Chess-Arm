import chess

#  (\(\
# ( -.-)
# o_(")(")
# Turns a single python-chess Move into the ordered list of physical
# pick-and-place steps the arm must actually perform.
#
# A step is a (from, to) tuple. `from` and `to` are normally squares (ints 0..63, a1=0 .. h8=63)
# A destination may instead be an off-board bin string, and a source may be a supply string:
#
#   normal:     [(e2, e4)]
#   capture:    [(d5, BIN), (e4, d5)]          # remove victim FIRST
#   castle:     [(e1, g1), (h1, f1)]           # king, then rook
#   en passant: [(d5, BIN), (e5, d6)]          # victim is NOT on the destination
#   promotion:  [(e7, BIN), (QUEEN_SUPPLY, e8)] # retire pawn, fetch new piece

BIN = "bin"  # where captured / retired pieces go off-board

# Off-board supply of spare pieces to bring in on promotion, keyed by piece type.
SUPPLY = {
    chess.QUEEN: "supply_q",
    chess.ROOK: "supply_r",
    chess.BISHOP: "supply_b",
    chess.KNIGHT: "supply_n",
}


def decompose(board, move):
    """Expand a single legal `move` (in the context of `board`, BEFORE it is pushed) into an ordered list of (from, to) pick-and-place steps."""
    steps = []

    # 1. Clear any captured piece off the board first.
    if board.is_en_passant(move):
        # The captured pawn sits behind the destination, not on it.
        victim = _en_passant_victim_square(board, move)
        steps.append((victim, BIN))
    elif board.is_capture(move):
        steps.append((move.to_square, BIN))

    # 2. Move the piece itself.
    if move.promotion:
        # The pawn never reaches the last rank physically: retire it, bring a new piece.
        steps.append((move.from_square, BIN))
        steps.append((SUPPLY[move.promotion], move.to_square))
    else:
        steps.append((move.from_square, move.to_square))

    # 3. Castling also moves the rook.
    if board.is_castling(move):
        steps.extend(_castling_rook_step(board, move))

    return steps


def _en_passant_victim_square(board, move):
    """The square of the pawn captured en passant: same file as the
    destination, same rank as the moving pawn's origin."""
    return chess.square(chess.square_file(move.to_square),
                        chess.square_rank(move.from_square))


def _castling_rook_step(board, move):
    """The rook's (from, to) step for a castling king move."""
    rank = chess.square_rank(move.from_square)
    if chess.square_file(move.to_square) > chess.square_file(move.from_square):
        # Kingside: rook h -> f
        return [(chess.square(7, rank), chess.square(5, rank))]
    else:
        # Queenside: rook a -> d
        return [(chess.square(0, rank), chess.square(3, rank))]
