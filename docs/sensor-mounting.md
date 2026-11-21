# Sensor mounting spec (for the ME team)

Where each sensor goes on the robot, and why. Written 2026-11-21. **Draft**: positions are from the simulation's placeholder body and will change with the real chassis.
Related: [roadmap.md](roadmap.md) (decisions), [sim-to-real.md](sim-to-real.md) (EE interface).

## Reference frame

- Measure every sensor from **one point: the chassis center** (`base_link`).
- Axes ([REP 103](https://www.ros.org/reps/rep-0103.html)): **x forward, y left, z up**. Meters and degrees.
- `base_footprint` = the ground directly under the chassis center (z = 0). Heights below are from the ground.

## Current sim positions (placeholder body 0.60 × 0.40 × 0.20 m, top at 0.25 m)

Source: [`ugv_sensors.xacro`](../src/ugv_description/urdf/ugv_sensors.xacro).

| Sensor | Where | x (m) | z above ground (m) | Angle |
|---|---|---|---|---|
| 360° lidar | Top center | 0 | 0.27 (scan plane) | Level |
| Curb lidar (2D, tilted) | Front edge, centered | +0.31 | 0.23 | 13° down |
| Front camera | Front edge, centered | +0.31 | 0.24 | Level, facing forward |
| Rear camera | Rear edge, centered | −0.31 | 0.24 | Level, facing back |
| GPS antenna | Top, behind center | −0.15 | 0.25 | Facing up |
| IMU + magnetometer | Center | 0 | 0.25 | Aligned with robot axes |

All sensors are at y = 0 (centered left/right).

## Mounting rules (these matter more than the numbers)

- **360° lidar:** highest thing on the robot. Nothing at its height for a full 360° (no posts, mast, or antenna in the scan plane).
- **Curb lidar:** must hit the ground **~1 m ahead**. Distance ahead = height ÷ tan(tilt). If the height changes, change the tilt to keep ~1 m. Clear view ±60° forward and down. **Mount rigidly:** 1° of tilt error moves the line ~0.1 m.
- **Cameras:** clear view forward / back, nothing in the lower part of the frame (wide lens, ~102° horizontal).
- **GPS antenna:** clear sky view, on a ground plane if the antenna needs one, not under or next to the lidar.
- **IMU + magnetometer:** near the center, rigid, axes lined up with the robot. **Keep away from motors, battery, and high-current wires.** They distort the compass and the heading.

## What we need back from ME

- Final x / y / z and angle of every sensor, from the chassis center.
- Overall robot size (L × W × H), track size and spacing, mass estimate.
- Meshes: chassis and tracks as **separate** files (see below).

## Part dimensions (fill in when the EE parts list is final)

| Part | Model | Size (L × W × H mm) | Mounting holes | Weight | Sensing point (scan plane / lens center) | Datasheet |
|---|---|---|---|---|---|---|
| 360° lidar | TBD | | | | | |
| Curb lidar | TBD | | | | | |
| Cameras (×2) | Pi Camera Module 3 Wide? | | | | | |
| GPS + antenna | TBD | | | | | |
| IMU | TBD | | | | | |

## EE parts list check (what the software assumes)

- 360° lidar: 2D, range ≥ 12 m, USB
- Curb lidar: 2D, short minimum range, USB
- GPS: **RTK-capable** (sim uses ~2 cm accuracy; standard GPS is ~2 m)
- IMU: **9-axis with magnetometer** (heading depends on it)
- Cameras: CSI, wide angle

## CAD → sim meshes

- **Visual:** OBJ exported from Inventor. If colors are lost or the file is huge, clean up in Blender (Decimate) and export OBJ or DAE.
- **Collision:** simple boxes / cylinders, not the mesh (detailed collision meshes slow Gazebo down).
- **Units:** STL/OBJ have no units, Inventor exports in mm. URDF uses meters → `scale="0.001 0.001 0.001"`.
- **Origin:** put the mesh origin at the chassis center so it lines up with `base_link`.
- Docs: [URDF visual model](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Building-a-Visual-Robot-Model-with-URDF-from-Scratch.html), [collision + physical properties](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Adding-Physical-and-Collision-Properties-to-a-URDF-Model.html)
