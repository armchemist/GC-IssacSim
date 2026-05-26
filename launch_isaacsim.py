"""Launch Isaac Sim with WebRTC livestream, empty scene."""
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

print("[launch_isaacsim] WebRTC livestream running. Connect via Isaac Sim WebRTC Streaming Client.")

while simulation_app.is_running():
    simulation_app.update()

simulation_app.close()
