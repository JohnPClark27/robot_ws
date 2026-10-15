# Quick commands

Copy-paste cheat sheet for getting the diff-drive sim running. Explanations: [gazebo-basics-log.md](gazebo-basics-log.md).

## Start the container (host, repo root)

```bash
docker compose run --rm ros
```

## Extra terminals into the same container (host)

```bash
docker exec -it $(docker ps -q --filter ancestor=robot_ws | head -1) bash
```

## Drive the robot: 3 terminals

**Terminal 1: simulator**
```bash
gz sim -r diff_drive.sdf
```

**Terminal 2: bridge (cmd_vel + odometry)**
```bash
ros2 run ros_gz_bridge parameter_bridge \
  /model/vehicle_blue/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist \
  /model/vehicle_blue/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry
```

**Terminal 3: keyboard teleop** (keep this terminal focused)
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/model/vehicle_blue/cmd_vel
```

Keys: `i` forward, `j`/`l` turn, `k` stop. Avoid `q`/`z` (they scale speed).

## Inspect

```bash
ros2 topic echo /model/vehicle_blue/odometry --field pose.pose.position
ros2 topic list
gz topic -l
gz topic -e -t /stats
```

## Stop the robot

```bash
ros2 topic pub --once /model/vehicle_blue/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

## Debug checklist

```bash
ros2 node list
ros2 node info /teleop_twist_keyboard
ros2 topic info /model/vehicle_blue/cmd_vel     # want 1 publisher, 1 subscriber
gz topic -e -t /model/vehicle_blue/cmd_vel      # do commands reach Gazebo?
```

## Other

```bash
gz sim shapes.sdf                               # simple test world
ros2 run ros_gz_bridge parameter_bridge /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock
rviz2
```

Bridge direction: `[` Gazebo→ROS, `]` ROS→Gazebo, `@` both.
