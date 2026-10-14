# robot_ws — ROS 2 Jazzy + Gazebo + Nav2 dev environment
# Build from repo root:  docker build -f docker/Dockerfile -t robot_ws .

# Layer 1: base image (Ubuntu 24.04 + ROS 2 Jazzy + RViz + Gazebo)
FROM osrf/ros:jazzy-desktop-full

# Layer 2: build settings
ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

# Layer 3: extra packages
RUN apt-get update && apt-get install -y \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-robot-localization \
    ros-jazzy-ros-gz \
    git \
    python3-vcstool \
    nano \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Layer 4: install dependencies declared in your packages' package.xml files
COPY src /tmp/src
RUN apt-get update && \
    rosdep update --rosdistro jazzy && \
    rosdep install --from-paths /tmp/src --ignore-src -y --rosdistro jazzy && \
    rm -rf /tmp/src /var/lib/apt/lists/*

# Layer 5: non-root user (reuse built-in 'ubuntu' user, UID 1000)
RUN echo "ubuntu ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ubuntu && \
    chmod 0440 /etc/sudoers.d/ubuntu
USER ubuntu

# Layer 6: workspace + auto-source ROS in every shell
WORKDIR /ws
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc && \
    echo "[ -f /ws/install/setup.bash ] && source /ws/install/setup.bash" >> ~/.bashrc

CMD ["bash"]