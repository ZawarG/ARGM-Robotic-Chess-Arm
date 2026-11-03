"""
Headless test for the human-input promotion flow — no video, no Stockfish, no vision.

It builds a ChessBoard via __new__ (skipping the heavy __init__) and stubs only the
two collaborators the promotion path touches: vision.squareDifference (capture check)
and visualizer.start_animation (animation kickoff). Then it drives the exact sequence
main.py's key handler would: detectMove -> PENDING_PROMOTION -> selectPromotion -> confirmPromotion.

Run it from the "Chessboard Image Detection" directory with the repo venv:

    ../.venv/bin/python tests/test_promotion.py
"""
import sys, os

# Make "src" importable no matter where this is run from: the package root is the
# "Chessboard Image Detection" dir, which is this file's parent's parent.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import chess
from src.logic.chess_board import ChessBoard, GameState


class StubVision:
    # A promotion-by-capture would call this; return a big diff so the capture is accepted.
    def squareDifference(self, name):
        return 999.0

class StubVisualizer:
    def __init__(self):
        self.calls = []
    def start_animation(self, symbol, frm, to):
        self.calls.append((symbol, frm, to))


def make_board(fen):
    game = ChessBoard.__new__(ChessBoard)          # skip __init__ (no engine/video/vision)
    game.board = chess.Board(fen)
    game.vision = StubVision()
    game.visualizer = StubVisualizer()
    game.state = GameState.WAITING_FOR_MOVE
    game.pending_push_move = None
    game.promotion_candidates = None
    game.promotion_selection = 'q'
    game.last_move_by_human = False
    return game


def changed_for(fen, from_sq, to_sq):
    """The squares vision would flag as occupancy-changed for a non-capture promotion."""
    return [chess.parse_square(from_sq), chess.parse_square(to_sq)]


def run_case(name, fen, from_sq, to_sq, pick, expected_uci):
    print(f"\n=== {name} ===")
    game = make_board(fen)
    changed = changed_for(fen, from_sq, to_sq)

    move = game.detectMove(changed)
    assert move is None, f"expected detectMove to defer (None), got {move}"
    assert game.promotion_candidates is not None, "expected promotion candidates to be stashed"
    assert len(game.promotion_candidates) == 4, \
        f"expected 4 promotion candidates, got {len(game.promotion_candidates)}"
    print("  detectMove deferred; candidates:",
          [m.uci() for m in game.promotion_candidates])

    # Simulate the handler transitioning to PENDING_PROMOTION (as the FSM handlers do)
    game.state = GameState.PENDING_PROMOTION
    game.promotion_selection = 'q'
    assert game.isAwaitingPromotion()

    # Human presses a key to pick, then Enter
    game.selectPromotion(pick)
    assert game.promotion_selection == pick
    game.confirmPromotion()

    assert game.pending_push_move is not None, "expected a move queued for animation"
    assert game.pending_push_move.uci() == expected_uci, \
        f"expected {expected_uci}, got {game.pending_push_move.uci()}"
    assert game.state == GameState.ANIMATING_MOVE
    assert game.promotion_candidates is None, "candidates should be cleared after commit"
    print(f"  picked '{pick}' -> committed {game.pending_push_move.uci()}  ✓")
    print(f"  animation kicked off: {game.visualizer.calls[-1]}")


if __name__ == "__main__":
    # White pawn on a7, empty a8 -> straight promotion. Only the a-pawn can move.
    fen_white = "8/P7/8/8/8/8/8/4k1K1 w - - 0 1"
    run_case("White a7->a8, pick Rook", fen_white, "a7", "a8", "r", "a7a8r")
    run_case("White a7->a8, default Queen (Enter only)", fen_white, "a7", "a8", "q", "a7a8q")
    run_case("White a7->a8, pick kNight", fen_white, "a7", "a8", "n", "a7a8n")

    # Black pawn on h2, empty h1 -> straight promotion. Black to move.
    fen_black = "4k1K1/8/8/8/8/8/7p/8 b - - 0 1"
    run_case("Black h2->h1, pick Bishop", fen_black, "h2", "h1", "b", "h2h1b")

    print("\nAll promotion cases passed ✓")
