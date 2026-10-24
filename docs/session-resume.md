# Session resume notes

Written 2026-10-15 so work can continue on another computer. Updated 2026-10-21 (new machine), 2026-10-23 (Step 10 progress), 2026-10-24 (ugv drivable).
Related: [roadmap.md](roadmap.md) (end goal + plan), [gazebo-basics-log.md](gazebo-basics-log.md) (full command log), [quick-commands.md](quick-commands.md) (cheat sheet).

## Where I am

Working through Gazebo Harmonic + ROS 2 Jazzy basics in the Docker container.
**Step 10: drivetrain done.** My own robot (`ugv_description` package) spawns in Gazebo, drives with `teleop_twist_keyboard`, and shows up in RViz (saved config) on sim time.
Next: **sensors on the ugv, starting with the IMU** written into the URDF/xacro, then 360° lidar → camera → GPS. See [roadmap.md](roadmap.md).

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
  - Known quirk: DiffDrive odom is 2D (z = 0), so `base_link` sits at ground level in RViz (robot looks half-sunk). Fix later with a `base_footprint` frame ([REP 105](https://www.ros.org/reps/rep-0105.html))

## Frames (`ugv`)

| Frame | Published by | Meaning |
|---|---|---|
| `odom` | DiffDrive → bridge → `/tf` | Fixed start point of odometry. RViz Fixed Frame |
| `base_link` | DiffDrive (`odom` → `base_link`) | Robot body center |
| `left_/right_wheel_{front,middle,rear}` | `robot_state_publisher` (from `/joint_states`) | Wheels |
| `map` | Not yet | Comes later from localization / Nav2 |

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
4. Terminal 1: `ros2 launch ugv_description sim.launch.py` (Gazebo + robot_state_publisher + spawn + bridge). Or `display.launch.py` for RViz only.
5. Extra terminals (host `jpcli@`): check `docker ps` shows exactly one container, then `docker exec` into it and `source install/setup.bash` (see [quick-commands.md](quick-commands.md)).
6. RViz with the saved config + teleop: see [quick-commands.md](quick-commands.md).
7. Continue with sensors: IMU in the ugv xacro.

## Notes for the group demo (2026-10-22)

- Drivetrain changed: **tank treads**, one per side, each driven by 2 motors. See [roadmap.md](roadmap.md).
- Demo scope: robot + sensors (lidar, camera, IMU, GPS) visualized in RViz, **teleoperated**. No autonomous nav yet.
- Part 2 if time allows: rough 3D campus map from OpenStreetMap (separate from the robot).
- Show **screen recordings** (record on the faster machine); live demo on the slower laptop only if asked.

## Planned next steps

1. ~~Finish TF in RViz (Step 8).~~ Done.
2. ~~Step 9: IMU.~~ Done.
3. Step 10: ~~package~~, ~~URDF/xacro body + 6 wheels~~, ~~spawn in Gazebo~~, ~~DiffDrive~~, ~~JointStatePublisher~~, ~~bridge~~, ~~teleop + RViz~~, ~~save RViz config~~. Remaining:
   - Sensors: **IMU (next)** → 360° lidar → camera → GPS. Each = a sensor link + fixed joint in the xacro, a `<gazebo reference=...>` sensor block, the world-level system plugin, and a bridge entry
   - Optional: start RViz from `sim.launch.py` with the saved config
   - Then obstacles in the world, record the demo
   - Try writing the sensor blocks myself from the [Gazebo sensors docs](https://gazebosim.org/docs/harmonic/sensors), using Step 9 as a template
4. Set up `robot_localization` to fuse GPS + IMU + odometry.
5. Bring up Nav2 against the simulated robot.
6. Later: Fusion 360 → URDF for the real robot, then custom PCBs / micro-ROS.

## Gotchas so far

- Bridge direction: `[` Gazebo→ROS, `]` ROS→Gazebo, `@` both.
- Bridge message types are case-sensitive (`gz.msgs.Pose_V`, not `Pose_v`). A bad type only breaks that one topic; check Terminal 1 for the error.
- Launch `remappings=` is a list of string tuples: `[('/from', '/to')]`. Unquoted topic names = Python syntax error.
- `package.xml` only lists dependencies. It never affects topic names.
- A topic in `ros2 topic list` only means it's advertised. Use `ros2 topic echo --once` / `hz` to confirm data.
- `gz topic -i -t <topic>` shows a Gazebo topic's message type. Query the exact name from `gz topic -l`.
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
- `msrdc.exe` on Windows is WSLg's Remote Desktop client that draws Linux GUI windows. Normal; don't kill it.
