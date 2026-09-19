# ROS 2 Jazzy dev environment for the ARGM Robotic Chess Arm
# ros:jazzy is multi-arch (native arm64 on Apple Silicon); osrf/ros:*-desktop is amd64-only
FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive
# Ubuntu installs stockfish to /usr/games
ENV PATH="/usr/games:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-desktop \
        python3-pip \
        stockfish \
    && rm -rf /var/lib/apt/lists/*

# Project Python dependencies (Ubuntu 24.04 needs --break-system-packages for system pip)
COPY ["Chessboard Image Detection/requirements.txt", "/tmp/requirements.txt"]
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed -r /tmp/requirements.txt

# Source ROS automatically in every shell
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc

WORKDIR /ws
CMD ["bash"]
