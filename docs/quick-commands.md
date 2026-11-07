# Quick commands

Copy-paste cheat sheet. Explanations: [gazebo-basics-log.md](gazebo-basics-log.md), progress: [session-resume.md](session-resume.md).

## Start the container (host, repo root)

```bash
docker compose run --rm ros
```

## Extra terminals into the same container (host)

```bash
docker exec -it $(docker ps -q --filter ancestor=robot_ws | head -1) bash
```

Then in every exec shell: `source install/setup.bash`.

## My robot (`ugv`): sim + RViz + teleop, 3 terminals

New container? Build first (Terminal 1, `/ws`):
```bash
colcon build --symlink-install && source install/setup.bash
```

**Terminal 1: Gazebo + robot_state_publisher + spawn + bridge**
```bash
ros2 launch ugv_description sim.launch.py
```

**Terminal 2: RViz with saved config, on sim time**
```bash
rviz2 -d $(ros2 pkg prefix ugv_description)/share/ugv_description/rviz/ugv.rviz --ros-args -p use_sim_time:=true
```

**Terminal 3: keyboard teleop** (no remap needed: everything is on `/cmd_vel`)
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

RViz only (no Gazebo, fake joint angles):
```bash
ros2 launch ugv_description display.launch.py
```

### ugv: check the Gazebo side (before blaming the bridge)

```bash
gz topic -l | grep -E "cmd_vel|odom|joint|tf"
gz topic -i -t /model/ugv/tf                    # message type of a gz topic
gz topic -e -t /joint_states -n 1 | grep -E 'name: ".*_joint"|position:'
gz topic -t /cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.3}'
gz topic -t /cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.0}'   # stop
```

### ugv: check the ROS side

```bash
ros2 topic list                                 # /clock /cmd_vel /imu /joint_states /odom /tf ...
ros2 topic info /tf
ros2 topic echo /tf --once                      # odom -> base_link, wheel frames
ros2 topic echo /tf_static --once               # base_link -> imu_link (fixed joints)
ros2 topic echo /imu --field linear_acceleration   # z ≈ 9.8 ± noise
ros2 topic echo /imu --once --field linear_acceleration_covariance
xacro src/ugv_description/urdf/ugv.urdf.xacro | grep -A14 "<gazebo>"   # expanded ${ } values
xacro src/ugv_description/urdf/ugv.urdf.xacro > /dev/null   # parse check: no output = OK
ros2 run tf2_ros tf2_echo base_link lidar_link  # fixed-joint offset (z 0.12)
ros2 topic hz /scan --window 50                 # ~10 Hz (lower if RTF < 1)
ros2 topic echo /scan --once --field ranges | head -5
ros2 topic hz /front_cam/image_raw --window 50  # ~15 Hz requested, ~11 at RTF 0.8
ros2 topic echo /front_cam/image_raw --once --field header   # frame_id: front_cam_optical_link
ros2 topic info /front_cam/image_raw --verbose  # subscribers + QoS (RViz "No Image" debugging)
gz topic -l | grep -E "scan|cam"                # gz-side sensor topics
```

## Old: `vehicle_blue` (diff_drive.sdf) + TF in RViz: 4 terminals

**Terminal 1: simulator**
```bash
gz sim -r diff_drive.sdf
```

**Terminal 2: bridge (clock + cmd_vel + odometry + TF)**
```bash
ros2 run ros_gz_bridge parameter_bridge \
  /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock \
  /model/vehicle_blue/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist \
  /model/vehicle_blue/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry \
  /model/vehicle_blue/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V \
  --ros-args -r /model/vehicle_blue/tf:=/tf
```

**Terminal 3: RViz on sim time**
```bash
rviz2 --ros-args -p use_sim_time:=true
```
Then: Fixed Frame → `vehicle_blue/odom` (press Enter), Add → TF, tick Show Names.

**Terminal 4: keyboard teleop** (keep this terminal focused)
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
ros2 topic info /tf                             # want 1 publisher (the bridge)
ros2 topic echo /tf --once                      # TF data arriving?
ros2 topic echo /clock --once                   # sim time arriving?
```

## Other

```bash
gz sim shapes.sdf                               # simple test world
ros2 run ros_gz_bridge parameter_bridge /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock
rviz2
```

Bridge direction: `[` Gazebo→ROS, `]` ROS→Gazebo, `@` both.
