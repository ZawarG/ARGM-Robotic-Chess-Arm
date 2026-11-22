# A move chosen by the engine, with the position it was chosen in.
#
# The FEN travels with the move so the planner can expand it without
# having to track game state itself: decompose() needs the board as it
# was BEFORE the move was played.

std_msgs/Header header

# Position before the move, in Forsyth-Edwards Notation
string fen

# The move, in UCI notation (e.g. "e2e4", "e7e8q")
string uci_move
