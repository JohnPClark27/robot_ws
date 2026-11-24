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
| Obstacle sensing | **1 × 360° 2D lidar** on top: **Slamtec RPLIDAR C1** (USB to the Pi) | Decided. Model proposed 2026-11-24, finalize with EE |
| Curb detection | **2nd 2D lidar, tilted down** (~14° on the real chassis, ground line ~1 m ahead): a **second RPLIDAR C1** (same driver) | Decided 2026-11-09 after sim comparison (cost). Model proposed 2026-11-24 |
| Cameras | 2 × **Pi Camera Module 3 Wide** on the Pi's 2 CSI ports, front corners at ±45°, for pedestrian/vehicle detection. Need 2 × **Pi 5 camera cables** (22-pin to 15-pin) | Proposed 2026-11-24 |
| Vision acceleration | Raspberry Pi AI HAT+ (Hailo), for camera detection only | Planned |
| Localization | **RTK GPS**: SparkFun GPS-RTK2 (u-blox ZED-F9P) + u-blox all-band antenna, USB to the Pi. **IMU + mag**: Adafruit BNO085 on the ESP32 (SPI or UART, not I²C). + wheel encoders | **RTK decided 2026-11-24.** Models proposed, finalize with EE. Check GPS ↔ antenna band match before ordering |
| Motor control | ESP32 running micro-ROS → motor controller. Motors **with quadrature encoders** (ME + EE pick) | Planned |
| E-stop + power | Hardware E-stop and power supply (incl. the Pi's 5 V) | **EE team owns it** |
| Drivetrain | **2 tank treads (tracks), one per side, 2 motors per track** (4 motors total), skid-steer | Decided (changed 2026-10-22 from 4 wheels). **2026-11-24: ME gave 5 in (0.127 m) wheels, 20 in (0.508 m) outside to outside. Confirm: tracks over these wheels, or plain wheels? How many per side?** |
| CAD → sim meshes | ME team models in **Autodesk Inventor**. Visual meshes as **OBJ** (or DAE via Blender), collision as simple boxes | Decided 2026-11-21 |

### Why these choices

- **One 360° lidar** instead of several front/rear lidars: full coverage with one device, less Pi CPU and USB load, lower cost.
- **A 2D lidar can't see curbs**: it scans one horizontal plane. Curbs need a sensor that looks down at the ground ahead.
  - Confirmed in sim: a 0.20 m curb is invisible to the top lidar (scan plane ~0.27 m above ground).
- **Tilted 2nd lidar for curbs (not a depth camera)**: chosen for cost (~$70–100 vs ~$300+ for a depth camera) and light Pi CPU load. Both were simulated (2026-11-09) and both detect the curb.
  - Trade-off: the tilted lidar sees the curb only where its scan line crosses it (~1 m ahead). Once the robot is closer, the curb edge is out of the scan, so Nav2's costmap has to remember it (obstacle marking with persistence).
  - Shallow 13–14° mount is sensitive to pitch: 1° of tilt (bumps, mounting error) moves the line ~0.1 m. Mount rigidly.
  - Depth camera stays in the sim as a fallback / comparison option.
- **RTK GPS** (decided 2026-11-24): standard GPS is accurate to ~2–5 m, but sidewalks are ~1.5–3 m wide. RTK gets ~cm accuracy using correction data.
  - Corrections: Indiana's **InCORS** network (INDOT) is free over NTRIP (RTCM 3.x), but needs a signed **RTK user agreement** before they send login details. **Register early**: approval isn't instant. [incors.in.gov/rtk.aspx](https://incors.in.gov/rtk.aspx)
- **Tracked skid-steer**: good traction and contact area for curbs. Tracks skid even more than wheels when turning, so track/encoder odometry drifts badly in turns; the IMU (and GPS) correct heading.
  - Software-wise it's still a differential drive: both motors on a track get the same command, so the robot is controlled as "left side speed / right side speed".
  - Sim approach (open): start by approximating each track with several wheels per side (simple, works with the DiffDrive plugin). Try Gazebo's tracked-vehicle plugins later if needed for curb tests.
- **URDF/xacro** for the robot model (not SDF): Nav2 and ROS tools need it, and CAD dimensions and meshes (Inventor, OBJ) drop in as variables.
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
       ├── IMU + magnetometer (BNO085, SPI or UART)
       ├── bump switches   → cut motors in firmware, publish /bumper
       └── e-stop + watchdog (stop motors if commands stop). E-stop hardware + power: EE team
```

- The ESP32 handles **realtime** jobs only. It is too slow to pass lidar or camera data through.
- The watchdog matters: Gazebo's DiffDrive keeps the last command forever (see [gazebo-basics-log.md](gazebo-basics-log.md), Step 5).
- **Bump switches are not simulated.** They're a last-resort safety stop, so they belong as low in the stack as possible: the ESP32 firmware cuts the motors directly instead of waiting on ROS → Nav2. In sim, prevention is handled by Nav2's Collision Monitor (lidar/point cloud) instead. Fake a bump for testing with `ros2 topic pub --once /bumper std_msgs/msg/Bool "{data: true}"`.

## Navigation design

| Layer | Tool | Job |
|---|---|---|
| Route (global) | **Nav2 Route Server** (`nav2_route`) on a sidewalk graph from OpenStreetMap | Shortest path along sidewalks: "past the library, then left" |
| Local | Nav2 controller + rolling-window costmap | Follow the route, avoid people and obstacles |
| Localization | `robot_localization` (EKF + `navsat_transform`) | Fuse GPS + IMU + odometry into one position |

- Sidewalk graph source: OpenStreetMap `highway=footway` ways. Our campus is mapped reasonably well.
- A full-campus global costmap would be too large. Use a **rolling window**, a small grid that moves with the robot.
- To check: `apt-cache policy ros-jazzy-nav2-route` (confirm the Route Server is packaged for Jazzy).

## Time estimate (2026-11-15)

Based on measured pace: smooth chunks ~20–40 min, debugging chunks 1–2 h. One session ≈ 2–3 h.

| Step | Hours |
|---|---|
| 13.4 GPS waypoints | 1–1.5 |
| 13.5 Collision Monitor | 0.5–1 |
| 13.x Test ramp + terrain classifier v1 (v2 with medium costs: +4–8) | 2–4 |
| 14 Campus world (OSM + elevation) | 6–12 |
| 15 Sidewalk routing, click-to-go | 6–10 |
| 16 Real dimensions + CAD | 2–4 |
| **Phase 1 left** | **~16–28** (+2–4 classifier) |
| Phase 2 hardware (my side, plus waiting on the EE team) | 20–45 |
| Phase 3 LLM planner (optional) | 4–8 |

## Semester plan (2026-11-21)

End-of-semester milestone is due ~2026-11-26. Goal: a technically and visually impressive demo, plus handoff docs for the EE and ME teams. Phase 1 left (~16–28 h) doesn't fit, so it's split:

**This weekend (2026-11-21/22)**
1. **Step 16 first (2–4 h):** Inventor meshes into the URDF; sensor mounting spec for the ME team ([sensor-mounting.md](sensor-mounting.md)). Re-place sensors once ME gives real positions.
2. **Step 14, minimal (4–8 h):** campus world from OSM, **flat ground** (buildings + sidewalks). Elevation only if time is left.
   - Fix the ~9.2° `map` frame tilt first (~1 h), or the robot looks off the sidewalk in RViz.
3. **Demo run (1 h):** GPS waypoints (Step 13 chunk 4) along a real campus sidewalk. Looks like click-to-go without the Route Server. **Screen-record it** as a backup for the presentation.

**Weekday evenings:** team handoff doc (what's built, system diagram, ME spec, EE needs from [sim-to-real.md](sim-to-real.md), next steps).

**Winter break**
- Step 15: Route Server + click-to-go
- Elevation in the campus world (if skipped)
- Test ramp + terrain classifier (ramps, steps, drop-offs)
- Collision Monitor stop zone + tuning (needs the real robot model)
- Optional EKF tuning leftovers

**Spring:** Phase 2, sim → real with the whole team.

**Update 2026-11-24 (DE5 handoff, `Clark - DE5.pdf`):** milestone moved to the team meeting, presentation is a couple of weeks out. Plan changed:
- **Done:** Step 16 part 1 (chassis mesh, sensor layout, ME spec from the rear-bottom datum), system diagram, proposed parts list for EE.
- **Dropped for now:** the OSM campus world (Step 14) and the `map` tilt fix → winter break.
- **Before the presentation:** a more complicated `test_world` to show off navigation, plus a screen recording.
- **Winter break:** navigation weights / costmap tuning (needs custom code, more time to learn), plus the list above.
- **Waiting on hardware:** most sim and micro-ROS work. Then only tweaks from ME and EE input.

## Budget (target: under $1000, Pi already covered)

Proposed parts (DE5, 2026-11-24). Prices are list prices from the retailer pages; check before buying.

| Item | Approx. |
|---|---|
| 360° lidar: Slamtec RPLIDAR C1 | $69 |
| Curb lidar: 2nd RPLIDAR C1 | $69 |
| 2 × Pi Camera Module 3 Wide ($38.50 each) | $77 |
| 2 × Pi 5 camera cable, 22-pin to 15-pin ($2.70 each) | ~$5 |
| RTK GPS: SparkFun GPS-RTK2 (ZED-F9P) | $260 (was on sale for $208) |
| GPS antenna: u-blox all-band (ANN-MB2), 5 m cable | $120 |
| IMU + mag: Adafruit BNO085 | $29.50 |
| Bump switches | ~$5 |
| **Sensors subtotal** | **~$635** |
| AI HAT+ | $70–130 |
| **Sensors + compute subtotal** | **~$705–765** |
| Chassis, motors (with encoders), motor controller, battery, ESP32, wiring | **remaining ~$235–295** |

- **Risk:** curb traversal needs high-torque motors and a sturdy chassis. Price the drivetrain early.
- **Parked (2026-11-24, not a worry yet):** 5 in wheels (6.35 cm radius) climb roughly a step no taller than their radius, with ~5 cm ground clearance. Revisit if curb climbing comes back into scope.
- **RTK:** decided (2026-11-24). Budget above includes it.

## Phases

### Phase 1: Simulation

| Step | Goal | Status |
|---|---|---|
| 1–7 | Gazebo + ROS 2 basics: bridge, teleop, odometry | Done |
| 8 | TF in RViz | Done |
| 9 | Add an IMU to `vehicle_blue` (copy in `src/robot_sim/worlds/`) | Done |
| 10 | Tracked skid-steer robot (tracks approximated as wheels per side) as a ROS package + URDF/xacro, placeholder dimensions; move the IMU onto it | Sim sensors complete (2026-11-09): drives with teleop, RViz config saved, IMU with noise (2026-10-24); 360° lidar + front/rear cameras (2026-11-07); own world `test_world.sdf` with obstacles, curb lidar + depth cam, magnetometer (2026-11-09). Bump sensors moved to Phase 2 (firmware) |
| 11 | Add GPS (`navsat` sensor) | Done (2026-11-09): `/gps/fix`, campus origin in `<spherical_coordinates>`, RTK-level noise |
| 12 | `robot_localization`: fuse GPS + IMU + odometry (+ magnetometer heading) | Done (2026-11-15). Local EKF (`odom → base_link`), `mag_relay` + Madgwick absolute yaw, `navsat_transform` (declination +0.1606 verified), `gps_cov_relay`, global EKF (`map → odom`), process noise tuned. Optional tuning leftovers in [session-resume.md](session-resume.md) |
| 13 | Nav2 on the simulated robot (GPS waypoints); Collision Monitor (slow/stop from lidar + curb lidar) | In progress. Chunks 1–3 done (2026-11-15): `ugv_navigation`, goals from RViz, avoids box, curb lidar in both costmaps (voxel layers), `base_footprint`. Next: GPS waypoints, Collision Monitor. Design item: drop-off step detector |
| 14 | Build the campus world (OSM + elevation → mesh → Gazebo) | **Winter break** (dropped from the semester plan 2026-11-24). Before the presentation: a more complicated `test_world` instead |
| 15 | Sidewalk route graph from OSM + Nav2 Route Server; click-to-go | **Winter break.** Semester demo uses GPS waypoints instead |
| 16 | Swap in real dimensions and CAD meshes from Inventor (OBJ); re-place 360° lidar, cameras, tilted curb lidar to match the real mounts | **Part 1 done (2026-11-23/24):** chassis mesh, 5 in wheels from ME, sensor layout, ME spec from the rear-bottom datum ([sensor-mounting.md](sensor-mounting.md)). Left: ground clearance + axle spacing from ME, real sensor sizes once parts are ordered |

### Phase 2: Hardware

Detailed checklist (code changes + what the EE team needs to provide): [sim-to-real.md](sim-to-real.md).

- `ros2_control` hardware interface so sim and real use the same controllers and launch files.
- ESP32 firmware (micro-ROS): motors, encoders, watchdog, e-stop.
- Bump switches → ESP32 firmware motor cut-off (+ `/bumper` `std_msgs/Bool` for logging/recovery). Decide count and placement with the chassis design.
- Custom PCBs (KiCad).
- Hardware-in-the-loop testing: real ESP32 and motors, simulated world.
- Multi-arch Docker image (amd64 for PCs, arm64 for the Pi).

### Future work: GPS keepout zones (stay off the grass)

Idea (2026-11-24): a georeferenced map of where the robot may and may not drive, so the planner **never considers** grass, flower beds, roads or building entrances. No custom code needed for the Nav2 side; it's configuration plus a map image.

- **Nav2 Keepout Filter** (a "costmap filter"): a **filter mask** (a black/white PGM image + YAML, like a normal map) marks forbidden areas as lethal in both costmaps. The planner and controller treat them like walls. A **Speed Filter** uses the same kind of mask for slow zones (crowded walkways, near doors).
- **Building the mask:** sidewalk polygons from OpenStreetMap, or traced on aerial imagery in QGIS → convert lat/lon to `map` x/y with the same origin as `navsat_transform` → rasterize (white = allowed, black = keepout, ~0.1 m per pixel). A small Python script can do it.
- **Prerequisites (do these first):**
  - **Fixed GPS datum:** `navsat_transform` has `wait_for_datum: false` today, so the `map` origin is wherever the robot gets its first GPS fix and moves every run. A mask needs a fixed origin: set `wait_for_datum: true` + `datum: [lat, lon, heading]`.
  - **`map` frame tilt fix** (~9.2° magnetic vs true, see [session-resume.md](session-resume.md)): a mask drawn in true east/north would be rotated against the tilted `map` frame.
  - **RTK:** with ~2 cm accuracy, a mask can follow a 1.5–3 m sidewalk. Standard GPS (~2 m) couldn't.
- **How it fits with the rest:** the Route Server (Step 15) picks *which* sidewalks to follow, the keepout mask makes sure it can't cut across the grass, and the terrain classifier (below) handles curbs and drop-offs the map doesn't know about. Only the classifier needs custom code (a node, or a C++ costmap layer for v2).
- Sim first: draw a mask for `test_world` (e.g. block one side of the curb) and check the planner routes around it.
- Docs: [Nav2 Keepout Filter tutorial](https://docs.nav2.org/tutorials/docs/navigation2_with_keepout_filter.html), [Speed Filter](https://docs.nav2.org/tutorials/docs/navigation2_with_speed_filter.html), [navsat_transform datum](https://docs.ros.org/en/jazzy/p/robot_localization/navsat_transform_node.html)

### Phase 3 (optional): LLM goal planner

- Small local LLM turns requests ("go to the library") into goals. Not in the realtime loop.

## Open questions

- [x] Does RTK GPS fit the budget? Is there a free NTRIP service near campus? **Yes** (2026-11-24): RTK decided, Indiana InCORS is free (registration).
- [x] Curb sensor: depth camera or tilted lidar? **Tilted 2D lidar** (cost), decided 2026-11-09 after the sim comparison.
- [ ] Drivetrain: motors, controller, chassis that can climb curbs within budget.
- [ ] Is `nav2_route` packaged for Jazzy?
- [ ] Curbs: climb them (project goal) or only use curb cuts? Decides whether a detected edge means "stop" or "slow down and climb".
- [ ] Terrain classifier on the curb lidar: label flat / ramp / small step / ledge / drop by shape (slope + jumps), mark only unsafe edges. Small steps (2–7 cm) = medium cost (needs a C++ costmap layer, v2). Thresholds from real lidar + real curbs. Also: long uphills look like walls to the 360° lidar.
- [ ] Max climbable step height and slope (up and down) for the real drivetrain.
- [ ] Keepout mask source: OSM sidewalks or hand-traced from aerial imagery? Who maintains it when campus changes?

## References

- [Nav2 GPS navigation tutorial](https://docs.nav2.org/tutorials/docs/navigation2_with_gps.html)
- [nav2_route (Jazzy)](https://docs.ros.org/en/jazzy/p/nav2_route)
- [robot_localization](https://docs.ros.org/en/jazzy/p/robot_localization/)
- [Gazebo Harmonic sensors](https://gazebosim.org/docs/harmonic/sensors/)
- [ros2_control](https://control.ros.org/jazzy/index.html)
- [micro-ROS](https://micro.ros.org/docs/overview/features/)
- [OpenStreetMap](https://www.openstreetmap.org)
