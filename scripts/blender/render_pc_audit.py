"""Render geometry and room-context previews of the current PC area."""

from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Vector


root = Path.cwd().resolve()
output_dir = root / "artifacts/pc-upgrade"
output_dir.mkdir(parents=True, exist_ok=True)

scene = bpy.context.scene
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = True


def add_camera(name, target, offset, ortho_scale):
    data = bpy.data.cameras.new(f"{name}_Camera")
    camera = bpy.data.objects.new(f"{name}_Camera", data)
    scene.collection.objects.link(camera)
    camera.location = target + offset
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    data.type = "ORTHO"
    data.ortho_scale = ortho_scale
    scene.camera = camera
    return camera, data


def render(name, target, offset, ortho_scale, isolated=None, engine="BLENDER_WORKBENCH"):
    original_hide = {obj: obj.hide_render for obj in bpy.data.objects}
    if isolated is not None:
        allowed = set(isolated)
        for obj in bpy.data.objects:
            obj.hide_render = obj.type != "MESH" or obj not in allowed

    scene.render.engine = engine
    if engine == "BLENDER_WORKBENCH":
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "TEXTURE"
        scene.display.shading.show_shadows = True
        scene.display.shading.show_cavity = True
        scene.display.shading.cavity_type = "WORLD"

    camera, camera_data = add_camera(name, target, offset, ortho_scale)
    scene.render.filepath = str(output_dir / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)

    for obj, hidden in original_hide.items():
        if obj.name in bpy.data.objects:
            obj.hide_render = hidden
    print("RENDERED", name, scene.render.filepath)


computer = bpy.data.objects.get("Computer_Baked")
case = bpy.data.objects.get("Plane.020_Baked")

render(
    "pc-case-isolated",
    Vector((-2.26, 3.57, 3.84)),
    Vector((3.2, -3.4, 1.7)),
    2.5,
    isolated=[case] if case else [],
)
render(
    "computer-object-isolated",
    Vector((-2.90, 1.50, 4.28)),
    Vector((3.2, -3.4, 1.7)),
    2.8,
    isolated=[computer] if computer else [],
)
render(
    "pc-room-context-before",
    Vector((-2.26, 3.57, 3.84)),
    Vector((3.2, -3.4, 1.7)),
    3.3,
    engine="BLENDER_EEVEE",
)
