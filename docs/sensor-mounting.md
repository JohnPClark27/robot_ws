# Sensor mounting spec (for the ME team)

**Draft (2026-11-24):** numbers will change once ME sends the real chassis and wheel dimensions.

## Reference point (datum)

- Measure every sensor from **one point: the center of the rear bottom edge of the main body** (see picture). Halfway across the rear face, where it meets the bottom.
- Directions are named by the robot, not by CAD axes (Inventor's x/y/z may point elsewhere):
  - **Forward** = toward the front wedge
  - **Left** = the robot's left side when facing forward (right side = negative)
  - **Up** = away from the ground
- Main units are inches (the CAD is in inches), mm in brackets. Angles in degrees.
- **Quick checks** against the model: top surface = Up 13.0 in. Main box ends at Forward 22.0 in. Wedge tip at Forward ≈ 32.0 in. Body sides at Left ±8.0 in.
- For software: the sim's chassis center (`base_link`) = datum + 11.0 in forward + 6.5 in up. I convert; ME doesn't need to.

## Sensor positions (estimated chassis, 2026-11-24)

Body from `chassis.obj`: main box 22 × 16 × 13 in (0.56 × 0.41 × 0.33 m) plus a 10 in (0.25 m) sloped wedge on the front.

**Wheels (from ME, 2026-11-24):** 5 in (0.127 m) diameter, 20 in (0.508 m) from the outside of the left wheels to the outside of the right wheels.
**Still estimated:** 6 wheels (3 per side), wheels right against the body sides (≈ 2 in wide), **~2 in (5 cm) ground clearance** (datum height above the ground). Positions below are from the datum, so they don't change if the clearance changes. Only the curb lidar **tilt** does (it depends on the height above the ground).

| Sensor | Point measured | Forward | Left | Up | Angle |
|---|---|---|---|---|---|
| 360° lidar | Center of the scan plane (riser base on the top surface: Up 13.0 in) | 11.0 in (280 mm) | 0 | 15.75 in (400 mm) | Level |
| Curb lidar (2D, tilted) | Sensor center, on the wedge face | 26.0 in (660 mm) | 0 | 8.1 in (205 mm) | 14° down |
| Front-left camera | Lens center, on top of the wedge ridge | 22.4 in (570 mm) | +7.3 in (185 mm) | 13.5 in (342 mm) | Level, turned 45° left |
| Front-right camera | Lens center, on top of the wedge ridge | 22.4 in (570 mm) | −7.3 in (−185 mm) | 13.5 in (342 mm) | Level, turned 45° right |
| GPS antenna | Base of the antenna, on the top surface | 5.5 in (140 mm) | 0 | 13.0 in (330 mm) | Facing up |
| IMU + magnetometer | Board center, just under the top lid | 11.0 in (280 mm) | 0 | ~12.6 in (320 mm) | Board axes lined up with the robot (one axis forward, one left) |

## Mounting rules (these matter more than the numbers)

- 360° lidar: highest point on the robot, on a 5 cm riser. **Nothing in the scan plane** (Up 15.75 in from the datum, ~0.45 m above the ground) for a full 360°: no mast, antenna or bracket, or the lidar sees the robot as an obstacle.
- Two front cameras, one on each corner, pointed out at 45°. Clear view with nothing in the lower part of the frame (wide lens, ~102° horizontal).
- GPS: puck on top, clear view of the sky, not right next to the lidar. Ground plane under it if the antenna needs one.
- IMU + magnetometer: near the middle, rigid, axes lined up with the robot. **Keep away from motors, battery and high-current wires**: they distort the compass and the heading.
- Curb lidar: must hit the ground ~1 m in front of it. **Tilt = atan(height above the ground ÷ 1 m)**: if the height changes, change the tilt. Clear view ±60° forward and down. **Mount rigidly:** 1° of tilt error moves the line ~10 cm.

## What we need back from ME

- Final Forward / Left / Up and angle of every sensor, from the datum.
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
