# One pick-and-place step, mirroring a (from, to) tuple from move_decomposition.decompose().
#
# Each location is either a square name ("a1".."h8") or an off-board location:
#   "bin"                                       captured / retired pieces
#   "supply_q", "supply_r", "supply_b", "supply_n"   spare pieces for promotion

string from_location
string to_location
