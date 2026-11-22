# IN PROGRESS: Code migration to ROS2
- Separates program into nodes, each with a single job
- Makes it easy to both test program as well as integrate the driver and serial communication

Difficulties: 
- Anything ROS related must run either on a Linux PC, VM, or Docker container.
- Docker on Mac can't pass a webcam in