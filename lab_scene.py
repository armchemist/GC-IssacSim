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

import math

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


def _metal_material(stage):
    return _get_or_create_preview_material(
        stage, "/World/Looks/Metal", (0.75, 0.76, 0.78),
        roughness=0.25, metallic=1.0)


def _dark_material(stage):
    return _get_or_create_preview_material(
        stage, "/World/Looks/DarkPlastic", (0.06, 0.06, 0.07), roughness=0.5)


# Distinct reagent liquid colours, keyed by name so materials are shared.
_REAGENT_COLORS = {
    "red":    (0.80, 0.12, 0.12),
    "blue":   (0.12, 0.30, 0.85),
    "green":  (0.12, 0.65, 0.25),
    "amber":  (0.85, 0.55, 0.10),
    "purple": (0.55, 0.15, 0.70),
}


def _reagent_material(stage, name):
    c = _REAGENT_COLORS[name]
    return _get_or_create_preview_material(
        stage, f"/World/Looks/Reagent_{name}", c, opacity=0.85, roughness=0.2)


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


# ─────────────────────── reagent zone (left) ────────────────────────
def add_reagent_shelf(stage, center_xy, top_z, colors=None,
                      path="/World/ReagentShelf"):
    """A small two-level shelf with a row of colour-coded reagent bottles
    (rigid bodies, graspable). Returns the bottle prims."""
    if colors is None:
        colors = ["red", "blue", "green", "amber", "purple"]
    cx, cy = center_xy
    wood = _wood_material(stage)
    UsdGeom.Xform.Define(stage, path)

    n = len(colors)
    spacing = 0.055
    width = spacing * n + 0.03
    depth = 0.10
    board_t = 0.010
    shelf_h = 0.14

    # Back board + one raised shelf board, so bottles read as "on a stand".
    _make_box(stage, f"{path}/back", (width, board_t, shelf_h),
              (cx, cy + depth * 0.5, top_z + shelf_h * 0.5), wood)
    _make_box(stage, f"{path}/shelf", (width, depth, board_t),
              (cx, cy, top_z + shelf_h * 0.55), wood)

    # Front row of bottles on the bench top, back row on the raised shelf.
    x0 = cx - spacing * (n - 1) * 0.5
    prims = []
    for i, col in enumerate(colors):
        x = x0 + i * spacing
        # front bottle (bench top)
        prims.append(_make_reagent_bottle(
            stage, f"{path}/bottle_front_{i}", (x, cy - 0.03), top_z, col))
        # back bottle (raised shelf), alternate colour
        col2 = colors[(i + 2) % n]
        prims.append(_make_reagent_bottle(
            stage, f"{path}/bottle_back_{i}", (x, cy + 0.015),
            top_z + shelf_h * 0.55 + board_t * 0.5, col2))
    print(f"[lab_scene] Reagent shelf with {len(prims)} bottles at {center_xy}")
    return prims


def _make_reagent_bottle(stage, path, xy, stand_z, color,
                         radius=0.016, height=0.075, cap_h=0.016, mass=0.06):
    """Colour-coded reagent bottle = coloured body cylinder + dark cap, as one
    rigid body."""
    x, y = xy
    UsdGeom.Xform.Define(stage, path)
    body_mat = _reagent_material(stage, color)
    cap_mat = _dark_material(stage)

    body = UsdGeom.Cylinder.Define(stage, f"{path}/body")
    body.CreateAxisAttr("Z")
    body.CreateRadiusAttr(radius)
    body.CreateHeightAttr(height)
    body.CreateExtentAttr([(-radius, -radius, -height / 2.0),
                           (radius, radius, height / 2.0)])
    UsdGeom.Xformable(body).AddTranslateOp().Set(
        Gf.Vec3d(0, 0, stand_z + height * 0.5))
    UsdShade.MaterialBindingAPI(body.GetPrim()).Bind(body_mat)

    cap = UsdGeom.Cylinder.Define(stage, f"{path}/cap")
    cap.CreateAxisAttr("Z")
    cap.CreateRadiusAttr(radius * 0.6)
    cap.CreateHeightAttr(cap_h)
    cap.CreateExtentAttr([(-radius, -radius, -cap_h / 2.0),
                          (radius, radius, cap_h / 2.0)])
    UsdGeom.Xformable(cap).AddTranslateOp().Set(
        Gf.Vec3d(0, 0, stand_z + height + cap_h * 0.5))
    UsdShade.MaterialBindingAPI(cap.GetPrim()).Bind(cap_mat)

    # Rigid body on the parent Xform; children are its collision/visual shapes.
    root = stage.GetPrimAtPath(path)
    UsdGeom.Xformable(root).AddTranslateOp().Set(Gf.Vec3d(x, y, 0))
    UsdPhysics.CollisionAPI.Apply(body.GetPrim())
    UsdPhysics.CollisionAPI.Apply(cap.GetPrim())
    UsdPhysics.RigidBodyAPI.Apply(root)
    UsdPhysics.MassAPI.Apply(root).CreateMassAttr(mass)
    return root


