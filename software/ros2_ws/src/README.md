# IN PROGRESS: Wrapping code in ROS2
As the project expands, it's important to keep the code modular and easily legible.
The core application logic in `software/core/` is separated from the ROS 2 communication layer.


## Packages
- `chess_interfaces`: Custom message, service, and action definitions.
- `chess_nodes`: Wrapper nodes acting as an adapter layer that translates ROS 2 messages into calls to software/core/.

## Why this structure?
- `software/core/` has zero ROS dependencies, so it remains easy to test and run outside of an ROS environment.
- Separating the program into dedicated nodes, each with a single job, isolates failures and is easier to understand.
- This adapter layer adds a level of abstraction between the software and hardware. Drivers, webcams, simulated inputs can be swapped/mocked easily within ROS, without touching the chess logic (e.g. switching between images, video streams, and live feed).
- Standard ROS tools make it easier to inspect the flow of data.

## Difficulties
- ROS nodes must run either on a Linux PC, VM, or Docker container.
- Docker on Mac can't pass a webcam or USB serial in, so those have to run outside the container.

## Build
Run from `software/ros2_ws/`:

    colcon build
    source install/setup.bash