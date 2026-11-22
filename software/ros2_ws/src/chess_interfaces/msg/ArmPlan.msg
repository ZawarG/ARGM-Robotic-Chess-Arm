# Ordered steps the arm must perform to play one chess move.

std_msgs/Header header

# The move being executed, in UCI notation (e.g. "e2e4", "e7e8q")
string uci_move

ArmStep[] steps
