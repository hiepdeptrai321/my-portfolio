"""Inspect disconnected geometry components inside Plane.020_Baked."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


root = Path.cwd().resolve()
output = root / "artifacts/pc-upgrade/pc-mesh-components.json"
output.parent.mkdir(parents=True, exist_ok=True)

obj = bpy.data.objects.get("Plane.020_Baked")
if not obj or obj.type != "MESH":
    raise RuntimeError("Plane.020_Baked mesh not found")

mesh = obj.data
parent = list(range(len(mesh.vertices)))
rank = [0] * len(parent)


def find(index):
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index


def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb:
        return
    if rank[ra] < rank[rb]:
        ra, rb = rb, ra
    parent[rb] = ra
    if rank[ra] == rank[rb]:
        rank[ra] += 1


for edge in mesh.edges:
    union(edge.vertices[0], edge.vertices[1])

component_vertices = defaultdict(set)
component_polygons = defaultdict(list)
for vertex in mesh.vertices:
    component_vertices[find(vertex.index)].add(vertex.index)
for polygon in mesh.polygons:
    root_index = find(polygon.vertices[0])
    component_polygons[root_index].append(polygon.index)

components = []
for root_index, vertices in component_vertices.items():
    coordinates = [obj.matrix_world @ mesh.vertices[index].co for index in vertices]
    minimum = Vector((min(p.x for p in coordinates), min(p.y for p in coordinates), min(p.z for p in coordinates)))
    maximum = Vector((max(p.x for p in coordinates), max(p.y for p in coordinates), max(p.z for p in coordinates)))
    dimensions = maximum - minimum
    centroid = (minimum + maximum) * 0.5
    polygons = component_polygons[root_index]
    components.append(
        {
            "id": root_index,
            "vertex_count": len(vertices),
            "polygon_count": len(polygons),
            "bounds": [
                [round(float(v), 6) for v in minimum],
                [round(float(v), 6) for v in maximum],
            ],
            "dimensions": [round(float(v), 6) for v in dimensions],
            "centroid": [round(float(v), 6) for v in centroid],
            "polygon_indices": polygons,
        }
    )

components.sort(key=lambda item: (-item["polygon_count"], item["id"]))
report = {
    "blend": bpy.data.filepath,
    "object": obj.name,
    "component_count": len(components),
    "components": components,
}
output.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("PC_COMPONENT_REPORT", output)
print("COMPONENT_COUNT", len(components))
for component in components:
    print(
        "COMPONENT",
        component["id"],
        "POLYGONS",
        component["polygon_count"],
        "BOUNDS",
        component["bounds"],
    )
