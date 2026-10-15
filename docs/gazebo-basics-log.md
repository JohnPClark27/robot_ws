# Gazebo + ROS 2 basics: what I ran and why

Log of the first simulation session. Everything runs **inside the container** unless noted.
Each step builds on the previous one.

## Key concepts

| Term | Meaning |
|---|---|
| Topic | Named channel nodes publish to / subscribe from |
| Gazebo topics vs ROS topics | Two separate messaging systems. They don't see each other without a bridge |
| `ros_gz_bridge` | Node that translates messages between Gazebo and ROS 2 topics |
| Twist | Velocity message: `linear` (m/s) + `angular` (rad/s) |
| Differential drive | Two independently driven wheels; steer by speed difference |
| Odometry | Robot's own position/velocity estimate from wheel motion |
| Remap (`-r a:=b`) | Redirect a node's topic name without changing its code |

## Step 0: Build and enter the container (host, from repo root)

```bash
docker compose build
docker compose run --rm ros
```

Open extra terminals into the same running container from another host shell:

```bash
docker ps                     # find the container name
docker exec -it <name> bash
```

## Step 1: First world

```bash
gz sim shapes.sdf
```

- Opens Gazebo Harmonic via WSLg. Starts **paused**; press play (bottom left).
- Orbit: middle mouse. Zoom: scroll.

## Step 2: Gazebo topics vs ROS topics

```bash
gz topic -l                   # Gazebo topics (/clock, /stats, /world/shapes/...)
gz topic -e -t /stats         # echo sim time / real-time factor
ros2 topic list               # only /parameter_events and /rosout, no bridge yet
```

**Learned:** the two lists differ because they are separate systems.

## Step 3: Bridge `/clock`

```bash
ros2 run ros_gz_bridge parameter_bridge /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock
ros2 topic echo /clock
```

Bridge syntax: `topic@ros_type<dir>gz_type`

| Char | Direction |
|---|---|
| `[` | Gazebo → ROS |
| `]` | ROS → Gazebo |
| `@` | both ways |

`/clock` is Gazebo → ROS, so `[`. Sim time freezes when Gazebo is paused.

## Step 4: Drive a robot from Gazebo's side

```bash
gz sim -r diff_drive.sdf      # -r = start running
gz topic -l | grep -i vehicle # find cmd_vel
gz topic -t /model/vehicle_blue/cmd_vel -m gz.msgs.Twist \
  -p 'linear: {x: 0.5}, angular: {z: 0.3}'
```

**Learned:** constant `v` and `ω` trace a circle of radius `v/ω` (0.5/0.3 ≈ 1.67 m).
Straight line: `angular.z = 0`. Spin in place: `linear.x = 0`.

## Step 5: Drive from ROS 2

```bash
ros2 run ros_gz_bridge parameter_bridge \
  /model/vehicle_blue/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist

ros2 topic pub --once /model/vehicle_blue/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5}, angular: {z: 0.0}}"
```

**Learned:** the DiffDrive plugin has **no timeout**. It keeps the last velocity until it gets a new one,
so the robot rolls away after a single `--once`. Stop it with a zero Twist.
Real hardware needs a **watchdog** that stops the motors when commands stop arriving (relevant for the ESP32 phase).

## Step 6: Keyboard teleop

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/model/vehicle_blue/cmd_vel
```

Keys: `i` forward, `j`/`l` turn, `k` stop. `q`/`z` scale speeds by 10% per press.

## Step 7: Odometry

```bash
gz topic -l | grep -i odom
ros2 run ros_gz_bridge parameter_bridge \
  /model/vehicle_blue/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist \
  /model/vehicle_blue/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry
ros2 topic echo /model/vehicle_blue/odometry --field pose.pose.position
```

Multiple bridged topics go in one command, space-separated.

## Debugging I did (reusable)

Trace the chain: **teleop → ROS topic → bridge → Gazebo topic → plugin**.

```bash
ros2 node list
ros2 node info /teleop_twist_keyboard    # check Publishers: topic name
ros2 topic info /model/vehicle_blue/cmd_vel   # publisher / subscription counts
ros2 topic echo /model/vehicle_blue/cmd_vel
gz topic -e -t /model/vehicle_blue/cmd_vel
```

| Symptom | Cause |
|---|---|
| Publisher count 0 | Teleop not running, or remap not applied |
| Subscription count 0 | Bridge not running |
| "not published yet" | Typo in topic name (`vehile_blue`) |
| Robot doesn't move, teleop speed ~1583 | Speed keys pressed too often; restart teleop and reset the sim |
| Teleop ignores keys | Its terminal must have keyboard focus |

## Docs

- [Gazebo Harmonic getting started](https://gazebosim.org/docs/harmonic/getstarted/)
- [Gazebo ↔ ROS 2 integration](https://gazebosim.org/docs/harmonic/ros2_integration/)
- [ROS 2 topics tutorial](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Topics/Understanding-ROS2-Topics.html)
- [nav_msgs/Odometry](https://docs.ros.org/en/jazzy/p/nav_msgs/interfaces/msg/Odometry.html)
