# OMX_F gripper finger dimensions

Source: STL analysis of `omx_f_mesh/follower_07_gripper_motorized.stl` (link6) and `follower_08_gripper_gear.stl` (link7), cross-referenced with `omx_f.urdf`. All units mm.

Reference these numbers when designing any gripper attachment (sleeve, jig, sensor mount, swap tool) instead of re-analyzing STLs.

## Mounting (from URDF, relative to link5)
- link6 pivot: xyz = (29.5, 7.5, 0), axis Z, mimic master
- link7 pivot: xyz = (29.5, -10.8, 0), axis Z, mimic of link6 ×(-1)
- Pivot Y spacing: 18.3 mm
- Both fingers symmetric (mirror in Y); link6 has motor housing, link7 has gear.

## Finger geometry (finger-local frame, X = length, pivot at X=0)
Total bbox: ~75 × 20 × ~42 mm (X × Y × Z, watertight).

| Zone | X range (mm) | Y width | Z height | Notes |
|---|---|---|---|---|
| Pivot shaft | -10 to 0 | ~4 | ~0 (axle) | rotation axis |
| Housing block | 0 to ~22 | ~40 | ~18 | motor/gear body — DO NOT cover |
| Grip blade (taper) | 22 to 65 | 35 → 14 | 8 → 5 | usable for attachments |
| Tip | 65 | 14 | <1 | flat edge |

### Blade cross-sections (link6, symmetrized half-extents)
| Finger-local X | half_Y | half_Z |
|---|---|---|
| 22 (blade base) | 18.5 | 5.0 |
| 28              | 16.5 | 3.8 |
| 36              | 14.0 | 3.2 |
| 46              | 11.0 | 3.5 |
| 55              | 8.0  | 3.2 |
| 62              | 7.5  | 1.6 |
| 65 (tip)        | 7.0  | 1.2 |

## Inner / outer face convention
- link6 "inner" (gripping) face = local **−Y** (faces partner finger at link7).
- link7 "inner" face = local **+Y** (mirror of link6).
- Closing direction at zero rotation: along link5's Y axis.

## Joint limits (URDF)
All revolute, effort 1000, velocity 4.8 rad/s, range ±2π:
joint1 (base yaw, Z), joint2/3/4 (pitch, Y), joint5 (roll, X), gripper_joint_1/2 (Z, mimic).

## Related files
- `analyze_gripper.py` — STL analysis script (re-run from this folder)
- `gripper_sleeve.scad` — parameterized slide-on sleeve (covers blade x=22..65)
- `../omx_f.urdf` — robot model
- `../omx_f_mesh/follower_07_*.stl`, `follower_08_*.stl` — finger meshes
