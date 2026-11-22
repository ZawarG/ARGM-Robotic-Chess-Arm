# Package: Chess Interfaces
Holds message types only.

No code is written in this package.

## Messages

### `EngineMove.msg`
This is used once a move has been decided by Stockfish.

It holds the current board state (FEN) and the move to play (UCI) so the planner can read it.

### `ArmPlan.msg`
The planner reads the EngineMove and sends this out.

It holds the list of planned physical actions. (e.g. a capture requires picking up one piece and moving it to the bin, then picking up another piece to move it to its new spot).

### `ArmStep.msg`
Each physical action held by ArmPlan is an ArmStep.

This holds a single instruction for the arm. A.K.A. where to pick up from and where to put down.

### `BoardState.msg`
This holds the camera occupancy report.

A.K.A. which squares have pieces on them.

## Flow
Stockfish → `EngineMove` → planner → `ArmPlan` (list of `ArmStep`) → arm