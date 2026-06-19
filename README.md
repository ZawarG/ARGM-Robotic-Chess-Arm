# ARGM — Artificial Robotic GrandMaster

## Overview
A robotic chess system that detects board state from a camera feed, tracks moves through square occupancy changes, interfaces with a chess engine, and ultimately controls a robotic arm to execute physical moves.

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

### Digital Visualizer
<img width="400" height="422" alt="Digital Chess Game Visualizer" src="https://github.com/user-attachments/assets/bc8d921f-1aa7-483a-a2b2-34497dbc55eb" />

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
