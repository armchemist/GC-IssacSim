"""
Keyboard teleoperation for OMX_F on linear rail in Isaac Sim 5.1 (WebRTC streaming).

Prerequisites:
  Run load_omx_f_rail.py once to generate model/omx_f_rail.usd.

Key bindings:
  W / S       — Rail forward / back  (X-axis, 0–630 mm)
  A / D       — Joint1 base rotation  (±)
  Q / E       — Joint2 shoulder       (±)
  Up / Down   — Joint3 elbow         (±)
  Left / Right— Joint4 forearm       (±)
  Z / X       — Joint5 wrist roll    (±)
  Space       — Gripper toggle (open / close)
  R           — Reset all to home position
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

HERE = os.path.dirname(os.path.abspath(__file__))
USD_PATH = os.path.join(HERE, "model", "omx_f_rail.usd")

if not os.path.exists(USD_PATH):
    raise FileNotFoundError(
        f"USD not found: {USD_PATH}\n"
        "Run load_omx_f_rail.py first to generate it."
    )

# ── Load stage ───────────────────────────────────────────────
omni.usd.get_context().open_stage(USD_PATH)
simulation_app.update()  # let stage settle

stage = omni.usd.get_context().get_stage()

# Add light if absent
if not stage.GetPrimAtPath("/World/DistantLight").IsValid():
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
gripper_open = False

# ── Keyboard ──────────────────────────────────────────────────
held = set()

def on_key(event, *args, **kwargs):
    global gripper_open, positions
    k = event.input
    K = carb.input.KeyboardInput
    press   = event.type == carb.input.KeyboardEventType.KEY_PRESS
    release = event.type == carb.input.KeyboardEventType.KEY_RELEASE

    if press:
        held.add(k)
        if k == K.SPACE:
            gripper_open = not gripper_open
            g = dof.get("gripper_joint_1")
            if g is not None:
                positions[g] = GRIP_OPEN if gripper_open else 0.0
            print(f"[teleop] Gripper {'OPEN' if gripper_open else 'CLOSE'}")
        if k == K.R:
            positions[:] = 0.0
            gripper_open = False
            print("[teleop] Reset to home")
    elif release:
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
    print("[teleop] Continuing without keyboard — use R/Space programmatically.")

print(__doc__)

# ── Main loop ─────────────────────────────────────────────────
K = carb.input.KeyboardInput

while simulation_app.is_running():
    # Rail
    r = dof.get("rail_joint")
    if r is not None:
        if K.W in held: positions[r] = min(RAIL_MAX, positions[r] + RAIL_STEP)
        if K.S in held: positions[r] = max(0.0,      positions[r] - RAIL_STEP)

    # Arm joints
    def bump(name, key_pos, key_neg, step=ARM_STEP):
        idx = dof.get(name)
        if idx is not None:
            if key_pos in held: positions[idx] += step
            if key_neg in held: positions[idx] -= step

    bump("joint1",          K.D,     K.A)
    bump("joint2",          K.Q,     K.E)
    bump("joint3",          K.UP,    K.DOWN)
    bump("joint4",          K.LEFT,  K.RIGHT)
    bump("joint5",          K.Z,     K.X)

    robot.set_joint_positions(positions)
    world.step(render=True)

# ── Cleanup ───────────────────────────────────────────────────
if kb_sub is not None:
    input_iface.unsubscribe_to_keyboard_events(keyboard, kb_sub)
simulation_app.close()
