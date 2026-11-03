# Next steps

A short, ordered checklist. Write the code yourself; use AI to explain concepts, give hints,
review diffs and decode errors. Tick a box (`[x]`) when its "done when" is true.

Why ROS comes later: the ROS chain ends at `arm_node`, which drives a stub serial driver and
firmware that doesn't compile yet. Make the arm real first; ROS is easier once it can move.

## Step 0 – Get ROS unstuck, then park it (1 evening, no code)

Follow "Everyday commands" in [ros2-and-docker.md](ros2-and-docker.md).

- [X] `docker compose run --rm ros2 bash` opens a shell in the container
- [X] `colcon build --symlink-install` succeeds, then `source install/setup.bash`
- [X] `planner_node` and `arm_node` both run (one terminal each)
- [X] Send the test move with `ros2 topic pub --once game/engine_move ...`
- [X] **Done when:** `arm_node` logs `step 1/2: d5 -> bin` and `step 2/2: e4 -> d5`
- [X] Commit `docs/ros2-and-docker.md`

## Step 1 – Warm-up bug fixes (1–2 evenings, one small commit each)

- [X] Firmware: `LED_BUILT_IN` → `LED_BUILTIN` (`firmware/arm_firmware.ino`)
- [X] Winner label is inverted (`core/src/logic/chess_board.py` ~204-207)
- [X] `close()` called twice (`chess_board.py` ~200 and `core/main.py`)
- [X] Hardcoded Stockfish path breaks in Docker (hint: `shutil.which`)
- [X] Non-ROS path sends square ints (`12`) instead of names (`e2`) (`core/src/hardware/robot.py` ~32)

## Step 2 – First tests (1 evening)

`pytest` tests for `decompose()` in `core/src/logic/move_decomposition.py`.

- [X] Normal move
- [X] Capture
- [X] Castling (both sides)
- [X] En passant
- [X] Promotion
- [X] **Done when:** `pytest` passes and you fixed or noted any bug the tests found

## Step 3 – Protocol spec (1 session, writing only)

Write `docs/protocol.md` in your own words from §4 of the plan (`argm-plan.md`).

- [ ] Frame layout: version, seq, type, len, payload, crc16
- [ ] Message table and error codes
- [ ] Reliability rules: ACK timeout, retries, seq dedup, ACK vs DONE
- [ ] 2–3 example frames worked out by hand (COBS on paper, CRC via an online calculator)
- [ ] **Done when:** you can explain every byte of a frame to someone else

## Step 4 – Rust driver `argm-link` (M1)

If Rust is new, read *The Rust Book* chapters 1–9 first.

- [ ] Hand-written COBS encode/decode, tested against your example frames
- [ ] CRC-16/CCITT-FALSE with the `crc` crate
- [ ] Frame header pack/unpack
- [ ] `MockTransport` (fake firmware that can drop/corrupt/delay frames)
- [ ] `Link`: send → wait for ACK → retry → typed errors
- [ ] Tests: happy path, CRC error then retry, 3 timeouts → `Timeout`, duplicate ACK, resync after garbage
- [ ] Small `clap` CLI (`argm-link --port ... ping`)

## Decide before M2/M3

- [ ] Actuators: steppers, servos, or DC motors + encoders?
- [ ] Microcontroller: Uno, or bigger (ESP32/Teensy)?
- [ ] Hardware host: Mac + Docker, or a Linux box / Raspberry Pi?

## Later (see `argm-plan.md`)

- [ ] M2 – Non-blocking C++ firmware: protocol, state machine, e-stop
- [ ] M3 – Motion: homing, trapezoidal profiles
- [ ] M4 – Inverse kinematics + board calibration
- [ ] M5 – Back to ROS: `game_node` first (no camera), then `vision_node`, then a launch file
- [ ] M6 – Benchmarks · M7 – CI · M8 – URDF + RViz
