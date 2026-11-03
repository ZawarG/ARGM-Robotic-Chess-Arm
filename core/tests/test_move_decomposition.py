"""
Headless test for the move-decomposition layer — no vision, no engine, no arm.

decompose(board, move) is a pure function: given the board position BEFORE a move
and the move itself, it returns the ordered list of physical (from, to) pick-and-place
steps the arm must perform. Squares are returned as names ("e2"); off-board endpoints
are strings (BIN, SUPPLY[...]). This checks all five move kinds.

Run it from the "core" directory with the repo venv:

    ../.venv/bin/python -m pytest tests/test_move_decomposition.py -v
"""
import chess
import pytest

from src.logic.move_decomposition import decompose, BIN, SUPPLY

CASES = [
    # (id, fen, uci, expected steps)
    ("normal", chess.STARTING_FEN, "e2e4",
     [("e2", "e4")]),

    # Victim is removed FIRST, then the capturing piece moves in.
    ("capture", "4k3/8/8/3n4/8/5B2/8/4K3 w - - 0 1", "f3d5",
     [("d5", BIN), ("f3", "d5")]),

    # King first, then rook.
    ("castle_kingside", "4k3/8/8/8/8/8/8/4K2R w K - 0 1", "e1g1",
     [("e1", "g1"), ("h1", "f1")]),

    ("castle_queenside", "4k3/8/8/8/8/8/8/R3K3 w Q - 0 1", "e1c1",
     [("e1", "c1"), ("a1", "d1")]),

    # The captured pawn sits on d5, not on the destination d6.
    ("en_passant", "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "e5d6",
     [("d5", BIN), ("e5", "d6")]),

    # The pawn never reaches the last rank: retire it, fetch a queen from supply.
    ("promotion", "6k1/4P3/8/8/8/8/8/4K3 w - - 0 1", "e7e8q",
     [("e7", BIN), (SUPPLY[chess.QUEEN], "e8")]),

    # Clear the victim, retire the pawn, fetch the queen.
    ("promotion_capture", "3r2k1/4P3/8/8/8/8/8/4K3 w - - 0 1", "e7d8q",
     [("d8", BIN), ("e7", BIN), (SUPPLY[chess.QUEEN], "d8")]),
]


@pytest.mark.parametrize("fen, uci, expected",
                         [c[1:] for c in CASES],
                         ids=[c[0] for c in CASES])
def test_decompose(fen, uci, expected):
    board = chess.Board(fen)
    move = chess.Move.from_uci(uci)
    assert move in board.legal_moves, f"{uci} is not legal in {fen}"
    assert decompose(board, move) == expected
