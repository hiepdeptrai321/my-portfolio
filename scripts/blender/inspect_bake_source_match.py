"""Report possible source-object matches for a baked atlas member."""

from pathlib import Path

import bpy
from mathutils import Vector


BAKED_OBJECT = "Plane.003_Baked"


def world_bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return (minimum + maximum) * 0.5, maximum - minimum


source_blend = Path(bpy.data.filepath).resolve()
export_blend = source_blend.parent / "For Export.blend"

with bpy.data.libraries.load(str(export_blend), link=False) as (data_from, data_to):
    if BAKED_OBJECT not in data_from.objects:
        raise RuntimeError(f"Missing {BAKED_OBJECT}")
    data_to.objects = [BAKED_OBJECT]

baked = data_to.objects[0]
bpy.context.scene.collection.objects.link(baked)
center, dimensions = world_bounds(baked)
print(
    "BAKED_OBJECT",
    baked.name,
    "vertices",
    len(baked.data.vertices),
    "polygons",
    len(baked.data.polygons),
    "center",
    tuple(round(value, 5) for value in center),
    "dimensions",
    tuple(round(value, 5) for value in dimensions),
)

candidates = []
for obj in bpy.context.scene.objects:
    if obj == baked or obj.type != "MESH":
        continue
    obj_center, obj_dimensions = world_bounds(obj)
    topology_penalty = abs(len(obj.data.vertices) - len(baked.data.vertices)) + abs(
        len(obj.data.polygons) - len(baked.data.polygons)
    )
    spatial_penalty = (obj_center - center).length + (obj_dimensions - dimensions).length
    candidates.append((topology_penalty, spatial_penalty, obj))

for topology_penalty, spatial_penalty, obj in sorted(candidates, key=lambda item: (item[0], item[1]))[:12]:
    obj_center, obj_dimensions = world_bounds(obj)
    print(
        "CANDIDATE",
        obj.name,
        "topology_penalty",
        topology_penalty,
        "spatial_penalty",
        round(spatial_penalty, 6),
        "vertices",
        len(obj.data.vertices),
        "polygons",
        len(obj.data.polygons),
        "center",
        tuple(round(value, 5) for value in obj_center),
        "dimensions",
        tuple(round(value, 5) for value in obj_dimensions),
    )
