"""Lab scene decoration helpers for the OMX_F dual-rail simulation.

Shared by load_omx_f_dual_rail.py (viewer / USD generation) and
teleop_omx_dual_rail.py (physics). Two pieces:

  add_lab_environment(stage)  — reference an NVIDIA indoor environment USD
                                (Simple_Room) so the scene looks like a room
                                instead of an empty grid, then swap its rounded
                                built-in table for a plain rectangular 4-leg desk.
  spawn_beakers(stage, ...)   — procedural translucent cylinders with rigid-body
                                physics, so the arms can pick them up / knock
                                them over.

Both are best-effort: if the NVIDIA asset server is unreachable the environment
is skipped (with a warning) and the rest of the scene still loads.
"""

from pxr import Usd, UsdGeom, UsdPhysics, UsdShade, Sdf, Gf

# Relative path of the indoor environment on the NVIDIA asset server.
ENV_REL_PATH = "/Isaac/Environments/Simple_Room/simple_room.usd"


def add_lab_environment(stage, prim_path="/World/Environment"):
    """Reference an NVIDIA indoor environment USD under `prim_path`.

    Returns the env Usd.Prim on success, or None if the asset root could not be
    resolved (offline). The environment ships its own floor + lighting, so the
    caller should NOT also add a procedural ground plane.
    """
    try:
        from isaacsim.storage.native import get_assets_root_path
    except Exception:  # pragma: no cover - older layouts
        from omni.isaac.nucleus import get_assets_root_path  # type: ignore

    assets_root = get_assets_root_path()
    if not assets_root:
        print("[lab_scene] WARNING: assets root unresolved (offline?) — "
              "skipping NVIDIA environment.")
        return None

    env_usd = assets_root + ENV_REL_PATH
    env_prim = stage.DefinePrim(prim_path, "Xform")
    env_prim.GetReferences().AddReference(env_usd)
    print(f"[lab_scene] Environment referenced: {env_usd}")

    # The referenced environment may carry its own PhysicsScene; a second
    # PhysicsScene fights the robot's. Deactivate any env-side ones.
    _disable_nested_physics_scenes(stage, prim_path)

    # Simple_Room ships a rounded table; swap it for a plain rectangular desk.
    replace_env_table_with_desk(stage, prim_path)
    return env_prim


def _disable_nested_physics_scenes(stage, root_path):
    root = Sdf.Path(root_path)
    for prim in stage.Traverse():
        if prim.GetPath().HasPrefix(root) and prim.IsA(UsdPhysics.Scene):
            prim.SetActive(False)
            print(f"[lab_scene] Disabled nested PhysicsScene: {prim.GetPath()}")


def _world_aabb(prim):
    """World-space axis-aligned bounding box (min, max) Gf.Vec3d of `prim`."""
    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
    )
    rng = cache.ComputeWorldBound(prim).ComputeAlignedRange()
    return rng.GetMin(), rng.GetMax()


