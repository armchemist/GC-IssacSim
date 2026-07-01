"""
Keyboard teleoperation for TWO OMX_F arms on one shared rail cart in Isaac Sim 5.1
(WebRTC streaming), in a decorated lab scene with grabbable beakers.

Prerequisites:
  Run load_omx_f_dual_rail.py once to generate model/omx_f_dual_rail.usd.

Both arms share one cart, so W/S moves them together. All arm-joint and gripper
keys act on the ACTIVE arm; switch the active arm with 1 / 2 (or Tab).

Key bindings:
  1 / 2 / Tab — Select active arm  (1 = left, 2 = right, Tab = toggle)
  W / S       — Rail forward / back  (shared cart, X-axis, 0–630 mm)
  A / D       — Active joint1 base rotation  (±)
  Q / E       — Active joint2 shoulder       (±)
  Up / Down   — Active joint3 elbow          (±)
  Left / Right— Active joint4 forearm        (±)
  Z / X       — Active joint5 wrist roll     (±)
  Space       — Active gripper toggle (open / close)
  R           — Reset all joints to home position
"""

from isaacsim import SimulationApp

simulation_app = SimulationApp({
    "headless": True,
    "hide_ui": False,
    "renderer": "RaytracedLighting",
    "width": 1280,
    "height": 720,
})

from isaacsim.core.utils.extensions import enable_extension
enable_extension("omni.kit.livestream.webrtc")

import os
import numpy as np
import omni.usd
import carb
import carb.input
from pxr import UsdLux, UsdPhysics, Gf

import lab_scene

HERE = os.path.dirname(os.path.abspath(__file__))
USD_PATH = os.path.join(HERE, "model", "omx_f_dual_rail.usd")

if not os.path.exists(USD_PATH):
    raise FileNotFoundError(
        f"USD not found: {USD_PATH}\n"
        "Run load_omx_f_dual_rail.py first to generate it."
    )

# ── Load stage ───────────────────────────────────────────────
omni.usd.get_context().open_stage(USD_PATH)
simulation_app.update()  # let stage settle

stage = omni.usd.get_context().get_stage()

# ── Decorate scene (before world.reset so colliders register) ─
lab_scene.add_lab_environment(stage)
lab_scene.spawn_beakers(stage)

# Fallback light only if the environment did not provide one.
if not stage.GetPrimAtPath("/World/DistantLight").IsValid() and \
        not stage.GetPrimAtPath("/World/Environment").IsValid():
    light = UsdLux.DistantLight.Define(stage, "/World/DistantLight")
    light.CreateIntensityAttr(3000.0)
    light.AddRotateXYZOp().Set(Gf.Vec3f(-45.0, 0.0, 0.0))

# ── Find articulation root ────────────────────────────────────
def find_articulation_path(stage):
    for prim in stage.Traverse():
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            return str(prim.GetPath())
    return None

art_path = find_articulation_path(stage)
if art_path is None:
    raise RuntimeError("No ArticulationRootAPI found in stage. Check USD generation.")
print(f"[teleop] Articulation root: {art_path}")

# ── Set up physics world ──────────────────────────────────────
from isaacsim.core.api import World
from isaacsim.core.prims import SingleArticulation

world = World(stage_units_in_meters=1.0)
robot = world.scene.add(SingleArticulation(prim_path=art_path, name="robot"))
world.reset()

dof_names = list(robot.dof_names)
print(f"[teleop] DOFs ({len(dof_names)}): {dof_names}")

dof = {name: i for i, name in enumerate(dof_names)}

# ── Joint state ───────────────────────────────────────────────
positions = robot.get_joint_positions()
if positions is None:
    positions = np.zeros(len(dof_names))
else:
    positions = positions.copy()

RAIL_MAX = 0.630
RAIL_STEP = 0.003   # m per frame
ARM_STEP  = 0.020   # rad per frame
GRIP_OPEN = 0.8     # rad open position

# Active arm + per-arm gripper state.
active = "l_"                                  # "l_" or "r_"
gripper_open = {"l_": False, "r_": False}

ARM_NAMES = {"l_": "LEFT", "r_": "RIGHT"}


def set_active(prefix):
    global active
    if prefix in ("l_", "r_") and prefix != active:
        active = prefix
        print(f"[teleop] Active arm: {ARM_NAMES[active]}")


# ── Keyboard ──────────────────────────────────────────────────
held = set()
K = carb.input.KeyboardInput
KEY_1 = getattr(K, "KEY_1", None)
KEY_2 = getattr(K, "KEY_2", None)


def on_key(event, *args, **kwargs):
    global positions
    k = event.input
    press   = event.type == carb.input.KeyboardEventType.KEY_PRESS

    if press:
        held.add(k)
        # Active-arm selection
        if k == KEY_1:
            set_active("l_")
        elif k == KEY_2:
            set_active("r_")
        elif k == K.TAB:
            set_active("r_" if active == "l_" else "l_")
        # Gripper toggle (active arm)
        elif k == K.SPACE:
            gripper_open[active] = not gripper_open[active]
            g = dof.get(f"{active}gripper_joint_1")
            if g is not None:
                positions[g] = GRIP_OPEN if gripper_open[active] else 0.0
            print(f"[teleop] {ARM_NAMES[active]} gripper "
                  f"{'OPEN' if gripper_open[active] else 'CLOSE'}")
        # Reset all
        elif k == K.R:
            positions[:] = 0.0
            gripper_open["l_"] = gripper_open["r_"] = False
            print("[teleop] Reset to home")
    elif event.type == carb.input.KeyboardEventType.KEY_RELEASE:
        held.discard(k)
    return True


try:
    from omni.appwindow import get_default_app_window
    app_window = get_default_app_window()
    input_iface = carb.input.acquire_input_interface()
    keyboard = app_window.get_keyboard()
    kb_sub = input_iface.subscribe_to_keyboard_events(keyboard, on_key)
    print("[teleop] Keyboard subscribed via omni.appwindow")
except Exception as e:
    kb_sub = None
    print(f"[teleop] WARNING: keyboard subscription failed: {e}")
    print("[teleop] Continuing without keyboard.")

print(__doc__)

# ── Main loop ─────────────────────────────────────────────────
def bump(name, key_pos, key_neg, step=ARM_STEP):
    idx = dof.get(name)
    if idx is not None:
        if key_pos in held: positions[idx] += step
        if key_neg in held: positions[idx] -= step


while simulation_app.is_running():
    # Rail (shared cart — moves both arms)
    r = dof.get("rail_joint")
    if r is not None:
        if K.W in held: positions[r] = min(RAIL_MAX, positions[r] + RAIL_STEP)
        if K.S in held: positions[r] = max(0.0,      positions[r] - RAIL_STEP)

    # Active-arm joints
    bump(f"{active}joint1", K.D,    K.A)
    bump(f"{active}joint2", K.Q,    K.E)
    bump(f"{active}joint3", K.UP,   K.DOWN)
    bump(f"{active}joint4", K.LEFT, K.RIGHT)
    bump(f"{active}joint5", K.Z,    K.X)

    robot.set_joint_positions(positions)
    world.step(render=True)

# ── Cleanup ───────────────────────────────────────────────────
if kb_sub is not None:
    input_iface.unsubscribe_to_keyboard_events(keyboard, kb_sub)
simulation_app.close()
