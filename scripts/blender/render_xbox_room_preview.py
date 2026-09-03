"""Render close room previews around the newly placed Xbox controller."""

from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Vector


root = Path.cwd().resolve()
output_dir = root / "artifacts/xbox-controller-audit"
output_dir.mkdir(parents=True, exist_ok=True)

stand_root = bpy.data.objects.get(
    "stand_fore_controller_Xbox.obj.cleaner.materialmerger.gles"
)
stand_objects = set()
if stand_root:
    stack = [stand_root]
    while stack:
        current = stack.pop()
        stand_objects.add(current)
        stack.extend(current.children)

for obj in bpy.data.objects:
    obj.hide_render = obj in stand_objects or obj.type != "MESH"

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.render.resolution_x = 1000
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = True

target = Vector((-2.92, -0.84, 5.0))
views = {
    "xbox-room-perspective": Vector((4.2, -2.5, 1.8)),
    "xbox-room-front": Vector((4.5, 0.0, 0.55)),
}

for label, offset in views.items():
    camera_data = bpy.data.cameras.new(f"{label}_Camera")
    camera = bpy.data.objects.new(f"{label}_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = target + offset
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 2.7
    scene.camera = camera
    scene.render.filepath = str(output_dir / f"{label}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", label, scene.render.filepath)
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)
