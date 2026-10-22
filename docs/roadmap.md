# Roadmap

Plan for the campus UGV, from simulation to a real robot. Written 2026-10-21.
Current progress: [session-resume.md](session-resume.md).

## End goal

- A Gazebo simulation of **our campus in 3D**, with the sidewalk network laid out.
- **Click any point on campus** → the robot plans the **shortest sidewalk route** and drives it, avoiding obstacles and handling curbs.
- The same software runs on the **real robot (Raspberry Pi 5)** with as few changes as possible.

## Decisions

| Topic | Decision | Status |
|---|---|---|
| Main computer | Raspberry Pi 5, 8 GB | Have it |
| Obstacle sensing | **1 × 360° 2D lidar** on top (e.g. RPLIDAR C1, LDRobot LD19) | Decided |
| Curb detection | Depth camera (e.g. OAK-D Lite) **or** 2nd 2D lidar tilted down | Open: compare both in sim |
| Cameras | 2 × Pi Camera Module 3 (wide) on the Pi's 2 CSI ports | Planned |
| Vision acceleration | Raspberry Pi AI HAT+ (Hailo), for camera detection only | Planned |
| Localization | **RTK GPS** (e.g. u-blox ZED-F9P) + IMU + wheel odometry | **Planned, budget TBD** |
| Motor control | ESP32 running micro-ROS → motor controller | Planned |
| Drivetrain | **2 tank treads (tracks), one per side, 2 motors per track** (4 motors total), skid-steer | Decided (changed 2026-10-22 from 4 wheels); dimensions TBD |

### Why these choices

- **One 360° lidar** instead of several front/rear lidars: full coverage with one device, less Pi CPU and USB load, lower cost.
- **A 2D lidar can't see curbs**: it scans one horizontal plane. Curbs need a sensor that looks down at the ground ahead.
- **RTK GPS**: standard GPS is accurate to ~2–5 m, but sidewalks are ~1.5–3 m wide. RTK gets ~cm accuracy using correction data (free NTRIP services exist in many US states).
  - If RTK doesn't fit the budget, fallback: standard GPS + heavier reliance on lidar and odometry. Expect worse lane-keeping on narrow sidewalks.
- **Tracked skid-steer**: good traction and contact area for curbs. Tracks skid even more than wheels when turning, so track/encoder odometry drifts badly in turns; the IMU (and GPS) correct heading.
  - Software-wise it's still a differential drive: both motors on a track get the same command, so the robot is controlled as "left side speed / right side speed".
  - Sim approach (open): start by approximating each track with several wheels per side (simple, works with the DiffDrive plugin). Try Gazebo's tracked-vehicle plugins later if needed for curb tests.
- **URDF/xacro** for the robot model (not SDF): Nav2 and ROS tools need it, and Fusion 360 dimensions and meshes drop in later as variables.
- **The AI HAT only speeds up neural-network vision.** Nav2, lidar processing, and localization still run on the Pi CPU. It uses the Pi 5's only PCIe port.

## System architecture

```
Raspberry Pi 5  (Nav2, robot_localization, perception)
 ├── USB:  360° lidar, curb sensor, RTK GPS   ← high-bandwidth, straight to the Pi
 ├── CSI:  2 × cameras
 ├── PCIe: AI HAT+
 └── USB serial: ESP32 (micro-ROS)
       ├── motor controller → motors
       ├── wheel encoders   → odometry
       ├── IMU (or on the Pi)
       └── e-stop + watchdog (stop motors if commands stop)
```

- The ESP32 handles **realtime** jobs only. It is too slow to pass lidar or camera data through.
- The watchdog matters: Gazebo's DiffDrive keeps the last command forever (see [gazebo-basics-log.md](gazebo-basics-log.md), Step 5).

## Navigation design

