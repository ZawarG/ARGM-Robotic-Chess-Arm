# Package: Chess Nodes
Holds the nodes, which are wrappers around the Python code in `software/core/`. 
Each node reads a message, calls a core function, and sends the result. The chess logic itself stays in core, which never imports ROS.

## Layout
- `setup.py` registers node names under `entry_points`
- `chess_nodes/` holds the nodes (.py files)

Not every .py file is a node. A node needs a `Node` class and a line in `entry_points`.

## Nodes
- `planner_node`: reads `EngineMove`, sends `ArmPlan`
- `arm_node`: reads `ArmPlan`, moves the arm (dry run for now)

## Run
    ros2 run chess_nodes planner_node