"""Extract dimensions from gripper finger STL files for sleeve design."""
import trimesh
import numpy as np

files = {
    "link6 (gripper_motorized)": "../model/omx_f_mesh/follower_07_gripper_motorized.stl",
    "link7 (gripper_gear)":      "../model/omx_f_mesh/follower_08_gripper_gear.stl",
}

# URDF mount offsets relative to link5 (meters; STL is in mm with scale 0.001)
mounts_mm = {
    "link6 (gripper_motorized)": np.array([29.5,  7.5, 0.0]),
    "link7 (gripper_gear)":      np.array([29.5, -10.8, 0.0]),
}

for name, path in files.items():
    m = trimesh.load(path)
    # STL native units assumed mm (URDF scales 0.001 → meters)
    bb_min, bb_max = m.bounds
    size = bb_max - bb_min
    print(f"\n=== {name} ===")
    print(f"  file: {path}")
    print(f"  vertices: {len(m.vertices)}, faces: {len(m.faces)}, watertight: {m.is_watertight}")
    print(f"  bbox min (mm): {bb_min}")
    print(f"  bbox max (mm): {bb_max}")
    print(f"  size  X×Y×Z (mm): {size[0]:.2f} × {size[1]:.2f} × {size[2]:.2f}")
    print(f"  centroid (mm): {m.centroid}")
    print(f"  mount on link5 (mm): {mounts_mm[name]}")

    # Cross-sections along X (finger length axis) — show width(Y) and height(Z)
    xs = np.linspace(bb_min[0] + 1e-3, bb_max[0] - 1e-3, 9)
    print(f"  cross-sections along X (finger length):")
    print(f"    {'x(mm)':>8} {'Ywidth':>8} {'Zheight':>8} {'Ymin':>8} {'Ymax':>8} {'Zmin':>8} {'Zmax':>8}")
    for x in xs:
        try:
            sec = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
            if sec is None:
                continue
            planar, _ = sec.to_2D()
            pts = planar.vertices  # 2D points in plane (Y,Z roughly)
            ymin, zmin = pts.min(axis=0); ymax, zmax = pts.max(axis=0)
            print(f"    {x:8.2f} {ymax-ymin:8.2f} {zmax-zmin:8.2f} {ymin:8.2f} {ymax:8.2f} {zmin:8.2f} {zmax:8.2f}")
        except Exception as e:
            print(f"    x={x:.2f}: section failed ({e})")

# Distance between fingers
gap = mounts_mm["link6 (gripper_motorized)"][1] - mounts_mm["link7 (gripper_gear)"][1]
print(f"\n=== Geometry summary ===")
print(f"  finger pivot spacing in Y (mm): {gap:.2f}  (link6_y - link7_y)")
print(f"  finger pivot X from link5 (mm): 29.5")
print(f"  rotation axis: Z (mimic, symmetric)")
