"""Render isolated previews of newly imported controller-related meshes."""

from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Vector


root = Path.cwd().resolve()
output_dir = root / "artifacts/xbox-controller-audit"
output_dir.mkdir(parents=True, exist_ok=True)


def mesh_descendants(root_object):
    result = []
    stack = [root_object]
    while stack:
        current = stack.pop()
        if current.type == "MESH":
            result.append(current)
        stack.extend(current.children)
    return result


def render_group(label, objects):
    for obj in bpy.data.objects:
        obj.hide_render = obj not in objects

    corners = [
        obj.matrix_world @ Vector(corner)
        for obj in objects
        for corner in obj.bound_box
    ]
    minimum = Vector(tuple(min(corner[axis] for corner in corners) for axis in range(3)))
    maximum = Vector(tuple(max(corner[axis] for corner in corners) for axis in range(3)))
    center = (minimum + maximum) / 2
    size = maximum - minimum

    camera_data = bpy.data.cameras.new(f"{label}_Camera")
    camera = bpy.data.objects.new(f"{label}_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    direction = Vector((1.7, -2.4, 1.35)).normalized()
    camera.location = center + direction * max(size) * 3
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(size.x, size.z, size.y) * 1.35
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    scene.render.filepath = str(output_dir / f"{label}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", label, scene.render.filepath, [obj.name for obj in objects])

    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)


small_candidate = bpy.data.objects.get("Xbox_Controller_Raycaster_Hover") or bpy.data.objects.get("Object_5")
stand_root = bpy.data.objects.get(
    "stand_fore_controller_Xbox.obj.cleaner.materialmerger.gles"
)

if small_candidate is None or small_candidate.type != "MESH":
    raise RuntimeError("Xbox controller candidate was not found")

render_group("object-5-candidate", [small_candidate])
if stand_root is not None:
    render_group("xbox-stand-candidate", mesh_descendants(stand_root))
else:
    print("SKIPPED xbox-stand-candidate: stand was already removed")