| Layer | Tool | Job |
|---|---|---|
| Route (global) | **Nav2 Route Server** (`nav2_route`) on a sidewalk graph from OpenStreetMap | Shortest path along sidewalks: "past the library, then left" |
| Local | Nav2 controller + rolling-window costmap | Follow the route, avoid people and obstacles |
| Localization | `robot_localization` (EKF + `navsat_transform`) | Fuse GPS + IMU + odometry into one position |

- Sidewalk graph source: OpenStreetMap `highway=footway` ways. Our campus is mapped reasonably well.
- A full-campus global costmap would be too large. Use a **rolling window**, a small grid that moves with the robot.
- To check: `apt-cache policy ros-jazzy-nav2-route` (confirm the Route Server is packaged for Jazzy).

## Budget (target: under $1000, Pi already covered)

Rough prices. Check current listings before buying.

| Item | Approx. |
|---|---|
| 360° 2D lidar | $70–100 |
| Curb sensor (depth camera / 2nd lidar) | $70–150 |
| 2 × Pi Camera Module 3 | $50–70 |
| AI HAT+ | $70–130 |
| RTK GPS + antenna | $200–300 |
| IMU | ~$25 |
| **Sensors + compute subtotal** | **~$500–775** |
| Chassis, motors, motor controller, battery, ESP32, wiring | **remaining ~$225–500** |

- **Risk:** curb traversal needs high-torque motors and a sturdy chassis. Price the drivetrain early.
- **Open:** whether RTK fits. Bring to the team.

## Phases

### Phase 1: Simulation

| Step | Goal | Status |
|---|---|---|
| 1–7 | Gazebo + ROS 2 basics: bridge, teleop, odometry | Done |
| 8 | TF in RViz | Done |
| 9 | Add an IMU to `vehicle_blue` (copy in `src/robot_sim/worlds/`) | Done |
| 10 | Tracked skid-steer robot (tracks approximated as wheels per side) as a ROS package + URDF/xacro, placeholder dimensions; move the IMU onto it | Next |
| 11 | Add GPS (`navsat` sensor) | |
| 12 | `robot_localization`: fuse GPS + IMU + odometry | |
| 13 | Nav2 on the simulated robot (GPS waypoints) | |
| 14 | Swap in real dimensions and CAD meshes from Fusion 360; add 360° lidar, cameras, and curb sensor options; compare curb sensors | |
| 15 | Build the campus world (OSM + elevation → mesh → Gazebo) | |
| 16 | Sidewalk route graph from OSM + Nav2 Route Server; click-to-go | |

### Phase 2: Hardware

- `ros2_control` hardware interface so sim and real use the same controllers and launch files.
- ESP32 firmware (micro-ROS): motors, encoders, watchdog, e-stop.
- Custom PCBs (KiCad).
- Hardware-in-the-loop testing: real ESP32 and motors, simulated world.
- Multi-arch Docker image (amd64 for PCs, arm64 for the Pi).

### Phase 3 (optional): LLM goal planner

- Small local LLM turns requests ("go to the library") into goals. Not in the realtime loop.

## Open questions

- [ ] Does RTK GPS fit the budget? Is there a free NTRIP service near campus?
- [ ] Curb sensor: depth camera or tilted lidar? Decide after the sim comparison.
- [ ] Drivetrain: motors, controller, chassis that can climb curbs within budget.
- [ ] Is `nav2_route` packaged for Jazzy?

## References

- [Nav2 GPS navigation tutorial](https://docs.nav2.org/tutorials/docs/navigation2_with_gps.html)
- [nav2_route (Jazzy)](https://docs.ros.org/en/jazzy/p/nav2_route)
- [robot_localization](https://docs.ros.org/en/jazzy/p/robot_localization/)
- [Gazebo Harmonic sensors](https://gazebosim.org/docs/harmonic/sensors/)
- [ros2_control](https://control.ros.org/jazzy/index.html)
- [micro-ROS](https://micro.ros.org/docs/overview/features/)
- [OpenStreetMap](https://www.openstreetmap.org)
