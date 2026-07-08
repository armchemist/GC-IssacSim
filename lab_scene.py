"""Lab scene decoration helpers for the OMX_F dual-rail simulation.

Shared by load_omx_f_dual_rail.py (viewer / USD generation) and
teleop_omx_dual_rail.py (physics). Pipeline:

  add_lab_environment(stage)  — reference an NVIDIA indoor environment USD
                                (Simple_Room), swap its rounded built-in table
                                for a plain rectangular bench, and return the
                                bench placement (center / top_z / size).
  add_lab_glassware(...)      — beakers, a test-tube rack, and test tubes on the
                                bench top, within the arms' reach. Beakers/tubes
                                are rigid bodies so they can be picked up.

The rail+arms are positioned by the URDF itself (world_to_rail_base is baked to
sit the rail on the bench top and run the full length of the bench's long (X)
edge, arms facing across toward -Y). Keep DEFAULT_BENCH here in sync with that
bake — see model/omx_f_dual_on_rail.urdf.

Everything is best-effort: if the NVIDIA asset server is unreachable the
environment is skipped and a default bench at the origin is used instead.
"""

from pxr import Usd, UsdGeom, UsdPhysics, UsdShade, Sdf, Gf

# Relative path of the indoor environment on the NVIDIA asset server.
ENV_REL_PATH = "/Isaac/Environments/Simple_Room/simple_room.usd"

# Bench sized so its long (X) edge holds the full 1.25 m rail + glassware.
# Must stay consistent with the placement baked into omx_f_dual_on_rail.urdf
# (rail centred on X, near +Y edge, top surface at top_z).
BENCH_SIZE = (1.3, 0.9)          # (x, y) metres — long edge is X
DEFAULT_BENCH = {"center": (0.0, 0.0), "top_z": 0.30, "size": BENCH_SIZE}


# ─────────────────────────── environment ────────────────────────────
def add_lab_environment(stage, prim_path="/World/Environment"):
    """Reference an NVIDIA indoor environment and build the lab bench.

    Returns a bench dict {center:(x,y), top_z, size:(sx,sy)} used by
    place_robot_on_bench() and add_lab_glassware(). Falls back to a default
    origin bench if the asset root cannot be resolved (offline).
    """
    try:
        from isaacsim.storage.native import get_assets_root_path
    except Exception:  # pragma: no cover - older layouts
        from omni.isaac.nucleus import get_assets_root_path  # type: ignore

    assets_root = get_assets_root_path()
    if not assets_root:
        print("[lab_scene] WARNING: assets root unresolved (offline?) — "
              "skipping NVIDIA environment, using default bench.")
        return add_rect_table(stage, DEFAULT_BENCH["center"],
                              DEFAULT_BENCH["top_z"], DEFAULT_BENCH["size"])[1]

    env_usd = assets_root + ENV_REL_PATH
    env_prim = stage.DefinePrim(prim_path, "Xform")
    env_prim.GetReferences().AddReference(env_usd)
    print(f"[lab_scene] Environment referenced: {env_usd}")

    # The referenced environment may carry its own PhysicsScene; a second
    # PhysicsScene fights the robot's. Deactivate any env-side ones.
    _disable_nested_physics_scenes(stage, prim_path)

    # Swap Simple_Room's rounded table for a plain rectangular bench.
    return replace_env_table_with_bench(stage, prim_path)


def _disable_nested_physics_scenes(stage, root_path):
    root = Sdf.Path(root_path)
    for prim in stage.Traverse():
        if prim.GetPath().HasPrefix(root) and prim.IsA(UsdPhysics.Scene):
            prim.SetActive(False)
            print(f"[lab_scene] Disabled nested PhysicsScene: {prim.GetPath()}")


def replace_env_table_with_bench(stage, env_root="/World/Environment"):
    """Deactivate the environment's built-in table(s) and build our own plain
    rectangular bench at a fixed, known spot (DEFAULT_BENCH).

    We intentionally do NOT reuse the env table's bounding box for placement:
    the referenced table geometry is not reliably bounded at this point in
    startup (empty bbox -> garbage coordinates). A fixed bench is robust and
    the arms/glassware are positioned relative to it.
    """
    root = Sdf.Path(env_root)
    tables = []
    for prim in stage.Traverse():
        path = prim.GetPath()
        if not path.HasPrefix(root):
            continue
        if "table" not in prim.GetName().lower():
            continue
        if any(path.HasPrefix(t.GetPath()) for t in tables):
            continue  # nested mesh under a table group already captured
        tables.append(prim)

    for tprim in tables:
        tprim.SetActive(False)
        print(f"[lab_scene] Deactivated env table {tprim.GetPath()}")
    if not tables:
        print("[lab_scene] No env table prim found (nothing to hide).")

    _, bench = add_rect_table(stage, DEFAULT_BENCH["center"],
                              DEFAULT_BENCH["top_z"], DEFAULT_BENCH["size"],
                              path="/World/LabBench")
    print(f"[lab_scene] Built bench at {bench['center']} top_z={bench['top_z']}")
    return bench


