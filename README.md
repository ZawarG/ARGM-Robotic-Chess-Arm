# ARGM — Artificial Robotic GrandMaster

## Overview
A robotic chess system that detects board state from a camera feed, tracks moves through square occupancy changes, interfaces with a chess engine, and ultimately controls a robotic arm to execute physical moves.
> The system is currently capable of detecting board state, tracking moves, and visualizing gameplay in real time using Stockfish.

## How It Works
1. A camera captures the chessboard in an empty state
2. YOLO-assisted board detection locates the board
   If this fails, a manual calibration window prompts the user to input the chess board corners
3. OpenCV warps the board and segments it into squares
4. Occupancy changes between consecutive board states are analyzed to infer player moves
5. Moves are validated and tracked in software
6. Stockfish generates a response move
7. Future versions transmit validated moves to a custom robotic arm for physical execution

## Technologies
- Python
- OpenCV
- YOLO
- Arduino/C++
- FSMs (Finite State Machines)
- Computer Vision

## Demo & Screenshots

### Board Detection & Segmentation
<img width="400" height="438" alt="Chess Board and Square Localization" src="https://github.com/user-attachments/assets/1ac860ec-5a66-41e0-ac07-b7a1ec556efe" />

Automatic board localization using YOLO-assisted detection and OpenCV preprocessing.
The pipeline extracts the chessboard from the camera feed, applies a perspective warp, and generates a stable 8×8 grid for gameplay.

### Occupancy Detection
<img width="400" height="332" alt="Manual Calibration and Occupancy Detection" src="https://github.com/user-attachments/assets/87d4be65-9997-4b52-bdf4-a6e7a2ac9360" />

After calibration, the board is split into an 8×8 grid, and each square is analyzed independently in HSV space.
The system uses a learned empty-square profile to classify each square as occupied or empty, improving robustness against lighting changes and board texture noise.
A manual calibration fallback is used when automatic detection fails. This mode is also used for testing since the primary detection pipeline assumes an initially visible, empty board.
Note: Square cropping is intentionally tight to isolate per-square analysis and improve occupancy classification reliability.

### Digital Visualizer
<img width="400" height="422" alt="Digital Chess Game Visualizer" src="https://github.com/user-attachments/assets/bc8d921f-1aa7-483a-a2b2-34497dbc55eb" />

The visualizer mirrors the physical game state by replaying moves as they are detected and validated by the system. It serves as a debugging and verification tool for board-state tracking and Stockfish integration.
It supports:
- Real-time board rendering from a `python-chess` state object
- Smooth piece animations for moves (including castling handling)
- Synchronization with engine-generated and human-detected moves
- Frame-based animation loop for smooth transitions

## System Loop
```
Initialization
├─ Board Localization
├─ Board Calibration
├─ Board Segmentation (64 Squares)
└─ Chess Engine Initialization

Game Loop (FSM)
├─ Human Turn
│  ├─ Wait for move
│  ├─ Detect occupancy changes
│  ├─ Validate move
│  └─ Update game state
│
├─ Robot Turn
│  ├─ Query Stockfish
│  ├─ Generate move
│  ├─ Send command to arm
│  └─ Update game state
│
└─ Digital Visualizer Updates
```

## Capabilities
- Automatic chessboard detection
- Board segmentation into 64 squares
- Camera calibration pipeline
- Board-state tracking through occupancy analysis
- Stockfish integration
- Digital game visualization
- Finite State Machine (FSM) for system coordination

## Current Progress
- [x] Camera calibration
- [x] Board detection pipeline
- [x] Board segmentation into 64 squares
- [x] FSM architecture
- [x] Digital game visualizer
- [x] Stockfish integration
- [ ] Reliable move tracking
- [ ] Python ↔ Arduino communication
- [ ] Robotic arm construction

## Technical Challenges
- Chess board detection and occupancy classification without an empty-board calibration stage
- Reliable chess board and state detection under varying lighting conditions and camera angles
- Distinguishing valid moves from temporary occlusions
- Handling one-off squares, which typically get flagged due to shadows, reflections, or wood grain
- Synchronizing physical and digital game states

## Future Work
- Improve detection accuracy with custom-trained dataset

## Team
This project is being developed by:
- **Aasees Badesha** - Lead software development, computer vision, game-state management, and robotic control software
- **Zawar Gondal** - Mechanical design, hardware integration, robotic system development, and software implementation
