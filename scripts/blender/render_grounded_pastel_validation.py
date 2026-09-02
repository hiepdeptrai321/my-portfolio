"""Render a small validation image from a Grounded Pastel blend's saved camera."""

from pathlib import Path

import bpy


blend = Path(bpy.data.filepath).resolve()
root = blend.parent.parent
output = (
    root
    / "artifacts/grounded-pastel-no-rebake"
    / f"{blend.stem.lower().replace(' ', '-')}-validation.png"
)
scene = bpy.context.scene
if scene.camera is None:
    raise RuntimeError("The scene has no active camera for validation rendering")

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 640
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(output)
output.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.render.render(write_still=True)

print("VALIDATION_RENDER", output)
print("CAMERA", scene.camera.name)
