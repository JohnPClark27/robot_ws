# Session resume notes

Written 2026-10-15 so work can continue on another computer. Updated 2026-10-21 (new machine).
Related: [roadmap.md](roadmap.md) (end goal + plan), [gazebo-basics-log.md](gazebo-basics-log.md) (full command log), [quick-commands.md](quick-commands.md) (cheat sheet).

## Where I am

Working through Gazebo Harmonic + ROS 2 Jazzy basics in the Docker container.
**Step 9 (IMU) is done.** Next: **Step 10, tracked skid-steer robot** (2 treads, 2 motors per tread; approximate treads as wheels per side in sim) as a ROS package + URDF/xacro (placeholder dimensions), then move the IMU onto it. See [roadmap.md](roadmap.md).

## Completed

- [x] Built the image and entered the container (`docker compose build`, `docker compose run --rm ros`)
- [x] Launched `gz sim shapes.sdf` (GUI works through WSLg)
- [x] Compared Gazebo topics (`gz topic -l`) vs ROS topics (`ros2 topic list`): separate systems
- [x] Bridged `/clock` with `ros_gz_bridge`; sim time visible in ROS
- [x] Launched `diff_drive.sdf`; drove the robot from `gz topic` (circle = v/ω)
- [x] Bridged `cmd_vel` ROS → Gazebo, published with `ros2 topic pub`
  - Learned: no timeout, robot keeps last velocity. Real hardware needs a watchdog
- [x] Drove with `teleop_twist_keyboard` and a remap
  - Debugged: publisher/subscriber counts, topic typo, runaway teleop speed
- [x] Bridged odometry (`nav_msgs/Odometry`) and echoed position while driving
- [x] Wrote docs in `docs/`
- [x] Step 8: TF in RViz. Chassis frame moves with the robot, odom frame stays fixed
  - Debug path: `gz topic -e` on `/model/vehicle_blue/tf` → `ros2 topic info /tf` (1 publisher) → `ros2 topic echo /tf --once`
  - Fix 1: Fixed Frame was still `map` (doesn't exist yet). Set it to `vehicle_blue/odom`
  - Fix 2: TF is stamped with sim time, so bridge `/clock` and run RViz with `use_sim_time:=true`
- [x] Step 9: IMU on `vehicle_blue`, in my own world copy `src/robot_sim/worlds/diff_drive_imu.sdf`
  - Source: `/opt/ros/jazzy/opt/gz_sim_vendor/share/gz/gz-sim8/worlds/diff_drive.sdf`
  - Two pieces: `gz-sim-imu-system` plugin at world level + `<sensor type="imu">` in the chassis link (50 Hz, topic `imu`)
  - Checked while driving a circle (v=0.5, ω=0.3): `angular_velocity.z` = 0.3, `linear_acceleration.y` = 0.15 (v·ω, centripetal), `linear_acceleration.z` = 9.8 (gravity)
  - Bridged: `/imu@sensor_msgs/msg/Imu[gz.msgs.IMU`, `ros2 topic hz /imu` ≈ 49 Hz (wall clock; sim real-time factor slightly < 1)
  - To fix later: covariances are all 0 (add `<noise>`), `frame_id` is Gazebo-style `vehicle_blue::chassis::imu_sensor` (needs a real TF frame like `imu_link`)

## Frames (from `diff_drive.sdf`)

| Frame | Meaning |
|---|---|
| `vehicle_blue/odom` | Fixed start point of odometry. Use as RViz Fixed Frame |
| `vehicle_blue/chassis` | Robot body. Moves relative to odom |
| `map` | Not published yet. Comes later from localization / Nav2 |

## Resume on a new computer

1. Install Docker (see README), clone the repo, `docker compose build`.
2. Start the container and open 4 terminals (see [quick-commands.md](quick-commands.md)).
3. Launch `gz sim -r /ws/src/robot_sim/worlds/diff_drive_imu.sdf`, the bridge (with `/clock`, TF, and `/imu`), RViz on sim time, then teleop.
4. Continue with Step 10.

## Notes for the group demo (2026-10-22)

- Drivetrain changed: **tank treads**, one per side, each driven by 2 motors. See [roadmap.md](roadmap.md).
- Demo scope: robot + sensors (lidar, camera, IMU, GPS) visualized in RViz, **teleoperated**. No autonomous nav yet.
- Part 2 if time allows: rough 3D campus map from OpenStreetMap (separate from the robot).
- Show **screen recordings** (record on the faster machine); live demo on the slower laptop only if asked.

## Planned next steps

1. ~~Finish TF in RViz (Step 8).~~ Done.
2. ~~Step 9: IMU.~~ Done.
3. Step 10: first ROS package + tracked skid-steer URDF/xacro, spawned in Gazebo; move the IMU onto it. Then GPS.
4. Set up `robot_localization` to fuse GPS + IMU + odometry.
5. Bring up Nav2 against the simulated robot.
6. Later: Fusion 360 → URDF for the real robot, then custom PCBs / micro-ROS.

## Gotchas so far

- Bridge direction: `[` Gazebo→ROS, `]` ROS→Gazebo, `@` both.
- DiffDrive keeps the last command; stop with a zero Twist.
- Teleop speed keys `q`/`z` change speed 10% per press. Restart teleop to reset.
- Teleop only reads keys when its terminal has focus.
- Always check pub/sub counts with `ros2 topic info` before assuming the sim is broken.
- RViz Fixed Frame must be `vehicle_blue/odom` (not `map`, not `odom`). Pick it from the dropdown or type it and press Enter.
- Sim data is stamped with sim time: bridge `/clock` and run `rviz2 --ros-args -p use_sim_time:=true`.
- Check the prompt: `ubuntu@...:/ws$` = container, `jpcli@...` = host (no `ros2` there).
- `Permission denied` on a `.sdf` = forgot `cp`; bash tried to run the file. Read what the shell was doing before reaching for `sudo`.
- `QStandardPaths: wrong permissions on runtime directory /mnt/wslg/...` is a harmless WSLg warning. Don't chmod it.
- Files in `/ws/src` (container) = `src/` (host), via bind mount. Anything else in the container is gone after `--rm`.
