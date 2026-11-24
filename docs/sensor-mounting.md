# Sensor mounting spec (for the ME team)

**Draft (2026-11-23):** numbers will change once ME sends the real chassis and wheel dimensions.

## Reference frame

- Measure every sensor from **one point: the chassis center** (`base_link`).
- Axes: **x forward, y left, z up**. Meters and degrees.
- `base_footprint` = the ground directly under the chassis center (z = 0). Heights below are from the ground.

## Current sim positions (estimated chassis, 2026-11-23)

Source: [`ugv_sensors.xacro`](../src/ugv_description/urdf/ugv_sensors.xacro). Body from `chassis.obj`: main box 0.56 × 0.41 × 0.33 m plus a 0.25 m sloped wedge on the front. Chassis center (`base_link`) is the middle of the main box, 0.215 m above the ground. Body top at 0.38 m.

**Wheels (from ME, 2026-11-24):** 5 in (0.127 m) diameter, 20 in (0.508 m) from the outside of the left wheels to the outside of the right wheels.
**Still estimated:** 6 wheels (3 per side), axles at x = −0.22 / 0 / +0.22 m, wheels right against the body sides (≈ 2 in / 0.049 m wide), **5 cm ground clearance**. If the ground clearance changes, every height below moves with it, and the curb lidar tilt must be recalculated.

| Sensor | Where | x (m) | y (m) | z above ground (m) | Angle |
|---|---|---|---|---|---|
| 360° lidar | Top center, on a 5 cm riser | 0 | 0 | 0.45 (scan plane) | Level |
| Curb lidar (2D, tilted) | Wedge face, centered | +0.38 | 0 | 0.25 | 14° down |
| Front-left camera | Top of wedge ridge, left corner | +0.29 | +0.185 | 0.39 | Level, turned 45° left |
| Front-right camera | Top of wedge ridge, right corner | +0.29 | −0.185 | 0.39 | Level, turned 45° right |
| GPS antenna | Top, behind center | −0.14 | 0 | 0.38 (base of antenna) | Facing up |
| IMU + magnetometer | Center, just under the top lid | 0 | 0 | ~0.37 | Aligned with robot axes |

## Mounting rules (these matter more than the numbers)

- 360° lidar: highest point on the robot, on a 5 cm riser. **Nothing in the scan plane** (0.45 m) for a full 360°: no mast, antenna or bracket, or the lidar sees the robot as an obstacle.
- Two front cameras, one on each corner, pointed out at 45°. Clear view with nothing in the lower part of the frame (wide lens, ~102° horizontal).
- GPS: puck on top, clear view of the sky, not right next to the lidar. Ground plane under it if the antenna needs one.
- IMU + magnetometer: near the middle, rigid, axes lined up with the robot. **Keep away from motors, battery and high-current wires**: they distort the compass and the heading.
- Curb lidar: must hit the ground ~1 m in front of it. **Tilt = atan(height ÷ 1 m)**: if the height changes, change the tilt. Clear view ±60° forward and down. **Mount rigidly:** 1° of tilt error moves the line ~10 cm.

## What we need back from ME

- Final x / y / z and angle of every sensor, from the chassis center.
- Wheel count, width and axle positions, and the ground clearance (diameter and overall width received 2026-11-24).
- Overall robot size (L × W × H) and mass estimate.

## Part dimensions

| Part | Model | Size (L × W × H mm) | Mounting holes | Weight | Sensing point (scan plane / lens center) | Datasheet |
|---|---|---|---|---|---|---|
| 360° lidar | TBD | | | | | |
| Curb lidar | TBD | | | | | |
| Cameras (×2, front corners) | Pi Camera Module 3 Wide? | | | | | |
| GPS + antenna | TBD | | | | | |
| IMU | TBD | | | | | |

## EE parts list check (what the software assumes)

- 360° lidar: 2D, range ≥ 12 m, USB
- Curb lidar: 2D, short minimum range, USB
- GPS: **RTK-capable** (sim uses ~2 cm accuracy; standard GPS is ~2 m)
- IMU: **9-axis with magnetometer** (heading depends on it)
- Cameras: CSI, wide angle
