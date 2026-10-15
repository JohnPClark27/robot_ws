# Session resume notes

Written 2026-10-15 so work can continue on another computer.
Related: [gazebo-basics-log.md](gazebo-basics-log.md) (full command log), [quick-commands.md](quick-commands.md) (cheat sheet).

## Where I am

Working through Gazebo Harmonic + ROS 2 Jazzy basics in the Docker container.
Currently on **Step 8: get TF into RViz**. RViz shows no TF data yet.

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
- [x] Wrote docs in `docs/` (uncommitted at the time of writing; check `git status`)

## In progress: Step 8, TF in RViz

Goal: see the robot's frames moving in RViz.

Last instruction given: add a TF bridge to the bridge command:

```bash
ros2 run ros_gz_bridge parameter_bridge \
  /model/vehicle_blue/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist \
  /model/vehicle_blue/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry \
  /model/vehicle_blue/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V \
  --ros-args -r /model/vehicle_blue/tf:=/tf
```

(Use the exact TF topic name from `gz topic -l | grep -i tf`. The remap must come after `--ros-args`, at the end.)

Then `rviz2`, set Fixed Frame to the odom frame, Add → TF.

**Problem:** RViz receives no TF data.

### Last debugging prompt (run these and report back)

```bash
gz topic -l | grep -i tf                 # does Gazebo publish a TF topic? exact name?
gz topic -e -t <that topic> -n 1         # does it carry data?
ros2 topic list | grep tf                # is /tf on the ROS side?
ros2 topic info /tf                      # bridge should be 1 publisher
ros2 topic echo /tf --once               # does data arrive?
```

| Result | Likely cause |
|---|---|
| No TF topic in Gazebo | World doesn't publish TF; check `tf_topic` in `diff_drive.sdf` |
| Gazebo has data, no `/tf` in ROS | Bridge arg wrong or remap in the wrong place |
| `/tf` has data, RViz empty | Fixed Frame name wrong, or TF display not added |
| `/tf` empty | Sim paused or robot hasn't moved |

To report back: exact bridge command, output of the checks above, RViz Fixed Frame value and its status.

## Resume on a new computer

1. Install Docker (see README), clone the repo, `docker compose build`.
2. Start the container and open 3 to 4 terminals (see [quick-commands.md](quick-commands.md)).
3. Launch `gz sim -r diff_drive.sdf`, then the bridge command above, then teleop.
4. Continue with the TF debugging checks.

## Planned next steps

1. Finish TF in RViz (Step 8).
2. Add a sensor (IMU, then GPS) to the robot SDF and bridge it.
3. Set up `robot_localization` to fuse GPS + IMU + odometry.
4. Bring up Nav2 against the simulated robot.
5. Later: Fusion 360 → URDF for the real robot, then custom PCBs / micro-ROS.

## Gotchas so far

- Bridge direction: `[` Gazebo→ROS, `]` ROS→Gazebo, `@` both.
- DiffDrive keeps the last command; stop with a zero Twist.
- Teleop speed keys `q`/`z` change speed 10% per press. Restart teleop to reset.
- Teleop only reads keys when its terminal has focus.
- Always check pub/sub counts with `ros2 topic info` before assuming the sim is broken.
