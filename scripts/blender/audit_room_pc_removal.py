"""Audit the runtime AABB used to remove the legacy PC from room-main.glb."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path.cwd().resolve()
MODEL = ROOT / "public/models/room-main.glb"
BOUNDS_MIN = Vector((-3.27, 3.145, 3.07))
BOUNDS_MAX = Vector((-1.25, 4.0, 4.6))


def inside(point):
    return all(
        BOUNDS_MIN[axis] <= point[axis] <= BOUNDS_MAX[axis]
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
parent = list(range(len(mesh.vertices)))


def find(index):
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index


def union(left, right):
    left_root = find(left)
    right_root = find(right)
    if left_root != right_root:
        parent[right_root] = left_root


for edge in mesh.edges:
    union(edge.vertices[0], edge.vertices[1])

components = {}
for triangle in mesh.loop_triangles:
    centroid_local = sum(
        (mesh.vertices[index].co for index in triangle.vertices),
        Vector(),
    ) / 3.0
    centroid_world = room_mesh.matrix_world @ centroid_local
    triangle_removed = inside(centroid_world)
    removed += int(triangle_removed)
    component = components.setdefault(
        find(triangle.vertices[0]),
        {"triangles": 0, "removed": 0, "min": centroid_world.copy(), "max": centroid_world.copy()},
    )
    component["triangles"] += 1
    component["removed"] += int(triangle_removed)
    for axis in range(3):
        component["min"][axis] = min(component["min"][axis], centroid_world[axis])
        component["max"][axis] = max(component["max"][axis], centroid_world[axis])

total = len(mesh.loop_triangles)
kept = total - removed

print("ROOM_PC_REMOVAL_AUDIT")
print("MODEL", MODEL)
print("TOTAL_TRIANGLES", total)
print("REMOVED_TRIANGLES", removed)
print("KEPT_TRIANGLES", kept)
print("REMOVED_PERCENT", round(removed / total * 100.0, 4))
for component_id, component in sorted(
    components.items(), key=lambda item: item[1]["removed"], reverse=True
):
    if not component["removed"]:
        continue
    print(
        "REMOVED_COMPONENT",
        component_id,
        "removed",
        component["removed"],
        "of",
        component["triangles"],
        "centroid_bounds",
        [round(value, 4) for value in component["min"]],
        [round(value, 4) for value in component["max"]],
    )

if removed < 4000 or removed > 6000:
    raise RuntimeError(
        f"Expected the isolated PC to contain 4000-6000 triangles, got {removed}"
    )