# ───────────────────────── scale / balance ──────────────────────────
def add_scale(stage, center_xy, top_z, path="/World/Scale"):
    """A digital-balance prop: dark base body + a small raised display panel +
    a round metal weighing platform. Returns the platform top Z so a beaker can
    be set on it."""
    cx, cy = center_xy
    dark = _dark_material(stage)
    metal = _metal_material(stage)
    UsdGeom.Xform.Define(stage, path)

    base_w, base_d, base_h = 0.20, 0.16, 0.04
    _make_box(stage, f"{path}/base", (base_w, base_d, base_h),
              (cx, cy, top_z + base_h * 0.5), dark)
    # Slanted display panel at the back.
    _make_box(stage, f"{path}/display", (0.12, 0.015, 0.045),
              (cx, cy + base_d * 0.5 - 0.02, top_z + base_h + 0.022), metal)

    # Round weighing platform.
    plat_z = top_z + base_h
    plat_h = 0.008
    plat_r = 0.06
    plat = UsdGeom.Cylinder.Define(stage, f"{path}/platform")
    plat.CreateAxisAttr("Z")
    plat.CreateRadiusAttr(plat_r)
    plat.CreateHeightAttr(plat_h)
    plat.CreateExtentAttr([(-plat_r, -plat_r, -plat_h / 2.0),
                           (plat_r, plat_r, plat_h / 2.0)])
    UsdGeom.Xformable(plat).AddTranslateOp().Set(
        Gf.Vec3d(cx, cy - 0.01, plat_z + plat_h * 0.5))
    UsdPhysics.CollisionAPI.Apply(plat.GetPrim())
    UsdShade.MaterialBindingAPI(plat.GetPrim()).Bind(metal)

    platform_top = plat_z + plat_h
    print(f"[lab_scene] Scale at {center_xy}, platform_top={platform_top:.3f}")
    return (cx, cy - 0.01), platform_top


