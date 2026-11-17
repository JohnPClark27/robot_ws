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

**Terminal 4: localization (required: publishes `odom → base_link` + `map → odom`)** — odom_cov_relay + mag_relay + Madgwick + local EKF + gps_cov_relay + navsat_transform + global EKF. RViz Fixed Frame: `map`
```bash
ros2 launch ugv_localization localization.launch.py
```
Changed `setup.py` / added a file / changed `ekf.yaml`? Rebuild first: `colcon build --symlink-install --packages-select ugv_localization && source install/setup.bash`

**Terminal 5: Nav2** (after localization; wait for `Managed nodes are active`). RViz: 2D Goal Pose to send a goal. No teleop while Nav2 drives
```bash
ros2 launch ugv_navigation navigation.launch.py
```

**Terminal 6: GPS waypoint route** (after Nav2 is active). Waypoints = `WAYPOINTS` list in the script
```bash
ros2 run ugv_navigation gps_waypoints.py
```
One GPS goal from the CLI, plus lat/lon ↔ map checks:
```bash
ros2 action send_goal /follow_gps_waypoints nav2_msgs/action/FollowGPSWaypoints "{gps_poses: [{position: {latitude: 40.515531, longitude: -85.655418, altitude: 0.0}}]}" --feedback
ros2 service call /fromLL robot_localization/srv/FromLL "{ll_point: {latitude: 40.515531, longitude: -85.655477, altitude: 0.0}}"
ros2 service call /toLL robot_localization/srv/ToLL "{map_point: {x: 0.0, y: 0.0, z: 0.0}}"
```

### ugv: Nav2 checks

```bash
ros2 node list | grep -E "ekf|navsat"                 # localization running? (Nav2 needs odom + map TF)
ros2 run tf2_ros tf2_echo map base_footprint          # full TF chain OK?
ros2 run tf2_ros tf2_echo base_footprint base_link    # fixed 0.15 m
grep -n "base_link\|base_footprint" /ws/src/ugv_navigation/config/nav2_params.yaml   # robot frame settings
```
RViz displays: Path `/plan`, Map `/local_costmap/costmap`, Map `/global_costmap/costmap`, LaserScan `/scan_curb` (size 0.03).

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

### ugv: localization checks

```bash
ros2 node list                                  # ekf_filter_node, imu_filter_madgwick, mag_relay, odom_cov_relay
ros2 daemon stop                                # node list empty while things run? stale daemon; then list again (twice)
ros2 topic echo /odom --once --field twist.covariance        # Gazebo: all 0
ros2 topic echo /wheel/odom --once --field twist.covariance  # relay: diagonal at 0, 7, 14, 21, 28, 35
ros2 topic echo /odometry/filtered --once --field pose.pose.position   # EKF output
ros2 run tf2_ros tf2_echo odom base_link        # robot pose, RPY in degrees (yaw ≈ -9.3 at spawn = declination)
ros2 topic info /tf --verbose | grep -E "Node name|Publisher count"   # who publishes TF
ros2 topic echo /mag --once --field magnetic_field       # gz raw: gauss, NED-ish
ros2 topic echo /imu/mag --once --field magnetic_field   # mag_relay: tesla, ENU (spawn ≈ -3.2e-06, 1.98e-05, -4.82e-05)
ros2 topic hz /imu/data --window 50                      # Madgwick output, ~50 Hz
ros2 topic echo /imu/data --once --field orientation     # quaternion; yaw = 2*asin(z) when level
ros2 topic echo /imu/data --once --field orientation_covariance   # 0.0025 diagonal
ros2 topic list | grep imu                      # which IMU topics actually exist
ros2 pkg prefix imu_filter_madgwick             # /opt/ros/jazzy = apt package, /ws/install = mine
python3 -c "import math; print(math.degrees(2*math.asin(-0.0813)))"   # quaternion z -> yaw (deg)
python3 -c "import math; print(math.degrees(math.atan2(-3.2, 19.8)))" # angle of an (x, y) arrow
gz model -m ugv -p                              # ground truth pose from Gazebo (world frame, yaw in rad)
ros2 topic echo /gps/fix --once --field latitude && ros2 topic echo /gps/fix --once --field longitude   # spawn ≈ 40.5155310, -85.6554788
xacro src/ugv_description/urdf/ugv.urdf.xacro | grep -A4 "<horizontal>" | head -5   # GPS noise stddev in DEGREES (~1.8e-07)
ros2 topic echo /odometry/gps --once --field pose.pose.position   # navsat_transform output, ≈ (0, 0) at start
ros2 topic info /imu/data --verbose | grep -E "Node name|Publisher count"   # want 1: imu_filter_madgwick
ros2 topic echo /imu/data --field orientation.z                   # start BEFORE relaunching localization to see first msgs
ros2 node info /navsat_transform                                  # real subscribed topic names (it reads `imu`, not `imu/data`!)
ros2 topic echo /odometry/gps --once --field pose.covariance      # 0.0004 at 0 and 7 (gps_cov_relay working)
ros2 run tf2_ros tf2_echo map odom                                # global EKF correction; drifts as wheel odom drifts
ros2 topic echo /odometry/global --field pose.pose.position       # global EKF; at rest should move only mm
```
navsat startup log: `Transform heading factor is now F` → captured raw IMU yaw = F − 0.1758 (declination + convergence). Should match the robot's magnetic yaw at that moment, not 0. Good value at spawn: factor ≈ 0.015 (raw ≈ −0.161).

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
