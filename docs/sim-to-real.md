# Sim → real roadmap

What changes when this code moves from Gazebo to the real robot (Pi 5 + ESP32).
Written 2026-11-15. Related: [roadmap.md](roadmap.md) (big picture), [session-resume.md](session-resume.md) (progress).

## The short version

- **Same:** the overall design. Dual EKF, `navsat_transform`, Madgwick, Nav2 (later).
- **Delete:** the sim-only "glue" nodes that fix Gazebo quirks.
- **Replace:** Gazebo + bridge → real sensor drivers + ESP32 (micro-ROS).
- **Re-measure:** every number that came from the sim (noise, declination, sizes, covariances).
- **Need from EE team:** an agreed list of topics, message types, units, frames and rates (the "interface contract" below).

```
SIM                                   REAL
Gazebo ──► ros_gz_bridge ──► ROS      sensors ──► drivers on Pi ──────► ROS
                                      ESP32   ──► micro-ROS agent ────► ROS
```

---

## Part 1: what I change in this repo

### Sim-only pieces → remove on the real robot

| Piece | Why it exists | Real robot |
|---|---|---|
| `ros_gz_bridge`, `ros_gz_sim create`, Gazebo | Sim | Gone. Replaced by drivers + micro-ROS agent |
| `odom_cov_relay` | Gazebo DiffDrive odom has 0 covariance | ESP32 (or `diff_drive_controller`) publishes odom **with** covariance |
| `gps_cov_relay` | Gazebo NavSat has 0 covariance | u-blox driver fills real covariance. Drop node + `('gps/fix', '/gps/fix_cov')` remap |
| `mag_relay` | Gazebo mag is gauss + NED + 108.4° rotation | Real IMU driver gives tesla + ENU. Drop node, point Madgwick at the real mag topic |
| `<gazebo>` blocks in the xacro | Gazebo plugins + sensors | Ignored on the real robot, but move them to a separate `ugv_gazebo.xacro` so the real URDF is clean |
| GPS noise props (`gps_h_std_deg`) | Gazebo noise is in degrees | Not used |

### Settings that were tuned for the sim → redo on the real robot

