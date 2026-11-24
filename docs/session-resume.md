# Session resume notes

Written 2026-10-15 so work can continue on another computer. Updated 2026-10-21 (new machine), 2026-10-23 (Step 10 progress), 2026-10-24 (ugv drivable, IMU on ugv), 2026-11-07 (lidar + 2 cameras), 2026-11-09 (world file, GPS, curb sensors, magnetometer: sim sensors complete), 2026-11-10 (Step 12 chunk A: local EKF; chunk B part 1: magnetometer + Madgwick), 2026-11-14 (chunk B part 2 started: GPS noise fix, navsat_transform running, declination test in progress), 2026-11-15 (Step 12 done: navsat IMU remap fix, gps_cov_relay, global EKF, process noise tuning; sim-to-real doc; Step 13 chunks 1–3: Nav2 drives to goals, around the box and around the curb; `base_footprint` frame), 2026-11-17 (Step 13 chunk 4: GPS waypoints; chunk 5: curb lidar in the Collision Monitor), 2026-11-21 (semester plan: weekend vs winter break, sensor mounting spec), 2026-11-23 (Step 16 part 1: chassis mesh, sensor layout for the real chassis, footprint, ME spec), 2026-11-24 (real wheel size from ME; DE5 handoff doc `Clark - DE5.pdf`: system diagram, ME spec from the rear-bottom datum, proposed parts list, plan change).
Related: [roadmap.md](roadmap.md) (end goal + plan), [gazebo-basics-log.md](gazebo-basics-log.md) (full command log), [quick-commands.md](quick-commands.md) (cheat sheet).

## Where I am

