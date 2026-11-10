# Session resume notes

Written 2026-10-15 so work can continue on another computer. Updated 2026-10-21 (new machine), 2026-10-23 (Step 10 progress), 2026-10-24 (ugv drivable, IMU on ugv), 2026-11-07 (lidar + 2 cameras), 2026-11-09 (world file, GPS, curb sensors, magnetometer: sim sensors complete), 2026-11-10 (Step 12 chunk A: local EKF).
Related: [roadmap.md](roadmap.md) (end goal + plan), [gazebo-basics-log.md](gazebo-basics-log.md) (full command log), [quick-commands.md](quick-commands.md) (cheat sheet).

## Where I am

Working through Gazebo Harmonic + ROS 2 Jazzy basics in the Docker container.
**Steps 10 + 11 done: sim sensors complete.** My own robot (`ugv_description` package) spawns in my own world (`worlds/test_world.sdf`, campus GPS origin, obstacles + a curb), drives with `teleop_twist_keyboard`, and shows up in RViz (saved config) on sim time.
Sensors on the ugv (all in `urdf/ugv_sensors.xacro`): IMU (`/imu`), magnetometer (`/mag`), 360° lidar (`/scan`), front + rear cameras (`/front_cam/image_raw`, `/rear_cam/image_raw`), GPS (`/gps/fix`), tilted curb lidar (`/scan_curb`), depth camera (`/depth_cam/points`, comparison only). Bump sensors moved to Phase 2 (firmware).
**Step 12 chunk A done (2026-11-10):** new `ugv_localization` package, local EKF fuses wheel odom + gyro and now owns `odom → base_link`. RViz robot matches Gazebo much better (not perfect: only rates fused, so drift still accumulates).
**Next: Step 12 chunk B**, starting with the magnetometer (gauss/NED → tesla/ENU), then `navsat_transform` + global EKF. See [Planned next steps](#planned-next-steps).

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
- [x] Rendering check (2026-10-23): `gz sim -r gpu_lidar_sensor.sdf` + GUI plugin "Visualize Lidar" shows rays hitting objects. GPU lidar works on this machine
- [x] Step 10 (partial, 2026-10-23): `ugv_description` package
  - Created with `ros2 pkg create ugv_description --build-type ament_cmake --license Apache-2.0`, deleted the C++ `include/` and `src/` folders, added `urdf/` + `launch/`
  - `CMakeLists.txt`: `install(DIRECTORY urdf launch DESTINATION share/${PROJECT_NAME})` so launch files can find them via `get_package_share_directory`
  - `package.xml` exec_depends: `robot_state_publisher`, `xacro`, `joint_state_publisher`, `ros_gz_sim`
  - `urdf/ugv.urdf.xacro`: `base_link` box + `track_wheel` macro called 6 times (3 per side). Each wheel = cylinder link + `continuous` joint, axis `0 1 0`, rotated `rpy="${pi/2} 0 0"` in visual, collision and inertial
  - `launch/display.launch.py`: robot_state_publisher + joint_state_publisher, for viewing in RViz (Fixed Frame `base_link`, add RobotModel on `/robot_description` + TF)
  - `launch/sim.launch.py`: robot_state_publisher (`use_sim_time: True`) + Gazebo (`gz_args: -r empty.sdf`) + `ros_gz_sim create -topic robot_description -name ugv -z 0.2`
  - Learned: wheel TF errors ("No transform from left_wheel_front") = nothing publishing `/joint_states`. robot_state_publisher needs joint angles for non-fixed joints
  - Learned: `ros2 run ... -p robot_description:="$(xacro ...)"` fails (the `-p` value is parsed as YAML). Use a launch file with `ParameterValue(Command(['xacro ', file]), value_type=str)`
- [x] Step 10 drivetrain (2026-10-24): drivable ugv
  - DiffDrive plugin in a `<gazebo>` block in the xacro: one `<left_joint>`/`<right_joint>` tag **per joint** (3 each), `wheel_separation = ${body_w+wheel_w}` (0.48, left-to-right wheel centers, not `wheel_x_spacing`), `wheel_radius = ${wheel_r}`
  - Set `<topic>cmd_vel</topic>`, `<odom_topic>odom</odom_topic>`, `<frame_id>odom</frame_id>`, `<child_frame_id>base_link</child_frame_id>`. Without `<topic>` it would be `/model/ugv/cmd_vel` and teleop would need a remap
  - JointStatePublisher plugin in a second `<gazebo>` block, `<topic>joint_states</topic>` (the name `robot_state_publisher` subscribes to). No `<joint_name>` = all joints. Replaces the `jsp` node in sim
  - Checked on the Gazebo side first: `gz topic -l`, `gz topic -e -t /joint_states -n 1`. Driving straight at 0.3 m/s: all 6 wheel angles equal and positive (~29.9 rad ≈ 3.0 m / 0.1 m radius)
  - Learned: joint angles show commanded wheel rotation, not real motion. Slip is invisible to wheel odometry, so it drifts (→ fuse IMU/GPS later)
  - `ros_gz_bridge` node in `sim.launch.py`: `/clock` `[`, `/cmd_vel` `]`, `/odom` `[`, `/joint_states` (`gz.msgs.Model`) `[`, `/model/ugv/tf` (`gz.msgs.Pose_V`) `[` with `remappings=[('/model/ugv/tf', '/tf')]`
  - Found the TF topic with `gz topic -l | grep tf`, its type with `gz topic -i -t /model/ugv/tf`
  - RViz config saved to `src/ugv_description/rviz/ugv.rviz` (Fixed Frame `odom`, RobotModel, TF), `rviz` added to `install(DIRECTORY ...)` in CMakeLists
  - Known quirk (see below): DiffDrive odom is 2D (z = 0), so `base_link` sits at ground level in RViz (robot looks half-sunk). Fix later with a `base_footprint` frame ([REP 105](https://www.ros.org/reps/rep-0105.html))

- [x] Step 10 IMU (2026-10-24): IMU on the ugv
  - `imu_link` (no geometry) + fixed `imu_joint` from `base_link`, `xyz="0 0 ${body_h/2}"` (top of the body). Fixed joints → `robot_state_publisher` publishes once on `/tf_static` (stamp 0 is normal)
  - `<gazebo reference="imu_link">` + `<sensor type="imu">`: `always_on 1`, `update_rate 50`, `topic imu`, `<gz_frame_id>imu_link</gz_frame_id>`
  - Why `gz_frame_id`: URDF→SDF merges fixed-joint links into the parent, so without it the frame_id isn't a real TF frame. Fixes the Step 9 to-do
  - `gz-sim-imu-system` / `gz::sim::systems::Imu` in a model-level `<gazebo>` block (works the same as world-level)
  - Bridge: `/imu@sensor_msgs/msg/Imu[gz.msgs.IMU`
  - Noise: `<imu><angular_velocity>` / `<linear_acceleration>` with `<x|y|z><noise type="gaussian">`, stddev 0.009 rad/s (gyro), 0.017 m/s² (accel). Placeholder cheap-MEMS values; replace with datasheet values
  - Result at rest: `frame_id: imu_link`, accel z ≈ 9.8 ± 0.02. Gazebo fills covariance = stddev² on the diagonal (0.000081 gyro, 0.000289 accel). **`orientation_covariance` stays all 0** (no orientation noise) → handle in `robot_localization` config (Step 12)

- [x] Sensors session (2026-11-07): lidar + cameras
  - Split sensors into `urdf/ugv_sensors.xacro`, pulled in with `<xacro:include filename="$(find ugv_description)/urdf/ugv_sensors.xacro"/>` just above `</robot>`. Included file needs its own `<robot xmlns:xacro=...>` root (no `name`). Properties from the main file still work (include = paste). **New file → `colcon build`** (symlink is only made for files that exist at build time)
  - **360° lidar:** `lidar_link` cylinder (r 0.028, h 0.04), fixed joint z = `body_h/2 + lidar_h/2` = 0.12 (checked with `ros2 run tf2_ros tf2_echo base_link lidar_link`)
    - `gpu_lidar` sensor: 500 samples (5000 samples/s ÷ 10 Hz, RPLIDAR C1), `${-pi}`..`${pi}`, range 0.05–12 m (min must clear the lidar's own radius), gaussian noise 0.01, `gz_frame_id lidar_link`, topic `scan`
    - Needs `gz-sim-sensors-system` (`render_engine ogre2`), shared by all rendering sensors (lidar, cameras, depth). Currently in a model-level `<gazebo>` block; move to the world file
    - Bridge `/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan`. RViz LaserScan display: red dots outline shapes
  - **Cameras:** `cam` xacro macro (params `name x y z yaw`), called for `front_cam` (x = `body_l/2 + 0.012/2`, yaw 0) and `rear_cam` (x mirrored, yaw `${pi}`), z = `body_h/2 - 0.024/2`
    - Two links per camera: `<name>_link` (x forward; Gazebo aims the camera along its +x, so `<gazebo reference>` points here) and `<name>_optical_link` (`rpy="${-pi/2} 0 ${-pi/2}"`, xyz 0: z forward, y down, [REP 103](https://www.ros.org/reps/rep-0103.html)). Image header uses the optical frame: `<gz_frame_id>${name}_optical_link</gz_frame_id>`
    - Pi Camera Module 3 Wide: `horizontal_fov` 1.780236 (102°), 640×360 (16:9), 15 Hz, clip 0.05–50 m, noise 0.007
    - Topics `<name>/image_raw`, CameraInfo auto-published next to it as `<name>/camera_info`. Bridge `sensor_msgs/msg/Image[gz.msgs.Image` and `sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo`
    - RViz: Add → By topic → Image display shows the camera view
  - Learned: a joint `<origin>` is relative to its **parent** link (optical joint = 0 offset from the camera link)
  - Learned: xacro macro params are like function args: placeholders `${x}` inside, real numbers at the call
  - Learned: the 4×4 TF matrix = 3×3 rotation + translation column; points are `[x, y, z, 1]`
  - Learned: RViz pose vs Gazebo pose drifts apart while driving = wheel-odometry drift (skid-steer slip, worst when turning). Expected; `robot_localization` fixes it in Step 12
  - Performance: RTF ≈ 0.81 with lidar + 2 cameras (RViz Time panel: ROS Elapsed ÷ Wall Elapsed), cameras ≈ 11 Hz by wall clock instead of 15

- [x] Sensors session 2 (2026-11-09): world file, GPS, curb sensors, magnetometer
  - **World file:** copied `empty.sdf` → `src/ugv_description/worlds/test_world.sdf`, added `worlds` to `install(DIRECTORY ...)` + rebuild, `sim.launch.py` builds `world_file` with `get_package_share_directory` and passes `'-r ' + world_file` to `gz_args`
    - `empty.sdf` loads 4 systems: Physics, UserCommands (needed by `ros_gz_sim create`), SceneBroadcaster, Contact. **No Sensors**
    - If a world lists any plugins, Gazebo loads only those (no defaults), so keep all 4 when adding more
    - Moved world-wide systems out of the robot into the world: Sensors (`render_engine ogre2`), Imu, later NavSat + Magnetometer. Rule: robot things in the URDF, things the world provides to everyone in the world file
    - Obstacles: static `box_1` (0.5 m cube at x 2), `cylinder_1` (r 0.25 at 3, 1), `curb` (0.5 × 10 × 0.2 m at x −3). Static models need collision + visual, no inertial; pose z = half the height
  - **Curb test:** the 360° lidar can't see the 0.20 m curb (scan plane ~0.27 m above ground). Confirms the need for a curb sensor
  - **GPS (Step 11):** `<spherical_coordinates>` in the world (EARTH_WGS84, ENU, lat 40.515531, lon −85.655477, elevation 260 m, heading 0) + `gz-sim-navsat-system`
    - `gps_link` on top, 0.15 m behind `base_link`; `navsat` sensor, 10 Hz, topic `gps/fix` (the name `navsat_transform` expects), bridge `/gps/fix@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat`
    - Noise via xacro props `gps_h_std` / `gps_v_std`: 0.02 / 0.04 m (RTK fixed, ZED-F9P class). Standard GPS = 2.0 / 4.0 m
    - 0.00001° latitude ≈ 1.1 m, but 0.00001° longitude ≈ 0.85 m here (× cos 40.5°)
    - RTK in reality drops to float (~0.3 m) / standard (~2 m) near buildings and trees. Gaussian noise doesn't model that, so tune fusion to survive standard GPS
    - No RViz display for NavSatFix: use rqt Topic Monitor now, `/odometry/gps` from `navsat_transform` in Step 12, Foxglove Map panel for the demo (later)
  - **Curb sensors (both simulated, tilted lidar chosen for cost, see roadmap):**
    - Depth camera (D435-like): `depth_cam_link` on the front face below the lidar plane, pitched 30° down (positive pitch = down), `depth_camera` sensor 320×240, HFOV 87°, clip 0.28–5 m, 10 Hz, `gz_frame_id depth_cam_link`. One `<topic>` gives 2 gz topics: `/depth_cam` (Image, 32FC1 meters) + `/depth_cam/points` (`gz.msgs.PointCloudPacked` → `sensor_msgs/msg/PointCloud2`). Sees the curb's full shape
    - Tilted curb lidar: `curb_lidar_link` on the front face, ~0.23 m above ground, pitch `${radians(13)}` so the ground line lands ~1 m ahead (θ = atan(h / d)), FOV ±60°, topic `scan_curb`. Curb shows as a step in the line, but only while the line crosses it
  - **Magnetometer:** second `<gazebo reference="imu_link">` block (9-DoF IMUs have it on the same chip), `magnetometer` sensor 50 Hz, topic `mag`, + `gz-sim-magnetometer-system` in the world. Bridge `/mag@sensor_msgs/msg/MagneticField[gz.msgs.Magnetometer`
    - Rotation test passed: turning 90° keeps z and the horizontal magnitude, rotates x/y by ~90°
    - **Sim quirk:** values look like **gauss** (|B| ≈ 0.52 = Indiana's ~52 µT) not tesla, and world axes look **NED** (x north, z down, z = +0.48). Heading from `/mag` would be 90° off vs ENU. Handle in Step 12 (conversion node, or use `/imu` orientation in sim)
  - Bump sensors: **not simulated**. Last-resort safety belongs in ESP32 firmware (cut motors directly); Nav2 Collision Monitor handles prevention in sim. See roadmap Phase 2

- [x] Step 12 chunk A (2026-11-10): local EKF (`robot_localization`)
  - Checked covariances first: `/odom` pose + twist covariance **all 0** (DiffDrive has no setting for it). 0 = "perfect" → EKF would ignore every other sensor
  - Covariance = 6×6 matrix (x, y, z, roll, pitch, yaw) flattened row by row into 36 values. Diagonal = **variance** of one value from **one** sensor, at index `i*6 + i` (0, 7, 14, 21, 28, 35). Off-diagonal = correlated errors within the same sensor (left 0). Each sensor sends its own matrix; sensors only meet inside the EKF
  - Smaller variance = more trust. √variance = stddev in real units (wheel `vyaw` 0.03 → ±0.17 rad/s vs gyro 0.000081 → ±0.009 rad/s, so the gyro wins on turning)
  - New package: `ros2 pkg create ugv_localization --build-type ament_python --license Apache-2.0 --dependencies rclpy nav_msgs`. Node code goes in the **inner** `ugv_localization/ugv_localization/` folder
  - **`odom_cov_relay` node** (`ugv_localization/odom_cov_relay.py`): subscribes `/odom`, fills the diagonals, republishes `/wheel/odom`. Plays the role `diff_drive_controller` / ESP32 firmware will play on the real robot
    - `TWIST_DIAG = [0.0025, 0.001, 1e3, 1e3, 1e3, 0.03]` (vx ±5 cm/s, vy ≈ 0, unused axes 1e3 = "ignore", vyaw loose because of slip), `POSE_DIAG = [0.01, 0.01, 1e3, 1e3, 1e3, 0.05]`
    - Covariance must be exactly **36 floats** (`[0.0] * 36`, then fill the diagonal in a loop)
    - Registered in `setup.py` `entry_points` → `console_scripts`: `'odom_cov_relay = ugv_localization.odom_cov_relay:main'`
    - Runs silently (no log = normal). `KeyboardInterrupt` traceback on Ctrl+C is harmless; clean exit with `with rclpy.init():` + `except (KeyboardInterrupt, ExternalShutdownException)`
  - **`config/ekf.yaml`**: top key `ekf_filter_node`, `use_sim_time`, `frequency 30`, `two_d_mode true`, `publish_tf true`, `world_frame odom`
    - `*_config` = 15 booleans: [x y z, roll pitch yaw, vx vy vz, vroll vpitch vyaw, ax ay az]
    - `odom0: /wheel/odom` fuses **vx, vy, vyaw** (velocities, not pose: wheel pose drifts without limit). vy is fused because "can't slide sideways" is real information
    - `imu0: /imu` fuses **vyaw only**. Not yaw orientation (`orientation_covariance` = 0, no mag yet), not accel (noisy + gravity, try in chunk C)
  - `setup.py` `data_files`: `(os.path.join('share', package_name, 'config'), glob('config/*.yaml'))` and the same for `launch` / `launch/*.launch.py` (needs `import os` + `from glob import glob`). Install into **your own** package's share folder only
  - **`launch/localization.launch.py`**: relay (`use_sim_time`) + `robot_localization` `ekf_node` with `name='ekf_filter_node'`, `parameters=[ekf_config]`. Run separately from `sim.launch.py`, so localization can restart while Gazebo keeps running
  - **TF conflict:** with the EKF running, `/tf` had 3 publishers: `ekf_filter_node` + `ros_gz_bridge` (both `odom → base_link`) + `robot_state_publisher` (wheels, no conflict). A conflict = two publishers of the **same parent → child pair**, not just two publishers on `/tf`
    - In RViz: robot flickered between two poses; after spinning in place, the two copies drove off in different directions (DiffDrive heading includes slip, EKF heading follows the gyro)
    - Fix: commented out `/model/ugv/tf` in the `sim.launch.py` bridge and removed its remapping. **`sim.launch.py` alone now has no `odom → base_link`** (RViz can't place the robot); always run `localization.launch.py` too
  - `tf2_monitor` in ROS 2: always `<no authority available>` (TF messages don't carry the sender). Without `use_sim_time` the delay is ~1.79e9 s (wall clock vs sim stamps); with it, startup clock jump makes averages garbage (negative delays). Not useful here

## Frames (`ugv`)

| Frame | Published by | Meaning |
|---|---|---|
| `odom` | `ekf_filter_node` (local EKF) | Fixed start point of odometry. RViz Fixed Frame |
| `base_link` | `ekf_filter_node` (`odom` → `base_link`). DiffDrive's TF is no longer bridged | Robot body center |
| `left_/right_wheel_{front,middle,rear}` | `robot_state_publisher` (from `/joint_states`) | Wheels |
| `imu_link` | `robot_state_publisher` (`/tf_static`) | IMU + magnetometer, 0.1 m above `base_link` (top of body) |
| `lidar_link` | `robot_state_publisher` (`/tf_static`) | Lidar center, 0.12 m above `base_link` |
| `front_cam_link`, `rear_cam_link` | `robot_state_publisher` (`/tf_static`) | Camera bodies at the front/rear face, x forward |
| `front_cam_optical_link`, `rear_cam_optical_link` | `robot_state_publisher` (`/tf_static`) | Same point, z forward / y down. Image `frame_id` |
| `gps_link` | `robot_state_publisher` (`/tf_static`) | GPS antenna, top of body, 0.15 m behind `base_link` |
| `depth_cam_link` | `robot_state_publisher` (`/tf_static`) | Depth camera, front face, pitched 30° down. Point cloud `frame_id` |
| `curb_lidar_link` | `robot_state_publisher` (`/tf_static`) | Tilted curb lidar, front face, pitched 13° down |
| `map` | Not yet | Comes from the global EKF (Step 12, chunk B) |

## Frames (old, from `diff_drive.sdf`)

| Frame | Meaning |
|---|---|
| `vehicle_blue/odom` | Fixed start point of odometry. Use as RViz Fixed Frame |
| `vehicle_blue/chassis` | Robot body. Moves relative to odom |
| `map` | Not published yet. Comes later from localization / Nav2 |

## My robot (`ugv_description`, placeholder dimensions)

| Property | Value | Meaning |
|---|---|---|
| `body_l` × `body_w` × `body_h` | 0.60 × 0.40 × 0.20 m | Body box, centered on `base_link` |
| `body_m` | 15 kg | Body mass (inertia: ixx 0.25, iyy 0.5, izz 0.65) |
| `wheel_r`, `wheel_w`, `wheel_m` | 0.10 m, 0.08 m, 1 kg | Each of the 6 wheels |
| `wheel_x_spacing` | 0.22 m | Front/rear wheels at x = ±0.22, middle at 0 |
| wheel y | ±(body_w/2 + wheel_w/2) = ±0.24 m | Left = +y, right = −y |
| `wheel_z` | −0.05 m | Wheel centers below `base_link`; wheel bottoms 0.15 m below, so spawn `-z 0.2` |

- Frames: `base_link` + `left_wheel_{front,middle,rear}`, `right_wheel_{front,middle,rear}`. Joints are `<name>_joint`.
- ROS axes: x forward, y left, z up.

## Resume on a new computer

1. Install Docker (see README), clone the repo, `docker compose build`.
2. Terminal 1 (host `jpcli@`, repo root): `docker compose run --rm ros`. This is the main shell; don't `exit` it until done.
3. Terminal 1 (container `ubuntu@`, `/ws`): `colcon build --symlink-install && source install/setup.bash` (needed in every new container).
4. Terminal 1: `ros2 launch ugv_description sim.launch.py` (Gazebo with `test_world.sdf` + robot_state_publisher + spawn + bridge). Or `display.launch.py` for RViz only.
5. Extra terminals (host `jpcli@`): check `docker ps` shows exactly one container, then `docker exec` into it and `source install/setup.bash` (see [quick-commands.md](quick-commands.md)).
6. RViz with the saved config + teleop: see [quick-commands.md](quick-commands.md).
7. Continue with Step 12, `robot_localization` (see Planned next steps).

## Notes for the group demo (2026-10-22)

- Drivetrain changed: **tank treads**, one per side, each driven by 2 motors. See [roadmap.md](roadmap.md).
- Demo scope: robot + sensors (lidar, camera, IMU, GPS) visualized in RViz, **teleoperated**. No autonomous nav yet.
- Part 2 if time allows: rough 3D campus map from OpenStreetMap (separate from the robot).
- Show **screen recordings** (record on the faster machine); live demo on the slower laptop only if asked.

## Planned next steps

1. ~~Finish TF in RViz (Step 8).~~ Done.
2. ~~Step 9: IMU.~~ Done.
3. ~~Step 10: robot package, drivetrain, sensors~~ Done (2026-11-09). ~~Step 11: GPS~~ Done. Leftovers:
   - Optional: start RViz from `sim.launch.py` with the saved config
   - Optional: give the obstacles different colors (all green now), record the demo
   - `base_footprint` frame ([REP 105](https://www.ros.org/reps/rep-0105.html)) so the robot doesn't look half-sunk in RViz
4. **Step 12: `robot_localization`**, ~4–6 h over 2–3 sessions
   - ~~Chunk A: local EKF~~ Done (2026-11-10). Run: `ros2 launch ugv_localization localization.launch.py` after `sim.launch.py`
   - **Chunk B (~2–3 h, next): absolute sensors.** Local EKF only fuses rates, so heading + position still drift
     - First: magnetometer. Gazebo gives gauss in NED; ROS wants tesla in ENU ([REP 103](https://www.ros.org/reps/rep-0103.html)). Likely another small relay/conversion node
     - Then `navsat_transform` (GPS lat/lon → meters, needs a north-referenced heading) + global EKF, publishes `map → odom`
   - Chunk C (~1–2 h): tune + drive test (RViz pose should stay on Gazebo's)
   - Docs: [robot_localization](https://docs.ros.org/en/jazzy/p/robot_localization/), [Nav2 GPS tutorial](https://docs.nav2.org/tutorials/docs/navigation2_with_gps.html)
5. Bring up Nav2 against the simulated robot (+ Collision Monitor).
6. Later: Fusion 360 → URDF for the real robot, then custom PCBs / micro-ROS.

## Gotchas so far

- Bridge direction: `[` Gazebo→ROS, `]` ROS→Gazebo, `@` both.
- Bridge message types are case-sensitive (`gz.msgs.Pose_V`, not `Pose_v`). A bad type only breaks that one topic; check Terminal 1 for the error.
- Launch `remappings=` is a list of string tuples: `[('/from', '/to')]`. Unquoted topic names = Python syntax error.
- `package.xml` only lists dependencies. It never affects topic names.
- A topic in `ros2 topic list` only means it's advertised. Use `ros2 topic echo --once` / `hz` to confirm data.
- `gz topic -i -t <topic>` shows a Gazebo topic's message type. Query the exact name from `gz topic -l`.
- Python list of strings: always end each line with a comma. A missing comma silently joins two strings into one (implicit concatenation) and breaks **both** bridge entries.
- XML: attribute values need quotes, attributes need a space between them, every tag needs a close. Run `xacro ... | grep` after each edit; the parse error names the line.
- `<noise type="gaussian">`: `type` is an attribute (space, not `_`), and it's spelled gaussian.
- `A message was lost!!!` on `ros2 topic echo` = the echo subscriber dropped samples while connecting. Harmless for `--once`; matters only if a real node keeps losing messages.
- Set plugin `<topic>` names to ROS conventions (`cmd_vel`, `odom`, `joint_states`) to avoid remaps.
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
  - That includes `build/`, `install/`, `log/`: **new container → `colcon build` first**, or you get `Package 'ugv_description' not found ... searching: ['/opt/ros/jazzy']`.
- **Run `pwd` and check the prompt before any `rm -r`.** On 2026-10-23, `rm -r include src` ran on the host at repo root and deleted the whole `src/`. `rm` reported the error for `include` but silently deleted `src`.
  - Recovered with `git restore src/` (only committed files come back). Commit early.
  - After deleting/recreating `src/` on the host, the container's `/ws/src` mount points at the old deleted folder (`Unable to read current working directory`). Exit and restart the container.
- **`docker compose run` = new container. `docker exec` = another shell in the same container.** Keep exactly one container running.
  - Nodes in separate containers didn't see each other (`ros2 node list` empty).
  - `docker ps` lists newest first, so `head -1` in the exec command picks the newest container if there are two.
  - The container stops when its first (`docker compose run`) shell exits, killing all exec shells too.
  - `docker exec ... requires at least 2 arguments` = `$(docker ps -q ...)` was empty (no container running).
- `ros2 topic echo` hanging = no messages. Check `ros2 node list` and `ros2 topic info <topic>` (publisher count) before changing code.
- xacro: anything to calculate or substitute goes in `${ }`. Without it the text is copied literally (e.g. `ixx="wheel_m/12*..."`).
- xacro macro calls go **after** `</xacro:macro>`, not inside it (calling it inside = infinite recursion).
- URDF cylinders stand along z. Wheels need `rpy="${pi/2} 0 0"` in visual, collision **and** inertial, and joint axis `0 1 0`.
- No `<material>` = default color (red in RViz).
- New files under `urdf/` or `launch/` need a rebuild; edits to existing files don't (`--symlink-install`).
- `joint_state_publisher_gui` (slider GUI) is not in the image; plain `joint_state_publisher` is.
- Bridge entries must match the **Gazebo** topic name exactly (check `gz topic -l | grep <name>` first). The bridge doesn't rename: `/front_image@...` waits on a gz topic that doesn't exist
- `gz_frame_id` must be a real TF frame name (e.g. `${name}_optical_link`), not `0`
- `RTPS_TRANSPORT_SHM Error ... open_and_lock_file failed` = FastDDS shared memory unavailable in Docker, falls back to UDP. Harmless
- `ros2 topic hz` average gets dragged down by one long startup gap (`max: 10s`). Use `--window 50` for the steady rate
- `msrdc.exe` on Windows is WSLg's Remote Desktop client that draws Linux GUI windows. Normal; don't kill it.
- Edit didn't take effect? Run `git status` first. If the file isn't listed as modified, it wasn't saved (happened twice with `test_world.sdf`)
- Debug sensors Gazebo-side first: `gz topic -l | grep <name>`. Missing = world system or sensor problem. Present = bridge/ROS problem. A missing world system gives a silent ROS topic (the bridge still advertises it)
- `gz_args` is one string: `'-r ' + world_file` needs the space, or Gazebo reads `-r/ws/...` as an invalid option. When a launch process dies, read the `cmd '...'` line to see exactly what ran
- One topic name = one message type. A display subscribing to `/depth_cam` as PointCloud2 while it's an Image crashed RViz (`incompatible type ... invalid allocator`). `ros2 topic info <topic> --verbose` shows who uses which type
- RViz "By topic" hides children of a name that is both a topic and a namespace (`/depth_cam` + `/depth_cam/points`). Keep the parent a pure namespace: remap `/depth_cam` → `/depth_cam/depth_image`. Fallback: By display type + type the topic
- RViz depth Image black = auto-normalize hit +inf (sky). Uncheck Normalize Range, Min 0, Max 5
- Sensor placement: the 360° lidar hit the depth camera box (both at ~0.12 m) = dots beside the camera + a blind wedge. Keep everything clear of the lidar plane
- A pitched sensor's ±90° rays don't tilt (pitch rotates about y). Narrow the FOV so side rays don't hit the wheels
- gz magnetometer: gauss (not tesla), world axes look NED. Heading 90° off vs ENU
- Launch `name=` must match the YAML's top key (`ekf_filter_node`), or the node silently ignores the whole config
- `parameters=[ekf_config]` (variable, no quotes) loads the YAML. `{'ekf_config': True}` just makes a useless parameter named "ekf_config". Quotes = literal text, no quotes = the variable's value
- Stop stray `ros2 run` copies of a node before launching it again, or two publishers send duplicate messages
- Bad `data_files` lines leave stray files in `install/`. Clean rebuild of one package (from `/ws`): `rm -rf build/<pkg> install/<pkg> && colcon build --symlink-install --packages-select <pkg>`
- Robot flickering between two poses in RViz = two publishers of the same transform