| Setting | Sim value | Real robot |
|---|---|---|
| `use_sim_time` | `true` (yaml + launch) | `false`. Make it a launch argument instead of hard-coded |
| `magnetic_declination_radians` | `+0.1606` (Gazebo's ~9.2°) | Campus ≈ 5° (NOAA). **Redo the drive test for the sign** |
| `yaw_offset` | `0.0` | Depends on the real IMU's "0°" (east or north?). Check with a compass |
| Global EKF process noise x, y | `0.001` | Retune with real GPS (jumps more near buildings) |
| Wheel odom covariance | `TWIST_DIAG` guesses | Measure: drive straight 10 m, spin 360°, compare |
| GPS covariance | 0.0004 (2 cm, RTK fixed) | From the driver. Check it **grows** when RTK drops to float/standard |
| IMU noise | Guessed MEMS values | From the datasheet, or measure at rest |
| Madgwick `orientation_stddev` | 0.05 | Retune after mag calibration |
| Robot size, sensor positions | Placeholders | Real Fusion 360 measurements (roadmap Step 16) |
| Collision Monitor zones | Only `FootprintApproach` (creeps, can touch) | Add a `stop` polygon (+ maybe `slowdown`) sized from real braking distance and top speed. Recheck that the curb lidar keeps short obstacles in view until contact |

### New things to add

| What | Notes |
|---|---|
| `real.launch.py` (new bringup) | `robot_state_publisher` + sensor drivers + micro-ROS agent + `localization.launch.py` with `use_sim_time:=false` |
| Sensor drivers | 360° lidar + curb lidar (e.g. `rplidar_ros` / `ldlidar` driver), GPS (e.g. `ublox_dgnss`), Pi cameras (e.g. `camera_ros`) |
| `micro_ros_agent` | Talks to the ESP32 over USB serial |
| NTRIP client | Feeds RTK corrections to the GPS (needs internet: Wi-Fi or phone hotspot) |
| udev rules | Fixed device names (`/dev/lidar`, `/dev/curb_lidar`, `/dev/gps`, `/dev/esp32`) so USB order doesn't matter |
| Docker for the Pi | arm64 image, pass through the USB devices (`devices:` in `compose.yaml`) |
| Frame names | Every driver's `frame_id` must match a URDF link (`lidar_link`, `curb_lidar_link`, `gps_link`, `imu_link`, ...) |

---

## Part 2: what I need from the EE team (Pi + ESP32 board)

**First decision, together:** how the ESP32 talks to ROS.

| Option | ESP32 does | Pi does | Notes |
|---|---|---|---|
| **A: micro-ROS, simple** | Reads `/cmd_vel`, does the diff-drive math, publishes odom | Nothing extra | Fastest to get working |
| **B: `ros2_control`** | Only wheel speeds in, encoder ticks out | `diff_drive_controller` does the math + odom | Same controller in sim and real (roadmap Phase 2 plan). More setup |

The interface contract below assumes **A**. If we pick **B**, the motor/odom rows change to "wheel velocity command in, wheel position/velocity out".

### Interface contract: ESP32 ↔ Pi

| Direction | Topic | Message type | Units / frame | Rate | Notes |
|---|---|---|---|---|---|
| Pi → ESP32 | `/cmd_vel` | `geometry_msgs/Twist` | m/s, rad/s | ~10–20 Hz | Only `linear.x` and `angular.z` used |
| ESP32 → Pi | `/wheel/odom` | `nav_msgs/Odometry` | m, m/s, rad/s. `frame_id: odom`, `child_frame_id: base_link` | 30–50 Hz | **Covariance filled in** (not zeros). **Do not publish TF**, the EKF owns `odom → base_link` |
| ESP32 → Pi | `/imu/data_raw` | `sensor_msgs/Imu` | rad/s, m/s². `frame_id: imu_link`. ROS axes: x forward, y left, z up | 50–100 Hz | Orientation not needed (Madgwick does it): set `orientation_covariance[0] = -1`. Fill gyro/accel covariance |
| ESP32 → Pi | `/imu/mag` | `sensor_msgs/MagneticField` | **tesla** (not gauss). Same axes as the IMU | 50 Hz | Calibrated (see below) |
| ESP32 → Pi | `/bumper` | `std_msgs/Bool` | — | On change + ~1 Hz | Firmware already cut the motors before this is sent |
| ESP32 → Pi | `/battery` | `sensor_msgs/BatteryState` | V, A | ~1 Hz | Nice to have |
| ESP32 → Pi | `/estop` | `std_msgs/Bool` | — | On change + ~1 Hz | So Nav2 knows why it isn't moving |

If the IMU ends up on the **Pi** (I2C) instead of the ESP32, same topics and units, just a different publisher.

### Firmware behavior I'm counting on

- [ ] **Watchdog:** no `/cmd_vel` for ~0.5 s → motors stop. (Gazebo keeps the last command forever; real hardware must not.)
- [ ] **E-stop and bump switches cut the motors in firmware/hardware**, not through ROS.
- [ ] **Time sync** with the micro-ROS agent, so message timestamps match the Pi's clock. The EKF drops or mis-fuses messages with bad stamps.
- [ ] Odom from **encoders**, not from commanded speed.
- [ ] Both motors on one track get the same command (skid-steer = left speed / right speed).

### Numbers I need (to put in the URDF and configs)

| Number | Used for |
|---|---|
| Encoder counts per motor revolution + gear ratio | Ticks → meters |
| Drive sprocket radius (effective track radius) | Ticks → meters |
| Track separation (center to center) | Turning math. We'll also measure the *effective* value with a spin test, since tracks slip |
| Max safe speed and acceleration | Nav2 limits + firmware limits |
| IMU part number + datasheet | Noise values, axis directions |
| IMU position + orientation on the board, and the board's position in the chassis | `imu_joint` in the URDF |
| GPS antenna position | `gps_joint` (sim has it 0.15 m behind center) |
| Lidar + curb lidar positions and tilt angle | `lidar_joint`, `curb_lidar_joint` (13° tilt in sim) |
| Robot mass, rough center of mass | URDF inertia, Nav2 tuning |

### Magnetometer: highest risk item

The heading bug we just fixed in sim shows how much a bad compass breaks GPS fusion.

- [ ] Mount it **away from motors, motor wires, and the battery** (≥ 10–15 cm if possible). Mast or top plate is best.
- [ ] Run a **hard-iron + soft-iron calibration** with the robot fully assembled, motors powered.
- [ ] Check the heading doesn't jump when the motors start.

### Pi / power / wiring

- [ ] Stable 5 V / 5 A to the Pi 5 (brownouts while motors draw current = random reboots).
- [ ] USB: 360° lidar, curb lidar, GPS, ESP32 (4 devices). Powered hub if needed.
- [ ] GPS antenna on top, clear sky view, with a ground plane.
- [ ] 2 CSI cameras + AI HAT (PCIe) fit together physically.
- [ ] Internet on the robot for RTK corrections (NTRIP).

---

## Part 3: bring-up order on the real robot

One layer at a time. Same checks as in sim (see [quick-commands.md](quick-commands.md)).

1. **Bench, wheels off the ground:** micro-ROS agent connects, `/cmd_vel` spins the tracks the right way, watchdog stops them.
2. **Each sensor alone:** `ros2 topic hz`, `ros2 topic echo --once`, check units and `frame_id`. IMU at rest: accel z ≈ +9.8.
3. **TF:** `robot_state_publisher` with real measurements. Check every sensor frame in RViz.
4. **Teleop** on the ground. Odom distance vs a tape measure (10 m).
5. **Mag calibration**, then Madgwick heading vs a phone compass.
6. **Local EKF** (`odom → base_link`). Drive a square, check it closes.
7. **GPS outside:** RTK fix status, covariance, `/odometry/gps` near (0, 0) at start.
8. **Declination drive test** (same as sim): EKF track vs GPS track should agree.
9. **Global EKF** (`map → odom`), then Nav2.

---

## Open questions

- [ ] micro-ROS simple (A) or `ros2_control` (B)?
- [ ] IMU on the ESP32 board or on the Pi?
- [ ] Which exact IMU, lidars, and GPS module? (drivers + datasheets)
- [ ] Encoder type and resolution?
- [ ] How does the robot get internet for RTK?