# ────────────────────────── tripod camera ───────────────────────────
def add_tripod_camera(stage, foot_xy, floor_z=0.0, head_z=0.55,
                      look_at=(0.0, 0.0, 0.35), path="/World/TripodCamera"):
    """A camera on a tripod standing on the floor beside the bench. Three
    splayed legs + a camera body + lens, plus a real UsdGeomCamera aimed at
    `look_at`. Returns the camera prim."""
    fx, fy = foot_xy
    metal = _metal_material(stage)
    dark = _dark_material(stage)
    UsdGeom.Xform.Define(stage, path)

    # Three legs splayed out from the apex at (fx, fy, head_z).
    leg_r = 0.008
    spread = 0.18
    for i in range(3):
        ang = math.radians(90 + i * 120)
        footx = fx + spread * math.cos(ang)
        footy = fy + spread * math.sin(ang)
        midx, midy = (fx + footx) * 0.5, (fy + footy) * 0.5
        length = math.sqrt((footx - fx) ** 2 + (footy - fy) ** 2 + head_z ** 2)
        leg = UsdGeom.Cylinder.Define(stage, f"{path}/leg_{i}")
        leg.CreateAxisAttr("Z")
        leg.CreateRadiusAttr(leg_r)
        leg.CreateHeightAttr(length)
        leg.CreateExtentAttr([(-leg_r, -leg_r, -length / 2.0),
                              (leg_r, leg_r, length / 2.0)])
        xf = UsdGeom.Xformable(leg)
        xf.AddTranslateOp().Set(Gf.Vec3d(midx, midy, floor_z + head_z * 0.5))
        # tilt leg so it spans apex -> foot
        tilt = math.degrees(math.atan2(spread, head_z))
        xf.AddRotateXYZOp().Set(Gf.Vec3f(
            -tilt * math.sin(ang), tilt * math.cos(ang), 0.0))
        UsdShade.MaterialBindingAPI(leg.GetPrim()).Bind(metal)

    # Camera body + lens at the apex.
    _make_box(stage, f"{path}/body", (0.09, 0.06, 0.06),
              (fx, fy, floor_z + head_z), dark)
    lens_r, lens_h = 0.022, 0.05
    lens = UsdGeom.Cylinder.Define(stage, f"{path}/lens")
    lens.CreateAxisAttr("Y")   # points toward -Y (the bench)
    lens.CreateRadiusAttr(lens_r)
    lens.CreateHeightAttr(lens_h)
    lens.CreateExtentAttr([(-lens_r, -lens_h / 2.0, -lens_r),
                           (lens_r, lens_h / 2.0, lens_r)])
    UsdGeom.Xformable(lens).AddTranslateOp().Set(
        Gf.Vec3d(fx, fy - 0.05, floor_z + head_z))
    UsdShade.MaterialBindingAPI(lens.GetPrim()).Bind(dark)

    # A real camera prim aimed at look_at (so it's usable as a viewport too).
    cam = UsdGeom.Camera.Define(stage, f"{path}/Camera")
    ex, ey, ez = fx, fy, floor_z + head_z
    lx, ly, lz = look_at
    yaw = math.degrees(math.atan2(lx - ex, -(ly - ey)))    # about Z
    dist_xy = math.sqrt((lx - ex) ** 2 + (ly - ey) ** 2)
    pitch = math.degrees(math.atan2(lz - ez, dist_xy))     # about X
    cxf = UsdGeom.Xformable(cam)
    cxf.AddTranslateOp().Set(Gf.Vec3d(ex, ey, ez))
    cxf.AddRotateZOp().Set(yaw)
    cxf.AddRotateXOp().Set(90.0 + pitch)
    print(f"[lab_scene] Tripod camera at {foot_xy} looking at {look_at}")
    return cam.GetPrim()


# ───────────────────────────── layout ───────────────────────────────
def add_lab_props(stage, bench):
    """Dress the bench like a chemistry station. Zones along the bench long (X)
    axis, all within the arms' reach band (y just in front of the rail):

      left  (-X): reagent zone — colour-coded reagent bottles on a shelf,
                  plus a test-tube rack with tubes
      centre    : beakers (the mixing area)
      right (+X): a balance/scale with a beaker sitting on its platform

    Off the front-left corner, on the floor, a camera on a tripod looks back at
    the mixing area.
    """
    if bench is None:
        return
    cx, cy = bench["center"]
    top_z = bench["top_z"]
    sx, sy = bench["size"]
    reach_y = cy + 0.10   # ~0.2 m in front of the rail

    # Left — reagent zone.
    add_reagent_shelf(stage, (cx - 0.45, reach_y + 0.02), top_z)
    slots, stand_z = add_test_tube_rack(stage, (cx - 0.28, reach_y), top_z, n=5)
    spawn_test_tubes(stage, slots, stand_z)

    # Centre — mixing beakers.
    spawn_beakers(stage, [
        (cx - 0.02, reach_y + 0.02, top_z),
        (cx + 0.08, reach_y - 0.04, top_z),
        (cx + 0.02, reach_y - 0.06, top_z),
    ])

    # Right — scale with a beaker on the platform.
    (px, py), plat_top = add_scale(stage, (cx + 0.35, reach_y), top_z)
    spawn_beakers(stage, [(px, py, plat_top)],
                  parent_path="/World/ScaleBeaker", radius=0.028, height=0.07)

    # Tripod camera on the floor, front-left, looking at the mixing area.
    add_tripod_camera(stage, (cx - sy * 0.0 - 0.55, cy - sy * 0.5 - 0.35),
                      floor_z=0.0, head_z=top_z + 0.25,
                      look_at=(cx, reach_y, top_z + 0.05))
