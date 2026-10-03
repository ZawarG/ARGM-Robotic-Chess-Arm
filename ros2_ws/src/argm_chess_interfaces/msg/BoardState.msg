# Board as seen by the vision node.

std_msgs/Header header

# Position in Forsyth-Edwards Notation
string fen

# Per-square occupancy, indexed like python-chess squares (a1=0 .. h8=63)
bool[64] occupancy
