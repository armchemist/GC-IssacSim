"""Load omx_f.urdf into Isaac Sim 5.1 with WebRTC livestream."""
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
import omni.kit.commands
import omni.usd
from pxr import UsdLux, UsdGeom, Sdf, Gf
from isaacsim.asset.importer.urdf import _urdf

HERE = os.path.dirname(os.path.abspath(__file__))
URDF_PATH = os.path.join(HERE, "model", "omx_f.urdf")
USD_OUT = os.path.join(HERE, "model", "omx_f.usd")

# Configure URDF importer — do NOT split into separate physics/sensor layers
import_config = _urdf.ImportConfig()
import_config.merge_fixed_joints = False
import_config.convex_decomp = False
import_config.fix_base = True
import_config.make_default_prim = True
import_config.self_collision = False
import_config.create_physics_scene = True
import_config.import_inertia_tensor = True
import_config.default_drive_strength = 1047.0
import_config.default_position_drive_damping = 52.0
import_config.distance_scale = 1.0
import_config.density = 0.0
# Single-file output (avoids broken cross-layer references)
if hasattr(import_config, "parse_mimic"):
    import_config.parse_mimic = True
if hasattr(import_config, "collapse_fixed_joints"):
    import_config.collapse_fixed_joints = False

result, robot_model = omni.kit.commands.execute(
    "URDFParseFile", urdf_path=URDF_PATH, import_config=import_config
)
omni.kit.commands.execute(
    "URDFImportRobot",
    urdf_path=URDF_PATH,
    urdf_robot=robot_model,
    import_config=import_config,
    dest_path=USD_OUT,
)

# Open the imported USD as the main stage
omni.usd.get_context().open_stage(USD_OUT)
stage = omni.usd.get_context().get_stage()

# Add light
light = UsdLux.DistantLight.Define(stage, "/World/DistantLight")
light.CreateIntensityAttr(3000.0)
light.AddRotateXYZOp().Set(Gf.Vec3f(-45.0, 0.0, 0.0))

# Add a simple ground plane
ground = UsdGeom.Mesh.Define(stage, "/World/GroundPlane")
ground.CreatePointsAttr([(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)])
ground.CreateFaceVertexCountsAttr([4])
ground.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
ground.CreateExtentAttr([(-5, -5, 0), (5, 5, 0)])

print(f"[load_omx_f] Stage opened: {USD_OUT}")
print("[load_omx_f] WebRTC livestream running. Connect via Isaac Sim WebRTC Streaming Client.")

# Main loop — just keep the app/streaming alive
while simulation_app.is_running():
    simulation_app.update()

simulation_app.close()