def replace_env_table_with_desk(stage, env_root="/World/Environment"):
    """Deactivate the environment's built-in table(s) and drop a plain
    rectangular 4-leg desk in the same footprint.

    The desk size/position is derived from the original table's world bounding
    box, so no hard-coded coordinates are needed. No-op if no table prim is
    found under `env_root`.
    """
    root = Sdf.Path(env_root)
    # Collect top-level table prims (skip descendants of an already-matched one).
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

    if not tables:
        print("[lab_scene] No env table prim found — skipping desk swap.")
        return []

    desks = []
    for i, tprim in enumerate(tables):
        try:
            mn, mx = _world_aabb(tprim)
        except Exception as e:
            print(f"[lab_scene] WARNING: bbox failed for {tprim.GetPath()}: {e}")
            continue
        tprim.SetActive(False)
        center = ((mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5)
        top_z = float(mx[2])
        footprint = (max(0.4, float(mx[0] - mn[0])),
                     max(0.4, float(mx[1] - mn[1])))
        desk = add_rect_table(stage, center, top_z, footprint,
                              path=f"/World/LabDesk_{i}")
        desks.append(desk)
        print(f"[lab_scene] Replaced env table {tprim.GetPath()} "
              f"-> rectangular desk (top_z={top_z:.3f})")
    return desks


def _get_or_create_wood_material(stage, mtl_path="/World/Looks/DeskWood"):
    if stage.GetPrimAtPath(mtl_path).IsValid():
        return UsdShade.Material.Get(stage, mtl_path)
    material = UsdShade.Material.Define(stage, mtl_path)
    shader = UsdShade.Shader.Define(stage, mtl_path + "/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.55, 0.38, 0.22))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.6)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface")
    return material


def add_rect_table(stage, center_xy, top_z, footprint,
                   path="/World/LabDesk", top_thick=0.04, leg=0.05):
    """Build a plain rectangular table: one top slab + four legs, as a static
    collider. `center_xy`=(x,y), `top_z`=top surface height, `footprint`=(sx,sy).
    """
    cx, cy = center_xy
    sx, sy = footprint
    material = _get_or_create_wood_material(stage)

    root = UsdGeom.Xform.Define(stage, path)

    def _box(sub, size, translate):
        p = f"{path}/{sub}"
        cube = UsdGeom.Cube.Define(stage, p)
        cube.CreateSizeAttr(1.0)  # unit cube, scaled below
        cube.CreateExtentAttr([(-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)])
        xf = UsdGeom.Xformable(cube)
        xf.AddTranslateOp().Set(Gf.Vec3d(*translate))
        xf.AddScaleOp().Set(Gf.Vec3f(size[0], size[1], size[2]))
        prim = cube.GetPrim()
        UsdPhysics.CollisionAPI.Apply(prim)           # static collider
        UsdShade.MaterialBindingAPI(prim).Bind(material)
        return prim

    # Top slab (centred so its upper face sits at top_z).
    _box("top", (sx, sy, top_thick), (cx, cy, top_z - top_thick * 0.5))

    # Four legs from floor (z=0) up to the underside of the slab.
    leg_h = max(0.05, top_z - top_thick)
    ix = sx * 0.5 - leg * 0.5   # inset so legs sit at the corners
    iy = sy * 0.5 - leg * 0.5
    for sxn in (-1, 1):
        for syn in (-1, 1):
            _box(f"leg_{sxn}_{syn}", (leg, leg, leg_h),
                 (cx + sxn * ix, cy + syn * iy, leg_h * 0.5))

    return root.GetPrim()


def _get_or_create_glass_material(stage, mtl_path="/World/Looks/BeakerGlass"):
    """A simple translucent material so beakers read as glassware."""
    if stage.GetPrimAtPath(mtl_path).IsValid():
        return UsdShade.Material.Get(stage, mtl_path)

    material = UsdShade.Material.Define(stage, mtl_path)
    shader = UsdShade.Shader.Define(stage, mtl_path + "/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.7, 0.85, 0.9))
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.25)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.1)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface")
    return material


# Default beaker layout: a small cluster in front of the cart, within the
# ~0.3 m reach of the arms. Coordinates are in metres, world frame.
DEFAULT_BEAKER_POSITIONS = [
    (0.28, 0.10, 0.05),
    (0.30, 0.00, 0.05),
    (0.28, -0.10, 0.05),
    (0.20, 0.06, 0.05),
    (0.20, -0.06, 0.05),
]


def spawn_beakers(stage, positions=None, parent_path="/World/Beakers",
                  radius=0.018, height=0.06, mass=0.05):
    """Create translucent rigid-body cylinders (beakers) at `positions`.

    Each beaker gets RigidBodyAPI + CollisionAPI + MassAPI so it falls under
    gravity and can be grasped. Call BEFORE world.reset() so the colliders are
    registered in the physics view.
    """
    if positions is None:
        positions = DEFAULT_BEAKER_POSITIONS

    stage.DefinePrim(parent_path, "Scope")
    material = _get_or_create_glass_material(stage)

    prims = []
    for i, (x, y, z) in enumerate(positions):
        path = f"{parent_path}/beaker_{i}"
        cyl = UsdGeom.Cylinder.Define(stage, path)
        cyl.CreateAxisAttr("Z")
        cyl.CreateRadiusAttr(radius)
        cyl.CreateHeightAttr(height)
        cyl.CreateExtentAttr([(-radius, -radius, -height / 2.0),
                              (radius, radius, height / 2.0)])

        xf = UsdGeom.Xformable(cyl)
        xf.AddTranslateOp().Set(Gf.Vec3d(x, y, z))

        prim = cyl.GetPrim()
        UsdPhysics.CollisionAPI.Apply(prim)
        UsdPhysics.RigidBodyAPI.Apply(prim)
        mass_api = UsdPhysics.MassAPI.Apply(prim)
        mass_api.CreateMassAttr(mass)

        UsdShade.MaterialBindingAPI(prim).Bind(material)
        prims.append(prim)

    print(f"[lab_scene] Spawned {len(prims)} beakers under {parent_path}")
    return prims
