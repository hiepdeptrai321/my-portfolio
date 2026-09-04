"""Audit the corrected Three.js AABB used to remove the legacy PC."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path.cwd().resolve()
MODEL = ROOT / "public/models/room-main.glb"
BOUNDS_MIN_WEB = Vector((-3.27, 3.07, -4.0))
BOUNDS_MAX_WEB = Vector((-1.25, 4.6, -3.145))


def inside_web_bounds(point):
    return all(
        BOUNDS_MIN_WEB[axis] <= point[axis] <= BOUNDS_MAX_WEB[axis]
        for axis in range(3)
    )


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(MODEL))

room_mesh = bpy.data.objects.get("Fourth")
if not room_mesh or room_mesh.type != "MESH":
    raise RuntimeError("Fourth mesh was not found in room-main.glb")

mesh = room_mesh.data
mesh.calc_loop_triangles()
removed = 0

for triangle in mesh.loop_triangles:
    centroid_local = sum(
        (mesh.vertices[index].co for index in triangle.vertices),
        Vector(),
    ) / 3.0
    centroid_blender = room_mesh.matrix_world @ centroid_local
    centroid_web = Vector(
        (centroid_blender.x, centroid_blender.z, -centroid_blender.y)
    )
    removed += int(inside_web_bounds(centroid_web))

total = len(mesh.loop_triangles)
kept = total - removed

print("ROOM_PC_REMOVAL_AUDIT")
print("WEB_BOUNDS_MIN", list(BOUNDS_MIN_WEB))
print("WEB_BOUNDS_MAX", list(BOUNDS_MAX_WEB))
print("TOTAL_TRIANGLES", total)
print("REMOVED_TRIANGLES", removed)
print("KEPT_TRIANGLES", kept)
print("REMOVED_PERCENT", round(removed / total * 100.0, 4))

if removed != 5236:
    raise RuntimeError(f"Expected 5236 isolated PC-area triangles, got {removed}")
