# Running ROS 2 in Docker

ROS 2 only installs on Linux, so on a Mac the nodes run inside a Docker container.
Only the nodes in `software/ros2_ws/` need it. The rest of the project (`software/core/`) runs natively on your Mac.

## How it fits together

| Piece | What it is |
|-------|-----------|
| **Image** (`Dockerfile`) | Linux + ROS 2 Jazzy + Stockfish + the pip packages from `software/core/requirements.txt`. Built once. |
| **Container** (`ros2`) | A running copy of the image. Disposable. |
| **Volume mount** | `docker-compose.yml` maps the whole repo to `/ws` inside the container. You edit on your Mac and the container sees the change instantly. Nothing is copied in. |
| **`PYTHONPATH`** | `docker-compose.yml` sets `PYTHONPATH=/ws/software/core`. This is how the nodes resolve `from src.logic... import ...`: Python finds `/ws/software/core/src/`, even though it sits outside the ROS workspace. |
| **`colcon build`** | Builds only the ROS packages in `software/ros2_ws/src/` (`chess_interfaces`, `chess_nodes`). Writes `build/`, `install/`, `log/` (gitignored, safe to delete). |
| **`source install/setup.bash`** | Tells the current shell where the built packages are. Every new shell needs it. |

Your prompt shows where you are: `root@...:/ws#` is inside the container. Anything else is your Mac, where `ros2` does not exist (`command not found: ros2`).

## Start and stop

Run from the repo root on your Mac. Docker Desktop must be running first (`open -a Docker`; check with `docker info`).

1. Start the container in the background (once per session; the first run builds the image and takes a few minutes):

   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```

2. Open a shell in it (once per terminal you want):

   ```bash
   docker exec -it ros2 bash
   ```

3. Inside each shell, load the workspace:

   ```bash
   cd /ws/software/ros2_ws && source install/setup.bash
   ```

   The first time, or after editing a `.msg` file or `setup.py`, build first:

   ```bash
   cd /ws/software/ros2_ws && colcon build --symlink-install && source install/setup.bash
   ```

4. Leave a shell with `exit`. This only closes that shell; the container keeps running.

5. When you are done for the day, stop and remove the container:

   ```bash
   docker compose -f docker/docker-compose.yml down
   ```

## Run the nodes

Use three terminals. Each one: `docker exec -it ros2 bash`, then `cd /ws/software/ros2_ws && source install/setup.bash`, then:

| Terminal | Command |
|----------|---------|
| 1 | `ros2 run chess_nodes planner_node` |
| 2 | `ros2 run chess_nodes arm_node` |
| 3 | the test publisher below |

Send a test move (white pawn takes on d5):

```bash
ros2 topic pub --once game/engine_move chess_interfaces/msg/EngineMove "{fen: 'rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2', uci_move: 'e4d5'}"
```

Expected output:

- planner: `e4d5: d5->bin, e4->d5`
- arm node: `step 1/2: d5 -> bin`, `step 2/2: e4 -> d5`, then `done e4d5` on `arm/status`

Handy inspection commands (any shell with the workspace sourced):

```bash
ros2 node list
ros2 topic list
ros2 topic echo arm/steps
ros2 topic echo arm/status
ros2 interface show chess_interfaces/msg/EngineMove
```

## When to rebuild

- Edited a node `.py` file: just restart the node (`--symlink-install` makes edits apply without rebuilding).
- Edited a `.msg` file or `setup.py`: `colcon build --symlink-install`, then `source install/setup.bash`.
- Edited `docker/Dockerfile` or `software/core/requirements.txt`: rebuild the image.

  ```bash
  docker compose -f docker/docker-compose.yml build
  ```

- Something odd in ROS: delete `software/ros2_ws/build install log` and rebuild.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Cannot connect to the Docker daemon` | Docker is not running | `open -a Docker`, wait, then `docker info` |
| `command not found: ros2` | You are in your Mac shell | `docker exec -it ros2 bash` |
| `container ... is not running` | The container exited or is stale | `docker rm -f ros2`, then `up -d` again |
| `No such file ... install/setup.bash` | Workspace not built | `colcon build --symlink-install` |
| `Package 'chess_nodes' not found` | Workspace not sourced in this shell | `source install/setup.bash` |
| `No module named 'src'` | `PYTHONPATH` not set | `echo $PYTHONPATH` should print `/ws/software/core`; start the container with compose, not plain `docker run` |
| `No module named 'chess'` | Image is out of date | rebuild the image |
| Test move gets no reaction | Nodes were not ready yet, or are in different containers | wait a few seconds and publish again; `docker ps` should list one `ros2` container |

## Cleaning up containers

List everything, running and stopped:

```bash
docker ps -a
```

Remove one container by name (also stops it if it is running):

```bash
docker rm -f <container-name>
```

Remove all stopped containers (asks for confirmation):

```bash
docker container prune
```

Do not use `docker compose run`. It creates a new throwaway container named `docker-ros2-run-...` every time. Use `up -d` plus `exec` instead.

## Limits

Docker on macOS cannot pass USB or serial devices into a container, so the real Arduino cannot be used from here. That is why `arm_node` defaults to `dry_run=True`. For hardware, run the node on a Linux machine or Raspberry Pi, or use `software/core/src/hardware/robot.py` natively.