Working through Gazebo Harmonic + ROS 2 Jazzy basics in the Docker container.
**Steps 10 + 11 done: sim sensors complete.** My own robot (`ugv_description` package) spawns in my own world (`worlds/test_world.sdf`, campus GPS origin, obstacles + a curb), drives with `teleop_twist_keyboard`, and shows up in RViz (saved config) on sim time.
Sensors on the ugv (all in `urdf/ugv_sensors.xacro`): IMU (`/imu`), magnetometer (`/mag`), 360° lidar (`/scan`), two front corner cameras at ±45° (`/front_left_cam/image_raw`, `/front_right_cam/image_raw`), GPS (`/gps/fix`), tilted curb lidar (`/scan_curb`). Depth camera commented out 2026-11-23 (was comparison only). Bump sensors moved to Phase 2 (firmware).
**Step 12 chunk A done (2026-11-10):** new `ugv_localization` package, local EKF fuses wheel odom + gyro and now owns `odom → base_link`. RViz robot matches Gazebo much better (not perfect: only rates fused, so drift still accumulates).
**Step 12 chunk B part 1 done (2026-11-10):** `mag_relay` converts Gazebo's mag (gauss, NED) to ROS (tesla, ENU), Madgwick fuses gyro + accel + mag into an absolute (magnetic) yaw, local EKF fuses it. Heading stays matched after spinning in place. `odom` x-axis now points ~9.2° off true east (magnetic declination, expected).
**Step 12 done (2026-11-15):** GPS noise fixed (degrees, not meters), `navsat_transform` reads Madgwick (`imu` → `/imu/data` remap), declination `+0.1606` confirmed (EKF and GPS tracks 4 cm apart), `gps_cov_relay` fills GPS covariance, **global EKF publishes `map → odom`**. Robot stays put in `map` when wheels slip against a block. Process noise x/y 0.001 cut the GPS jitter from 2–4 cm to a few mm.
Sim → real checklist (code changes + what the EE team must provide): [sim-to-real.md](sim-to-real.md).
**Step 13 chunks 1–3 done (2026-11-15):** new `ugv_navigation` package. Nav2 drives to RViz goals, plans around the box, and sees the curb via the tilted lidar (voxel layers in both costmaps, height filter 8 cm). Added `base_footprint` (ground frame) so z = 0 is the ground.
**Step 13 chunk 4 done (2026-11-17):** GPS waypoints. `gps_waypoints.py` (Simple Commander) sends a lat/lon route to Nav2's `/follow_gps_waypoints`, which converts each point with navsat's `/fromLL` service. Run: `ros2 run ugv_navigation gps_waypoints.py` after sim + localization + navigation.
**Step 13 chunk 5 done (2026-11-17):** Collision Monitor sees the curb (`laserscan_to_pointcloud` turns `/scan_curb` into `/scan_curb_cloud`, `pointcloud` source with 8 cm height filter) and uses a static footprint. Stop zone + tuning **deferred** until the real robot model.
**Design item (open): `map` frame tilted ~9.2° from true ENU.** EKF yaw comes from Madgwick (magnetic), so `map` x points magnetic east, not true east. Fine for Nav2 (`/fromLL` uses the same frame). Fix before the OSM overlay or comparing to Gazebo ground truth. See Step 13 chunk 4 notes.
**Design item (open): terrain classifier.** Today's height filter flags upward ramps as obstacles and can't see drop-offs. Plan: a node that labels the curb-lidar line (flat / ramp / small step / ledge / drop) and marks only unsafe **edges**, small steps get a medium cost. See Step 13 notes.
**Semester plan (2026-11-21):** ramp + terrain classifier moved to winter break. See [roadmap.md](roadmap.md#semester-plan-2026-11-21).
**Step 16 part 1 done (2026-11-23):** Inventor chassis mesh (red) in the URDF, sensors re-placed for the real chassis (blue), footprint includes the front wedge, ME spec updated ([sensor-mounting.md](sensor-mounting.md)). **Wheels from ME (2026-11-24):** 5 in diameter, 20 in outside to outside → `wheel_r` 0.0635, `wheel_w` 0.049 (derived), wheel_separation 0.459. Ground clearance (5 cm) and axle spacing (0.22 m) are still estimates; sensor heights didn't change. **Risk:** a 5 in wheel climbs roughly ≤ its 6 cm radius, well short of a 10–15 cm curb. Bring to ME.
**Open issue (2026-11-24): Collision Monitor barely slows the robot, if at all.** Seen after Step 16 (new footprint, `footprint:` → `points:` fix on `FootprintApproach`). Not debugged yet. Things to check first:
  - The `FootprintApproach` polygon in RViz (`visualize: True`): does it reach the wedge tip (+0.54)? Was the `points:` fix rebuilt (`ugv_navigation`)?
  - `collision_monitor` startup log for polygon or parameter errors
  - Does it see points at all? `ros2 topic hz /scan_curb_cloud`; obstacle height vs `min_height` (scan 0.15, curb cloud 0.08). The 360° lidar is now at 0.45 m, so it misses short obstacles
  - `min_points: 6` and `time_before_collision: 1.2` may be too lax for the larger footprint
  - Command chain: Nav2 → `cmd_vel_smoothed` → Collision Monitor → `cmd_vel`. Teleop tests must publish to `cmd_vel_smoothed` and **hold** keys
**DE5 handoff (2026-11-24):** [`Clark - DE5.pdf`](Clark%20-%20DE5.pdf) went to the team: progress, ME positions from the rear-bottom datum (inches), [system diagram](system-diagram.png), proposed parts (RPLIDAR C1 × 2, Camera Module 3 Wide × 2 + Pi 5 cables, ZED-F9P + all-band antenna, BNO085 on the ESP32). RTK is decided; E-stop + power belong to EE; curb climbing parked.
**Next (updated 2026-11-24):** register for InCORS (RTK corrections), finalize parts with EE, then a more complicated `test_world` + screen recording before the presentation. Nav tuning, the `map` tilt fix and the OSM world → winter break. Most other sim / micro-ROS work waits for the real parts.

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
  - Known quirk: DiffDrive odom is 2D (z = 0), so `base_link` sat at ground level in RViz (robot looked half-sunk). **Fixed 2026-11-15** with a `base_footprint` frame ([REP 105](https://www.ros.org/reps/rep-0105.html))

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
    - **Sim quirk:** values look like **gauss** (|B| ≈ 0.52 = Indiana's ~52 µT) not tesla, and world axes look **NED** (x north, z down, z = +0.48). Solved in Step 12 chunk B with `mag_relay` (fixed 108.4° rotation, not a 90° swap; see below)
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
- [x] Step 12 chunk B part 1 (2026-11-10): magnetometer → absolute heading
  - Gyro measures a **rate**; integrating it adds up errors (drift) and it never knows where north is. Absolute heading needs the magnetometer (and later GPS)
  - `robot_localization` can't take `MagneticField`. Pipeline: `/mag` → `mag_relay` → `/imu/mag` + `/imu` → **Madgwick** → `/imu/data` (orientation incl. yaw) → EKF
  - **Measured the gz quirk at 2 known headings** (yaw from `ros2 run tf2_ros tf2_echo odom base_link`, RPY in degrees):
    - Spawn (yaw 0, facing east): gz `(0.198, -0.032, 0.482)` gauss = (North, East, Down) in µT ×100. Correct ENU sensor: `(-3.2, 19.8, -48.2)` µT
    - Facing south (yaw −88.7°): gz `(0.035, 0.198, 0.482)`. Correct: `(-19.8, -3.2, -48.2)` µT
    - **The x↔y swap is a trap**: matches facing east, ~180° wrong facing south. A swap is a mirror (turning left looks like turning right). Never derive a frame conversion from one measurement
    - Gazebo's horizontal arrow has the right size and rotation direction, just a **fixed angle** off. `atan2(y, x)` of gz vs correct arrow: 108.4° (east), 109.2° (south, turn wasn't exactly 90°). = 90° − 2 × (−9.18° gz declination)
  - **`mag_relay` node** (`ugv_localization/mag_relay.py`, sim only; real IMU drivers already give tesla ENU): rotate (x, y) by `MAG_ROTATION = math.radians(108.4)` (keep `x_new`/`y_new` separate), `z = -z`, × `GAUSS_TO_TESLA = 1e-4`, publish `imu/mag`. Only exact while level (2D). Verified: spawn `(-3.23e-06, 1.98e-05, -4.82e-05)`, south `(-1.99e-05, -2.99e-06, -4.82e-05)` T
  - Reading a magnetometer: the field arrow's "shadow" on each robot axis (same direction = +, opposite = −). Northern hemisphere: field dives ~67° into the ground → z negative in z-up
  - **Madgwick** (`imu_filter_madgwick`): installed by adding `<exec_depend>imu_filter_madgwick</exec_depend>` to `package.xml` → Dockerfile Layer 4 (`rosdep install --from-paths src`) installs it on `docker compose build`. `ros2 pkg prefix` → `/opt/ros/jazzy` = apt package
    - Params: `use_mag: True`, `world_frame: 'enu'`, `publish_tf: False` (else `imu_link` gets 2 parents), `orientation_stddev: 0.05` (→ `orientation_covariance` 0.0025, no more zeros)
    - Remap `('imu/data_raw', '/imu')`: **(name inside the node's code, real topic)**. Reversed = silent failure. `imu/data_raw` then only exists inside Madgwick, not on the network
    - At spawn: quaternion z = −0.081 → yaw = 2·asin(z) = **−9.3°** = magnetic declination. Compass/Madgwick point to **magnetic** north, not true north. Correct in `navsat_transform` (`magnetic_declination_radians`; test the sign, ENU yaw is CCW, compass headings are CW). Gazebo uses ~−9.2°, NOAA says ~−5° for the real campus
  - `ekf.yaml`: `imu0: /imu/data`, fuse **yaw + vyaw**. `tf2_echo odom base_link` at spawn: yaw −9.294° → `odom` x-axis = magnetic east (fine for the local EKF; `map` handles true north)
  - Drive test: heading matches Gazebo after spinning. Obstacles wiggle slightly in RViz when changing direction = pose error made visible (not GPS, it isn't fused yet). Suspects for chunk C: Madgwick `gain` lag, slip in wheel `vx`
  - Ran `docker compose build` (rosdep) → new container → `colcon build` first
- [x] Step 12 chunk B part 2 (2026-11-14 → 11-15): GPS → `navsat_transform` → global EKF
  - **GPS noise bug:** robot ~0.7 m from origin (`gz model -m ugv -p` = ground truth), but `/gps/fix` said ~1.5 km away, and a 2nd fix jumped ~2 km. Random jumps = noise, not an offset
    - gz-sensors NavSat applies `<horizontal>` noise to **lat/lon in degrees**, not meters. `0.02` = 0.02° ≈ 2.2 km. `<vertical>` (altitude) is in meters
    - Fix in `ugv_sensors.xacro`: keep `gps_h_std` in meters, add `gps_h_std_deg = ${gps_h_std / 111320}` (= 1.797e-07) and use it in `<horizontal>`. Longitude noise ends up ~1.3× bigger (cos 40.5°), fine for sim
    - Verified at spawn: lat 40.5155310 (origin), lon −85.6554788 = 0.15 m west of origin (`gps_link` is 0.15 m behind `base_link`, robot faces east). Fix-to-fix change ~1 cm
    - Lesson: wheel odom isn't ground truth (it can't see sliding or being flung). Ask Gazebo: `gz model -m ugv -p`
  - **`/gps/fix` covariance is all 0** (`position_covariance_type: 0` = unknown). `navsat_transform` copies it into `/odometry/gps` → an EKF would treat GPS as perfect. **To do before fusing:** GPS covariance relay (same pattern as `odom_cov_relay`, variance = 0.02² m²)
  - Checking xacro: run it on the **main** file `ugv.urdf.xacro`. `ugv_sensors.xacro` alone fails (`name 'body_h' is not defined`) because its properties come from the main file. Xacro reformats XML, so `grep -A4` (not `-A2`) to see `<stddev>`
  - **`config/navsat.yaml`** (top key `navsat_transform`): `frequency 30`, `delay 3.0`, `magnetic_declination_radians 0.1605703` (+9.2°, sign under test), `yaw_offset 0.0` (Madgwick ENU yaw 0 = facing east already), `zero_altitude true`, `broadcast_cartesian_transform false`, `publish_filtered_gps true`, `use_odometry_yaw false`, `wait_for_datum false`
    - Default topics `imu/data`, `gps/fix`, `odometry/filtered` already match → no remaps. New yaml file → rebuild once
    - Trap 1: wrote `9.2` (degrees) in a `_radians` param
    - Trap 2: `yaw_offset: 0` crashed the node (exit code −6 = SIGABRT, uncaught exception). YAML `0` = integer, node declares a double → `InvalidParameterTypeException`. Write `0.0`
  - Added `navsat_transform_node` (`name='navsat_transform'`, `parameters=[navsat_config]`) to `localization.launch.py`. At rest, `/odometry/gps` ≈ (0.04, 0.00): first fix becomes the origin
  - **Declination sign test** (turn left ~90°, drive north, compare track directions with `atan2(y, x)`; correct sign → tracks agree, wrong sign → ~18° apart):
    - Truth (`gz model`): (0.059, 1.905), yaw 89.3°, track 88.2°. EKF: (0.363, 1.867), yaw 80.2°, track 79.0° (= truth − 9.2°, odom frame rotated by declination, as expected). GPS: (0.663, 1.811), track 71.0° (truth − 17.2°, **~8° wrong**)
    - Log: `Corrected for magnetic declination of 0.16057, user-specified offset of 0 and meridian convergence of 0.0152466. Transform heading factor is now 0.175817`
    - Source ([navsat_transform.cpp](https://github.com/cra-ros-pkg/robot_localization/blob/jazzy-devel/src/navsat_transform.cpp)): `imu_yaw += declination + yaw_offset + convergence`, then logs `imu_yaw`. 0.175817 − 0.16057 − 0.01525 ≈ 0 → **captured raw IMU yaw ≈ 0** (should be ≈ −0.16 rad). Exactly 0 looks like an identity quaternion, not a noisy reading. Plugging in 0 predicts a ~69° GPS track (measured 70–71°)
    - The transform is computed **once** (first timer tick with IMU + odom + GPS), then locked; later IMU messages are ignored. One bad snapshot ruins the whole run
    - Ruled out: Madgwick slow start. `/imu/data` `orientation.z` = 0.644 (80.2°) from the very first message after a relaunch → raising `delay` won't fix it
    - **Root cause (2026-11-15):** `navsat_transform` subscribes to **`imu`**, not `imu/data` (checked the source: `create_subscription<Imu>("imu", ...)`; the docs/my earlier claim were wrong). It was reading Gazebo's raw `/imu`, whose orientation is perfect true heading (0° at spawn, no noise) → declination added on top = ~9° error. Same wrong value every launch = systematic, not a race
    - **Fix:** remap `('imu', '/imu/data')` on the navsat node. Heading factor became 0.0151 → raw yaw = 0.0151 − 0.1758 = −0.161 rad (−9.2°) = Madgwick ✅. Leftover 0.015 = meridian convergence
    - **Drive test passed:** EKF (0.450, 2.235) vs GPS (0.459, 2.278), both 78.6°, 4 cm apart. **`+0.1606` is the right sign** (true yaw = imu yaw + declination)
    - Lesson: don't trust default topic names from memory; check `ros2 node info /navsat_transform` (Subscribers) or the source
  - **`gps_cov_relay` node** (`ugv_localization/gps_cov_relay.py`, sim only): `/gps/fix` → `/gps/fix_cov`
    - `NavSatFix.position_covariance` = 3×3 (east, north, up) = **9 values**, diagonal at `i*3 + i` (0, 4, 8). `POS_DIAG = [0.0004, 0.0004, 0.0016]` (2 cm / 4 cm squared)
    - Set `position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN` (2)
    - Registered in `setup.py`, added to the launch file, navsat remap `('gps/fix', '/gps/fix_cov')`. New node → rebuild
    - Check: `/odometry/gps` `pose.covariance` shows 0.0004 at 0 and 7, 0.0016 at 14
  - **Global EKF** (2nd `ekf_node`, `name='ekf_filter_node_map'`, same `ekf.yaml`, 2nd top-level block)
    - `world_frame: map`, `map_frame: map`, `publish_tf: true` → publishes **`map → odom`**. Same `odom0` (`/wheel/odom`) + `imu0` (`/imu/data`) as the local EKF, plus `odom1: /odometry/gps` fusing **x, y only** (z false: not using altitude)
    - The node `name` picks which yaml block it reads
    - Output remap `('odometry/filtered', '/odometry/global')`, else both EKFs publish on the same topic. navsat now reads `('odometry/filtered', '/odometry/global')` (standard dual-EKF setup)
    - **Test against the box:** wheels spinning, robot stuck. Fixed Frame `odom`: robot keeps "driving" forward (wheel slip). 2nd axis = `map`, slides backward to cancel it. Fixed Frame **`map`**: robot stays put ✅. `map → odom` = the correction for odom drift
  - **GPS jitter tuning:** robot stopped but shaking in `map`. Measured: `/odometry/global` jumped 2–4 cm every 3rd message (EKF 30 Hz, GPS 10 Hz), heading only ±0.1°
    - Not wheels (pressing `k` didn't help), not GPS covariance (0.01 made no visible difference)
    - Cause: default **process noise** x, y = 0.05 ("robot may drift ~22 cm/s on its own") → EKF trusts GPS almost 1:1
    - Fix: `process_noise_covariance` (15×15 = 225 values) in the **global** block only, x and y = **0.001**, rest = defaults. Now mostly mm jumps, occasional ~2 cm. 0.0001 = smoother but slower to correct drift
    - Write every entry as `0.0` (doubles), same type trap as `yaw_offset`
  - Madgwick "Still waiting for data on topics imu/data_raw and imu/mag" = no IMU data (sim not running/paused). Topic names in that warning are hardcoded text, not a remap problem. Start the sim first, then localization
- [x] Step 13 chunks 1–3 (2026-11-15): Nav2
  - **Nav2 pieces:** planner (draws the path), controller (follows it, sends `/cmd_vel`), costmaps (grid of safe/unsafe cells from the lidar), BT navigator (the boss: plan, follow, retry). **No AMCL / map server**: they're for indoor pre-made maps; the EKFs already give `map`
  - **Package:** `ros2 pkg create ugv_navigation --build-type ament_cmake`, delete `include/` + `src/`, add `config/` + `launch/`, `install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})`, `<exec_depend>nav2_bringup</exec_depend>`
  - `config/nav2_params.yaml` = copy of `/opt/ros/jazzy/share/nav2_bringup/params/nav2_params.yaml`. Changes:
    - `odom_topic` → `/odometry/filtered` (local EKF) in `bt_navigator` + `velocity_smoother`
    - `robot_radius: 0.22` → `footprint: "[[0.30, 0.28], [0.30, -0.28], [-0.30, -0.28], [-0.30, 0.28]]"` (both costmaps)
    - Global costmap: no `static_layer` (it waits forever for a map that doesn't exist), `rolling_window: true`, 50 × 50 m, `track_unknown_space: false`. Local: 5 × 5 m
    - Every robot frame setting (`robot_base_frame`, `base_frame_id`, `base_frame`) → `base_footprint`
  - `launch/navigation.launch.py`: `IncludeLaunchDescription` of `nav2_bringup/launch/navigation_launch.py` with `use_sim_time: 'True'` + `params_file`
  - Local costmap uses `odom` (smooth, never jumps: good for dodging), global uses `map` (GPS-corrected: good for long routes)
  - **Debug 1:** `Invalid frame ID "odom" ... frame does not exist` = localization not running (`ros2 node list` had no EKFs). Start order: sim → localization → navigation. Wait for `Managed nodes are active`. Errors after `^C` are shutdown noise
  - **Debug 2:** path planned but robot didn't move. `Failed to get "lidar_link"->"base_footprint"`: Collision Monitor (last in the `cmd_vel` chain: controller → velocity_smoother → collision_monitor → `/cmd_vel`) defaulted to `base_footprint`, which didn't exist yet → blocked all commands
  - Harmless: "Control loop missed its desired rate of 20 Hz. Current loop rate is 41 Hz" (sim-time quirk)
  - Don't use teleop while Nav2 drives (both publish `/cmd_vel`)
  - RViz: Fixed Frame `map`, Path on `/plan`, Map displays on `/local_costmap/costmap` + `/global_costmap/costmap`, goal with **2D Goal Pose**
  - Chunk 2: goal behind the box → path curves around it. Inflation "halo" = Nav2 plans for the robot's center, so cells where the body would hit (+ margin) are costly
  - **`base_footprint` frame** ([REP 105](https://www.ros.org/reps/rep-0105.html)): `<link name="base_footprint"/>` + fixed joint to `base_link` at z = `${-wheel_z + wheel_r}` = 0.15. DiffDrive `<child_frame_id>base_footprint`, both EKFs `base_link_frame: base_footprint`. Tree: `map → odom → base_footprint → base_link → sensors`. Ground = z 0 → simple height filters, robot no longer half-sunk in RViz
  - **Chunk 3, curb:** `/scan_curb` in RViz: straight ground line, breaks into an angled step at the curb
    - Added source `scan_curb` to the voxel layer: `min_obstacle_height: 0.08` (ignore ground hits), `max_obstacle_height: 0.5`, `obstacle_max_range: 2.0`, `raytrace_max_range: 2.5`
    - Local only → robot got stuck: global planner (blind to the curb) drew a path through it, local controller refused. Both costmaps must agree
    - Global costmap switched from `obstacle_layer` (2D) to a **`voxel_layer` (3D)** with `scan` + `scan_curb`. In 2D, 360° lidar rays passing *over* the curb would erase it. → planner routes around the curb's end ✅
  - **Design item: drop-offs and memory** (not built yet)
    - Height filter only catches things *above* ground. A sidewalk ledge (drop) is invisible today
    - Marking "low points" (z < −8 cm) also flags downhill ramps, **and marks the road surface itself** as danger. Ground hits are filtered out, so they never erase those marks → stale danger when the robot later drives on the road
    - Plan: **step detector node**. Read `/scan_curb`, find sudden jumps between neighboring points (step) vs gradual change (ramp), publish only the **edge** as an obstacle. Edge looks the same from above or below, surfaces stay clean. Heights are relative to the robot (it's always at z 0)
    - Option: a decaying layer (STVL, check it's packaged for Jazzy) so old marks fade
    - Thresholds depend on the real lidar and real curbs → build after hardware data, or at least retune then
    - Team question: climb curbs (project goal) or only use curb cuts? Decides if an edge = "stop" or "slow down and climb"
    - OSM sidewalk routes (Step 15) are the main defense; costmap is the backup
  - **Design item: upward ramps** (2026-11-15, not built yet)
    - Curb lidar: a ramp rising 8+ cm gets flagged like a curb. Height alone can't tell them apart; **shape** can (ramp = gradual, curb = sudden jump)
    - 360° lidar (flat plane ~27 cm up): a long uphill crosses the plane and looks like a wall. Distance ≈ 0.27 / tan(slope): **5° (ADA ramp) → ~3 m, 10° → ~1.5 m**
    - Fix ideas: judge **slope**, not height (≤ max climbable, e.g. 10–15° = drivable). For the 360° lidar: ignore hits that match the ground slope from the curb lidar (simple), or a 3D elevation map (`grid_map` / elevation mapping, heavier on the Pi)
    - Test first: add a ramp (tilted box) to `test_world.sdf` to see both problems in sim
  - **Design: terrain classifier** (combines drop-offs + ramps; likely the most important custom piece of the robot)
    - Label each edge in the curb-lidar line by height:

      | Edge height | Label | Costmap |
      |---|---|---|
      | < 2 cm | Flat (noise) | nothing |
      | 2–7 cm (~1–3 in) | Small step, OK to cross | **medium cost** (e.g. 150) |
      | > 7 cm | Ledge / curb | lethal (254) |
      | Gentle slope ≤ max climb | Ramp | nothing |
      | Steep slope | Too steep | lethal |

    - Thresholds depend on the real robot (track size, torque, up vs down)
    - **Avoid zig-zagging between levels:** costmap cells are 0 (free) → 254 (lethal), not just yes/no. Crossing a small step costs something, so the planner only crosses when it saves real distance. Same costs every replan → stable path. Which surface to use is the route's job (Step 15)
    - Limits: costmaps have **no direction** (can't say "OK down, not up"). Medium costs need a **custom C++ costmap layer**; standard layers only mark lethal
    - **v1** (~2–3 h): Python node, small steps ignored, big edges + steep slopes lethal. **v2** (~4–8 h): C++ costmap layer with medium costs

- [x] Step 13 chunk 4 (2026-11-17): GPS waypoints
  - **How it works:** Nav2 only takes map x/y. `navsat_transform` offers services `/fromLL` (lat/lon → map x/y) and `/toLL` (reverse). Nav2's `waypoint_follower` (already started by `navigation_launch.py`) has a `/follow_gps_waypoints` action that calls `/fromLL` for each point. **No `nav2_params.yaml` change needed**
  - Origin (`test_world.sdf` + datum, since `wait_for_datum: false` and the robot spawns there): **lat 40.515531, lon −85.655477**. At this latitude: 1 m north ≈ 0.00000898° lat (1 / 111,320), 1 m east ≈ 0.0000118° lon (1 / 84,650)
  - `/fromLL` test: first call gave (533, 3287) = a **typo** in the latitude (40.5**4**55 vs 40.5**1**55 = 0.03° ≈ 3.3 km). `toLL(0, 0)` returned exactly the world origin → service fine, input wrong. Lesson: check the input before blaming the tool
    - Correct origin → (0.04, −0.01). 0.0001° north (~11 m) → (1.82, 10.95), predicted (1.78, 10.96)
  - **`map` frame tilt (design item):** a point due north came out rotated ~9.2° (x positive). EKFs fuse Madgwick's **magnetic** yaw, so `map`/`odom` x = magnetic east. Navsat adds declination so GPS matches the EKF, and `/fromLL` uses the same frame → goals land right. Matters later for the OSM overlay (Step 15) and comparing RViz to `gz model` truth. Possible fix: correct the IMU yaw by the declination before the EKFs
  - `ros2 interface show nav2_msgs/action/FollowGPSWaypoints`: goal `gps_poses` = list of `geographic_msgs/GeoPose` (lat/lon/alt + orientation), feedback `current_waypoint` (index), result `missed_waypoints` (each with the converted map `PoseStamped`)
  - **CLI test:** 5 m true east (lon −85.655418), `box_1` in the way:
    ```bash
    ros2 action send_goal /follow_gps_waypoints nav2_msgs/action/FollowGPSWaypoints "{gps_poses: [{position: {latitude: 40.515531, longitude: -85.655418, altitude: 0.0}}]}" --feedback
    ```
    - Gazebo truth (4.87, −0.10), `map` (4.82, −0.89) vs predicted (4.94, −0.80). Both ~15 cm off = inside `xy_goal_tolerance` (0.25 m). Yaw: gz 22.8°, map 13.6° → 9.2° tilt again
  - **Script** `ugv_navigation/scripts/gps_waypoints.py` ([Simple Commander](https://docs.nav2.org/commander_api/index.html)): `BasicNavigator`, `waitUntilNav2Active(localizer='robot_localization')` (no AMCL), build `GeoPose` list, `followGpsWaypoints()`, loop on `isTaskComplete()`, print `getFeedback().current_waypoint`, `getResult()` (= `TaskResult`, not the missed list)
    - Test route (truth): (0, 0) → (5, 0) → (5, 5) → (0, 0). Hardcoded for now; final version = click on a map to drop points (MapViz or a web map) → same `followGpsWaypoints()` call
    - CMake package: `install(PROGRAMS scripts/gps_waypoints.py DESTINATION lib/${PROJECT_NAME})` (not `install(DIRECTORY ...)` → `share/`, where `ros2 run` doesn't look). `chmod +x` on the host
    - `package.xml`: `exec_depend` on `rclpy`, `nav2_simple_commander`, `geographic_msgs` (so rosdep installs them for teammates)
    - Bugs fixed: missing `sleep` import, `getFeedback()` returns `None` before the first feedback, **CRLF line endings** (`/usr/bin/env: 'python3\r': No such file or directory`, exit 127) → `sed -i 's/\r$//' <file>`. Added `.gitattributes` (`* text=auto eol=lf`) so it can't come back

- [x] Step 13 chunk 5 (2026-11-17): Collision Monitor
  - **What it is:** last-line safety node between Nav2 and the wheels: controller → velocity_smoother → `cmd_vel_smoothed` → **collision_monitor** → `/cmd_vel`. Reads raw sensor points (not costmaps), slows/stops if a hit is coming. [Docs](https://docs.nav2.org/configuration/packages/configuring-collision-monitor.html)
  - **Test by hand through the monitor:** `ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_smoothed` (plain teleop publishes `/cmd_vel` = skips the monitor). Don't send Nav2 goals at the same time
  - **Monitor only runs when a command arrives** on `cmd_vel_smoothed` (no timer). Teleop publishes only on key press → tap `i` once, DiffDrive keeps rolling, monitor never re-checks → **drove into the box**. **Hold** the key (auto-repeat) to test. Nav2's controller sends 20 Hz, so autonomous driving is fine
    - Same reason the green polygon in RViz only moved on a new key press, and no markers show while parked
    - Real robot: firmware **watchdog** (no `/cmd_vel` for ~0.5 s → stop), already in [sim-to-real.md](sim-to-real.md)
  - After touching the box the robot wouldn't move at all: box points **inside** the footprint = every command (even reverse) is an instant collision → zeros. Restart the sim to reset
  - `Robot to approach for 1.200000 seconds away from collision` = monitor switched into approach mode (slowing), not an error
  - **Visualize:** `visualize: True` on the polygon → RViz **Polygon** `/FootprintApproach` + **MarkerArray** `/collision_monitor/collision_points_marker` (points it counts as obstacles). Shows in **RViz, not Gazebo**. `ros2 param get /collision_monitor FootprintApproach.visualize` checks what the running node loaded
  - **Footprint lag fix:** `footprint_topic: /local_costmap/published_footprint` updates a few times/s in `odom` → the monitor checked where the robot **was** (~25 cm behind at 0.5 m/s). Replaced with static `points: "[[0.30, 0.28], [0.30, -0.28], [-0.30, -0.28], [-0.30, 0.28]]"` (same as the costmap footprint, in `base_footprint`)
  - **Approach mode** (`time_before_collision: 1.2`): simulates the footprint forward in 0.1 s steps, scales speed so the hit stays 1.2 s away (speed ≈ distance ÷ 1.2). Creeps closer and closer, never a hard stop → small errors (0.1 s steps, ~1 cm lidar noise, coasting) → **eventually touches**. Meant for getting close (docking), not for keeping a gap
  - **Curb:** `/scan` (plane ~27 cm) passes over the 20 cm curb → drove straight into it. Monitor doesn't use costmaps, so chunk 3 didn't help
    - `type: "scan"` sources have **no height filter** (flattened to 2D) → the tilted curb lidar's ground line ~1 m ahead would look like a permanent wall
    - `type: "pointcloud"` sources do: `min_height` / `max_height` in `base_footprint`. So: **`laserscan_to_pointcloud_node`** (`pointcloud_to_laserscan` package) in `navigation.launch.py`, remaps `('scan_in', '/scan_curb')`, `('cloud', '/scan_curb_cloud')`
    - Package wasn't installed: `<exec_depend>pointcloud_to_laserscan</exec_depend>` in `ugv_navigation/package.xml` → `docker compose build` (rosdep layer) → new container → `colcon build`
    - Source block: `scan_curb: {type: "pointcloud", topic: "/scan_curb_cloud", min_height: 0.08, max_height: 0.5}`, added to `observation_sources`
    - Rates match: `/scan_curb` and `/scan_curb_cloud` both ~5.9 Hz
    - Result: **slows for the curb**, then bumps it (same approach creep as the box)
  - **Finding node topic names:** left side of a remap = the node's internal name (README "Subscribed/Published Topics", or `ros2 node info`). Right side = your real topic (`ros2 topic list`) or a new name you pick
    - **Lazy subscription:** `laserscan_to_pointcloud` only subscribes to `scan_in` while someone listens to `cloud` → `node info` showed `/cloud` but no `/scan_in`. `ros2 topic echo /cloud` in another shell → `/scan_in` appears. Also why `hz` first says "does not appear to be published yet"
  - **Curb lidar geometry** (from the xacro): ~0.23 m up, pitched 13°, front of body. Ground hit ≈ 0.23 / tan 13° ≈ **1.0 m** ahead of the lidar. Sees the curb face (0–20 cm) from 1.0 m to 0.14 m, closer than that the beam lands on the curb **top** (z 0.2 > 0.08) → the curb never leaves view before contact. The monitor has **no memory** (latest scan only), so a shorter obstacle, or a different real lidar height/tilt, could vanish before contact. Recheck with real dimensions
  - **Deferred (until the real robot model, Step 16):** a `stop` polygon a bit larger than the footprint (hard stop, guaranteed gap) + maybe a `slowdown` zone. Size depends on real braking distance and top speed: a 10 cm margin is too small at 1.5 m/s (latency + braking). Nav2's default config has `PolygonStop` / `PolygonSlow` as templates

- [x] Step 16 part 1 (2026-11-23): Inventor chassis mesh + sensor layout
  - `meshes/chassis.obj` (exported from the `.iam` in meters, wheels suppressed) + hand-written `chassis.mtl` (red). The `newmtl` name must match the OBJ's `usemtl` line (`191,191,191`). `meshes` added to `install(DIRECTORY ...)`
  - OBJ is Inventor **y-up**, origin at the body bottom, wedge toward Inventor −x → visual `<origin xyz="-0.066 0 -0.164" rpy="${pi/2} 0 ${pi}"/>`. Only the visual is a mesh; collision stays a box
  - Body read from the mesh's vertices: main box 0.56 × 0.41 × 0.33 m (22 × 16 × 13 in) + 0.25 m sloped wedge in front. `base_link` = middle of the main box (wheelbase center = turning center), not the bounding-box center
  - Wheels: no wheel mesh, kept cylinders. First estimate r 0.10, `wheel_z` −0.114. **Updated 2026-11-24 from ME:** 5 in diameter (`wheel_r` 0.0635), 20 in outside to outside (`wheel_outer_w` 0.508 → `wheel_w` 0.049). New `ground_clearance` property (0.05, estimate) sets `wheel_z` = −0.1515 → `base_link` 0.215 m up, so sensor heights moved only 1 mm
  - Cameras: front + rear → `front_left_cam` / `front_right_cam` on the wedge ridge corners (x 0.29, y ±0.185), yaw ±45° (~192° view, ~12° overlap). No rear camera; the 360° lidar covers the rear
  - Curb lidar moved to the wedge face (0.38, 0, 0.04): 0.25 m above ground, 14° down → ground ~1 m ahead. Nav2 height filters unchanged (they're ground-relative)
  - 360° lidar on a 5 cm riser (`lidar_riser`), scan plane 0.45 m. The new cams + GPS puck sat in its scan plane (self-hits). It's blind below 0.45 m except where the curb lidar looks
  - Depth cam commented out (xacro + 2 bridge lines)
  - All sensor visuals use `sensor_blue`; IMU (board under the lid) and GPS (puck on top) got visuals
  - Gazebo finds the mesh via `AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', <share>/..)` in `sim.launch.py`
  - Nav2 footprint (both costmaps + Collision Monitor `FootprintApproach`): `[[0.54, 0.29], [0.54, -0.29], [-0.33, -0.29], [-0.33, 0.29]]`. GPS waypoint run OK. With the real wheels (2026-11-24): `[[0.54, 0.26], [0.54, -0.26], [-0.29, -0.26], [-0.29, 0.26]]`
  - Still open: ground clearance, axle spacing and wheel count from ME (→ ride height → curb lidar tilt), collision box doesn't include the wedge, Collision Monitor stop zone; Collision Monitor barely slows (open issue in Where I am)

## Frames (`ugv`)

| Frame | Published by | Meaning |
|---|---|---|
| `odom` | `ekf_filter_node` (local EKF) | Fixed start point of odometry. Local costmap frame. x-axis = magnetic east (~9.2° off true east) since the EKF fuses Madgwick yaw |
| `base_footprint` | `ekf_filter_node` (`odom` → `base_footprint`). DiffDrive's TF is not bridged | On the ground under the robot center (z 0). Nav2 robot frame |
| `base_link` | `robot_state_publisher` (`/tf_static`, fixed joint) | Middle of the main box (wheelbase center), 0.215 m above `base_footprint` |
| `left_/right_wheel_{front,middle,rear}` | `robot_state_publisher` (from `/joint_states`) | Wheels |
| `imu_link` | `robot_state_publisher` (`/tf_static`) | IMU + magnetometer, 0.165 m above `base_link` (top of body). Madgwick has `publish_tf: False` so it doesn't add a 2nd parent |
| `lidar_link` | `robot_state_publisher` (`/tf_static`) | Lidar center on a 5 cm riser, 0.235 m above `base_link` (0.45 m above ground) |
| `front_left_cam_link`, `front_right_cam_link` | `robot_state_publisher` (`/tf_static`) | Camera bodies on the wedge ridge corners, yaw ±45° |
| `front_left_cam_optical_link`, `front_right_cam_optical_link` | `robot_state_publisher` (`/tf_static`) | Same point, z forward / y down. Image `frame_id` |
| `gps_link` | `robot_state_publisher` (`/tf_static`) | GPS antenna, top of body, 0.14 m behind `base_link` |
| `curb_lidar_link` | `robot_state_publisher` (`/tf_static`) | Tilted curb lidar on the wedge face, 0.25 m above ground, pitched 14° down |
| `map` | `ekf_filter_node_map` (global EKF, `map → odom`) | True position (GPS-corrected). x-axis = true east. Use as RViz Fixed Frame from now on; Nav2 uses it |

## Frames (old, from `diff_drive.sdf`)

| Frame | Meaning |
|---|---|
| `vehicle_blue/odom` | Fixed start point of odometry. Use as RViz Fixed Frame |
| `vehicle_blue/chassis` | Robot body. Moves relative to odom |
| `map` | Not published yet. Comes later from localization / Nav2 |

## My robot (`ugv_description`, chassis from Inventor, wheel size from ME)

| Property | Value | Meaning |
|---|---|---|
| `body_l` × `body_w` × `body_h` | 0.56 × 0.41 × 0.33 m | Main box (collision box), centered on `base_link`. Wedge not included |
| Visual | `meshes/chassis.obj` | Main box + 0.25 m wedge in front, tip at x ≈ +0.53 |
| `body_m` | 15 kg | Body mass (placeholder) |
| `wheel_r`, `wheel_w`, `wheel_m` | 0.0635 m (5 in dia.), 0.049 m, 1 kg | Each of the 6 wheels. `wheel_w` = `wheel_outer_w`/2 − `body_w`/2, from ME's 20 in outside-to-outside. Mass is a guess |
| `wheel_x_spacing` | 0.22 m | Front/rear wheels at x = ±0.22, middle at 0 (estimate) |
| wheel y | ±(body_w/2 + wheel_w/2) = ±0.2295 m | Left = +y, right = −y. Outer edge ±0.254 m. DiffDrive `wheel_separation` 0.459 |
| `ground_clearance` | 0.05 m | Ground to body bottom (estimate). Sets `wheel_z` = `wheel_r` − `ground_clearance` − `body_h`/2 = −0.1515 → `base_link` 0.215 m up |

- Frames: `base_link` + `left_wheel_{front,middle,rear}`, `right_wheel_{front,middle,rear}`. Joints are `<name>_joint`.
- ROS axes: x forward, y left, z up.

## Resume on a new computer

1. Install Docker (see README), clone the repo, `docker compose build`.
2. Terminal 1 (host `jpcli@`, repo root): `docker compose run --rm ros`. This is the main shell; don't `exit` it until done.
3. Terminal 1 (container `ubuntu@`, `/ws`): `colcon build --symlink-install && source install/setup.bash` (needed in every new container).
4. Terminal 1: `ros2 launch ugv_description sim.launch.py` (Gazebo with `test_world.sdf` + robot_state_publisher + spawn + bridge). Or `display.launch.py` for RViz only.
5. Extra terminals (host `jpcli@`): check `docker ps` shows exactly one container, then `docker exec` into it and `source install/setup.bash` (see [quick-commands.md](quick-commands.md)).
6. RViz with the saved config + teleop: see [quick-commands.md](quick-commands.md).
7. Terminal 2: `ros2 launch ugv_localization localization.launch.py` (odom_cov_relay + mag_relay + Madgwick + local EKF + gps_cov_relay + navsat_transform + global EKF). Start it **after** the sim is up. **Required**: without it nothing publishes `odom → base_link`.
8. Terminal 3: `ros2 launch ugv_navigation navigation.launch.py` after localization. Wait for `Managed nodes are active`. RViz Fixed Frame `map`, send goals with 2D Goal Pose.
9. Terminal 4 (optional): `ros2 run ugv_navigation gps_waypoints.py` drives the GPS test route.
10. Optional, test the Collision Monitor by hand: teleop with `--ros-args -r cmd_vel:=cmd_vel_smoothed`, **hold** keys.
11. Continue with the `map` frame tilt, then Step 14 minimal (see Planned next steps).

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
   - **Chunk B: absolute sensors**
     - ~~Part 1: magnetometer + Madgwick, EKF fuses absolute yaw~~ Done (2026-11-10)
     - ~~Part 2: GPS noise units, `navsat_transform`, declination test, GPS covariance relay, global EKF~~ Done (2026-11-15). Original plan: `navsat_transform` (GPS lat/lon → meters on `/odometry/gps`, needs the IMU heading + `magnetic_declination_radians`; verify the sign by test, sim value ~−9.2° = −0.160 rad) + global EKF (`world_frame: map`, fuses `/odometry/gps` + same odom/IMU), publishes `map → odom`
   - Chunk C: tuning. ~~GPS jitter (process noise)~~ done. Optional leftovers (revisit if Nav2 struggles): obstacle wiggle in RViz on direction changes (Madgwick `gain`, wheel `vx` slip), try fusing accel
   - Chunk C (~1–2 h): tune + drive test (RViz pose should stay on Gazebo's)
   - Docs: [robot_localization](https://docs.ros.org/en/jazzy/p/robot_localization/), [Nav2 GPS tutorial](https://docs.nav2.org/tutorials/docs/navigation2_with_gps.html)
5. **Step 13: Nav2** against the simulated robot. Chunks: ~~(1) Nav2 running, click goal in RViz~~, ~~(2) costmaps from `/scan`, drive around the box~~, ~~(3) curb lidar in the costmap~~ done 2026-11-15, ~~(4) GPS waypoints (lat/lon goals)~~ done 2026-11-17, ~~(5) Collision Monitor: curb lidar~~ done 2026-11-17 (stop zone + tuning deferred to the real robot model). Ramp + terrain classifier v1 → **winter break** (design items above). Docs: [Nav2 getting started](https://docs.nav2.org/getting_started/index.html)
6. **Step 16:** ~~chassis mesh, sensor layout, footprint, ME spec~~ done 2026-11-23. Wheel size from ME done 2026-11-24. Left: ground clearance, axle spacing, wheel count from ME (re-check ride height + curb lidar tilt), collision box with the wedge, cross-check the EE parts list and fill in datasheet sizes ([sensor-mounting.md](sensor-mounting.md)).
7. ~~Team handoff doc for EE + ME~~ done 2026-11-24 (`Clark - DE5.pdf`). Register for InCORS; finalize parts with EE.
8. **Before the presentation:** a more complicated `test_world` (e.g. curb with a curb cut, sidewalks, pedestrian-sized obstacles), update the GPS waypoint route, screen-record the demo.
9. Winter break: navigation weights / costmap tuning, Collision Monitor fix + stop zone, Step 14 (OSM campus world + `map` tilt fix), Step 15 (Route Server, click-to-go), ramp + terrain classifier.
10. Spring: custom PCBs / micro-ROS, sim → real.

## Gotchas so far

- Nav2 default params assume `base_footprint` and `/odom`. Grep for both when adapting them.
- A costmap that's missing an obstacle the other one has = robot stuck (planner and controller disagree).
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
- Empty `ros2 node list` while things clearly run = stale ROS daemon. `ros2 daemon stop`, then list again (first run after restart can be partial; run twice). `--no-daemon` also works but may miss slow nodes
- `with rclpy.init():` is Kilted/Rolling only. In Jazzy `rclpy.init()` returns None → `TypeError: 'NoneType' object does not support the context manager protocol`. Use `try/except/finally` + `rclpy.try_shutdown()`. Check the docs URL says **jazzy**
- `cos`/`sin` need `math.` (NameError only shows when the line runs, i.e. on the first message)
- A topic name in a YAML/launch file that isn't in `ros2 topic list` = silent failure. Check with `ros2 topic list | grep <name>`
- Frame conversions: test at 2+ orientations. One matching reading proves nothing
- Obstacles moving in RViz (Fixed Frame `odom`) = localization error made visible
- `/usr/bin/env: 'python3\r'` = Windows CRLF line endings. `file <script>` shows "with CRLF line terminators". Fix: `sed -i 's/\r$//' <file>`; `.gitattributes` keeps it LF
- Python scripts in an `ament_cmake` package: `install(PROGRAMS ... DESTINATION lib/${PROJECT_NAME})` + `chmod +x`. `install(DIRECTORY)` puts them in `share/` → `ros2 run` says no executable found
- Simple Commander `getFeedback()` returns `None` until the first feedback arrives. Check before using `.current_waypoint`
- `ros2 node info` only shows current connections. Lazy nodes (e.g. `laserscan_to_pointcloud`) don't subscribe to their input until something subscribes to their output
- Collision Monitor: `scan` sources ignore height (2D), `pointcloud` sources filter by `min_height`/`max_height`. A tilted lidar needs the pointcloud route
- Collision Monitor only checks when a command arrives. Testing with teleop: remap to `cmd_vel_smoothed` and **hold** keys
- Collision Monitor `visualize` output shows in RViz, never in Gazebo
- Weird `/fromLL` result? Run `/toLL` on (0, 0) and compare to the world origin. Digit typos in lat/lon = km errors (0.01° ≈ 1.1 km)
- Inventor OBJ: **y-up** and origin wherever the CAD origin is. Read the vertex min/max (`v x y z` lines) to get size, units and origin before writing the URDF `<origin>`
- `--symlink-install` links the files that exist at build time. A **new** file (e.g. `chassis.mtl`) needs a rebuild
- Gazebo turns `package://pkg/...` into `model://pkg/...` and looks for `pkg/` inside each `GZ_SIM_RESOURCE_PATH` folder → append the package's share dir **parent** (`<share>/..`)
- After moving or adding any sensor: check no sensor sees the robot's own body (run with nothing around, look at `/scan`). A self-hit moves with the robot → Collision Monitor slows to 0, costmap marks the robot's own cells
- XML comments can't contain `--` or another comment. Comment out a block below its header comment
