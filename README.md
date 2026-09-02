# ARGM — Artificial Robotic GrandMaster

## Overview
An autonomous chess-playing robot that combines computer vision, state estimation, and robotic manipulation to detect human moves, interface with the Stockfish chess engine, and execute physical responses using a custom robotic arm.
> **Current Status:** The system is successfully detects board state, tracks physical moves, and visualizes gameplay in real time.

## How It Works
1. **Feed Capture:** A camera captures the chessboard in its initial state
2. **Board Detection:** A YOLO-assisted pipeline locates the board.
   If this fails, a manual calibration window prompts the user to input the chessboard corners
3. **Segmentation:** OpenCV applies a perspective warp and segments it into squares
4. **Move Inference:** The system analyzes square occupancy changes between consecutive frames to infer player moves
5. **Validation:** Moves are validated and tracked via software logic
6. **Engine Query:** Stockfish analyzes the state and generates a response move
7. **Execution:** The validated response move is transmitted to a custom robotic arm for physical execution

## Technologies & Concepts
- **Python** (NumPy, OpenCV, Ultralytics YOLO)
- **Arduino/C++**
- **Computer Vision** (Object detection and tracking)
- **Finite State Machines (FSM)** (System logic and control flow)

## Demo & Screenshots

### Board Detection & Segmentation
<img width="400" height="438" alt="Chess Board and Square Localization" src="https://github.com/user-attachments/assets/1ac860ec-5a66-41e0-ac07-b7a1ec556efe" />

*Automatic board localization using YOLO-assisted detection and OpenCV preprocessing.*

The pipeline extracts the chessboard from the camera feed, applies a perspective warp, and generates a stable 8×8 grid for gameplay.

### Occupancy Detection
<img width="400" height="332" alt="Manual Calibration and Occupancy Detection" src="https://github.com/user-attachments/assets/87d4be65-9997-4b52-bdf4-a6e7a2ac9360" />

*A manual calibration fallback is used when automatic detection fails and for testing under controlled conditions.*

After calibration, the board is split into an 64 individual squares. Each square is classified as occupied or empty using a learned empty-square profile.
Square cropping is intentionally tight to improve per-square classification consistency.

### Digital Visualizer
<img width="400" height="422" alt="Digital Chess Game Visualizer" src="https://github.com/user-attachments/assets/bc8d921f-1aa7-483a-a2b2-34497dbc55eb" />

*Mirrors the physical game state, replaying moves as they are detected and validated by the system.*

It serves as a core debugging tool for board-state tracking and Stockfish integration, featuring:
- Real-time board rendering from a `python-chess` state object
- Smooth piece animations for moves
- Tight synchronization with engine-generated and human-detected moves
- Frame-based animation loop for seamless transitions

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

## Features & Capabilities
- **Automated Setup:** Automatic chessboard localization and segmentation.- **State Tracking:** Real-time board-state tracking via occupancy and color analysis.
- **Engine Integration:** Full integration with the Stockfish chess engine.- **Live UI:** Interactive digital visualizer for debugging and game mirroring.
- **Robust Logic:** Centralized Finite State Machine (FSM) for system coordination.

## Current Progress
- [x] Camera calibration
- [x] Board detection pipeline
- [x] Board segmentation into 64 squares
- [x] FSM architecture
- [x] Digital game visualizer
- [x] Stockfish integration
- [X] Reliable move tracking
- [ ] Python ↔ Arduino communication
- [ ] Robotic arm construction

## Technical Challenges
- **Dynamic Lighting:** Maintaining reliable board detection and state tracking under varying lighting conditions, wood grain reflections, and severe camera angles.
- **Occlusion Handling:** Distinguishing between valid completed moves and temporary hand/arm occlusions during gameplay.
- **Shadow Mitigation:** Eliminating false positive occupancy flags caused by shadows cast by pieces onto adjacent squares.
- **Move Tracking:** Tracking moves captures and promotions using the occupancy-first approach.
- **Physical Syncing:** Eliminating the mandatory empty-board calibration step to allow system initialization mid-game.
- Chess board detection and occupancy classification without an empty-board calibration stage
- Reliable chess board and state detection under varying lighting conditions and camera angles
- Distinguishing valid moves from temporary occlusions
- Handling one-off squares, which typically get flagged due to shadows, reflections, or wood grain
- Synchronizing physical and digital game states

## Future Work
- Eliminate the empty-board calibration requirement
- Support full piece-type classification directly from camera input
- Migrate software architecture to **ROS 2** for scalable robot integration
- Improve detection accuracy under varying lighting and camera angles

## Team
This project is being developed by:
- **Aasees Badesha** - Lead software development, computer vision, game-state management, and robotic control software
- **Zawar Gondal** - Mechanical design, hardware integration, robotic system development, and software implementation