# ──────────────────────────── materials ─────────────────────────────
def _get_or_create_preview_material(stage, mtl_path, diffuse,
                                    opacity=1.0, roughness=0.5, metallic=0.0):
    if stage.GetPrimAtPath(mtl_path).IsValid():
        return UsdShade.Material.Get(stage, mtl_path)
    material = UsdShade.Material.Define(stage, mtl_path)
    shader = UsdShade.Shader.Define(stage, mtl_path + "/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(*diffuse))
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface")
    return material


def _wood_material(stage):
    return _get_or_create_preview_material(
        stage, "/World/Looks/BenchWood", (0.55, 0.38, 0.22), roughness=0.6)


def _glass_material(stage):
    return _get_or_create_preview_material(
        stage, "/World/Looks/Glass", (0.70, 0.85, 0.90),
        opacity=0.25, roughness=0.1)


def _plastic_material(stage):
    return _get_or_create_preview_material(
        stage, "/World/Looks/RackPlastic", (0.10, 0.35, 0.55), roughness=0.4)


# ─────────────────────────── box primitive ──────────────────────────
def _make_box(stage, path, size, translate, material=None, collider=True):
    """Axis-aligned box from a unit cube scaled to `size`, centred at
    `translate`. Static collider by default."""
    cube = UsdGeom.Cube.Define(stage, path)
    cube.CreateSizeAttr(1.0)
    cube.CreateExtentAttr([(-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)])
    xf = UsdGeom.Xformable(cube)
    xf.AddTranslateOp().Set(Gf.Vec3d(*translate))
    xf.AddScaleOp().Set(Gf.Vec3f(size[0], size[1], size[2]))
    prim = cube.GetPrim()
    if collider:
        UsdPhysics.CollisionAPI.Apply(prim)
    if material is not None:
        UsdShade.MaterialBindingAPI(prim).Bind(material)
    return prim


def add_rect_table(stage, center_xy, top_z, footprint,
                   path="/World/LabBench", top_thick=0.04, leg=0.06):
    """Rectangular table: top slab + four legs (static collider).

    Returns (root_prim, bench_dict). `bench_dict` = {center, top_z, size}.
    """
    cx, cy = center_xy
    sx, sy = footprint
    material = _wood_material(stage)
    root = UsdGeom.Xform.Define(stage, path)

    # Top slab, upper face at top_z.
    _make_box(stage, f"{path}/top", (sx, sy, top_thick),
              (cx, cy, top_z - top_thick * 0.5), material)

    # Legs from floor to underside of slab.
    leg_h = max(0.05, top_z - top_thick)
    ix = sx * 0.5 - leg * 0.5
    iy = sy * 0.5 - leg * 0.5
    for sxn, xl in ((-1, "nx"), (1, "px")):
        for syn, yl in ((-1, "ny"), (1, "py")):
            _make_box(stage, f"{path}/leg_{xl}_{yl}", (leg, leg, leg_h),
                      (cx + sxn * ix, cy + syn * iy, leg_h * 0.5), material)

    bench = {"center": (cx, cy), "top_z": top_z, "size": (sx, sy)}
    return root.GetPrim(), bench


# ──────────────────────────── glassware ─────────────────────────────
def _spawn_rigid_cylinder(stage, path, pos, radius, height, mass, material):
    cyl = UsdGeom.Cylinder.Define(stage, path)
    cyl.CreateAxisAttr("Z")
    cyl.CreateRadiusAttr(radius)
    cyl.CreateHeightAttr(height)
    cyl.CreateExtentAttr([(-radius, -radius, -height / 2.0),
                          (radius, radius, height / 2.0)])
    UsdGeom.Xformable(cyl).AddTranslateOp().Set(Gf.Vec3d(*pos))
    prim = cyl.GetPrim()
    UsdPhysics.CollisionAPI.Apply(prim)
    UsdPhysics.RigidBodyAPI.Apply(prim)
    UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(mass)
    UsdShade.MaterialBindingAPI(prim).Bind(material)
    return prim


def spawn_beakers(stage, positions, parent_path="/World/Beakers",
                  radius=0.03, height=0.08, mass=0.05):
    """Translucent rigid-body cylinders (beakers). `positions` are the centres
    of each beaker's base (bottom sits at z, body rises upward)."""
    stage.DefinePrim(parent_path, "Scope")
    material = _glass_material(stage)
    prims = []
    for i, (x, y, z) in enumerate(positions):
        prims.append(_spawn_rigid_cylinder(
            stage, f"{parent_path}/beaker_{i}", (x, y, z + height * 0.5),
            radius, height, mass, material))
    print(f"[lab_scene] Spawned {len(prims)} beakers")
    return prims


def add_test_tube_rack(stage, center_xy, top_z, n=5, path="/World/TubeRack"):
    """Static rack: base slab + four posts + a top border frame. Returns the
    (x, y) slot centres where test tubes should stand."""
    cx, cy = center_xy
    mat = _plastic_material(stage)
    UsdGeom.Xform.Define(stage, path)

    spacing = 0.030
    width = spacing * n + 0.02      # x extent
    depth = 0.055                   # y extent
    base_t = 0.012
    post_h = 0.10
    bar = 0.008

    # Base slab sitting on the bench top.
    _make_box(stage, f"{path}/base", (width, depth, base_t),
              (cx, cy, top_z + base_t * 0.5), mat)

    ix = width * 0.5 - bar * 0.5
    iy = depth * 0.5 - bar * 0.5
    # Four corner posts.
    for sxn, xl in ((-1, "nx"), (1, "px")):
        for syn, yl in ((-1, "ny"), (1, "py")):
            _make_box(stage, f"{path}/post_{xl}_{yl}", (bar, bar, post_h),
                      (cx + sxn * ix, cy + syn * iy, top_z + post_h * 0.5), mat)
    # Top border frame (holds tubes upright, reads as slotted rack).
    ztop = top_z + post_h
    _make_box(stage, f"{path}/rail_ny", (width, bar, bar), (cx, cy - iy, ztop), mat)
    _make_box(stage, f"{path}/rail_py", (width, bar, bar), (cx, cy + iy, ztop), mat)
    _make_box(stage, f"{path}/rail_nx", (bar, depth, bar), (cx - ix, cy, ztop), mat)
    _make_box(stage, f"{path}/rail_px", (bar, depth, bar), (cx + ix, cy, ztop), mat)

    x0 = cx - spacing * (n - 1) * 0.5
    slots = [(x0 + i * spacing, cy) for i in range(n)]
    print(f"[lab_scene] Test-tube rack with {n} slots at {center_xy}")
    return slots, top_z + base_t


def spawn_test_tubes(stage, slots, stand_z, parent_path="/World/TestTubes",
                     radius=0.007, height=0.12, mass=0.02):
    """Thin rigid-body cylinders standing in the rack slots."""
    stage.DefinePrim(parent_path, "Scope")
    material = _glass_material(stage)
    prims = []
    for i, (x, y) in enumerate(slots):
        prims.append(_spawn_rigid_cylinder(
            stage, f"{parent_path}/tube_{i}", (x, y, stand_z + height * 0.5),
            radius, height, mass, material))
    print(f"[lab_scene] Spawned {len(prims)} test tubes")
    return prims


def add_lab_glassware(stage, bench):
    """Place a test-tube rack (+tubes) and a few beakers on the bench top,
    inside the arms' reach in front of the rail.

    The rail runs along the bench long (X) edge near the back (+Y); both arms
    reach across toward -Y. Items are spread along X (the cart drives to them)
    at y ~0.05–0.12 (about 0.2 m in front of the rail)."""
    if bench is None:
        return
    cx, cy = bench["center"]
    top_z = bench["top_z"]

    rack_center = (cx - 0.20, cy + 0.10)
    slots, stand_z = add_test_tube_rack(stage, rack_center, top_z, n=5)
    spawn_test_tubes(stage, slots, stand_z)

    spawn_beakers(stage, [
        (cx + 0.10, cy + 0.12, top_z),
        (cx + 0.22, cy + 0.05, top_z),
        (cx - 0.05, cy + 0.05, top_z),
    ])
