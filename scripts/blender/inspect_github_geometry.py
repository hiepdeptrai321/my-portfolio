"""Inspect loose geometry components of the final GitHub card without mutating it."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, deque
from pathlib import Path

import bpy


arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument("--model")
args = parser.parse_args(arguments)

root = Path.cwd().resolve()
if args.model:
    model_path = (root / args.model).resolve()
    if not model_path.is_file():
        raise FileNotFoundError(model_path)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(model_path))
    source_path = model_path
else:
    blend_path = Path(bpy.data.filepath).resolve()
    source_path = blend_path
    root = blend_path.parent.parent
github = next(
    (obj for obj in bpy.data.objects if obj.type == "MESH" and "GitHub" in obj.name),
    None,
)

if github is None:
    raise RuntimeError("GitHub mesh was not found")

mesh = github.data
adjacency = [set() for _ in mesh.vertices]
for edge in mesh.edges:
    a, b = edge.vertices
    adjacency[a].add(b)
    adjacency[b].add(a)

vertex_polygons = [[] for _ in mesh.vertices]
for polygon in mesh.polygons:
    for vertex_index in polygon.vertices:
        vertex_polygons[vertex_index].append(polygon.index)

unvisited = set(range(len(mesh.vertices)))
components = []
while unvisited:
    seed = next(iter(unvisited))
    queue = deque([seed])
    unvisited.remove(seed)
    vertex_indices = []

    while queue:
        vertex_index = queue.popleft()
        vertex_indices.append(vertex_index)
        for neighbor in adjacency[vertex_index]:
            if neighbor in unvisited:
                unvisited.remove(neighbor)
                queue.append(neighbor)

    polygon_indices = sorted(
        {polygon_index for index in vertex_indices for polygon_index in vertex_polygons[index]}
    )
    local_coordinates = [mesh.vertices[index].co for index in vertex_indices]
    world_coordinates = [github.matrix_world @ coordinate for coordinate in local_coordinates]
    material_counts = Counter(mesh.polygons[index].material_index for index in polygon_indices)

    def bounds(coordinates):
        return {
            "min": [round(min(coordinate[axis] for coordinate in coordinates), 6) for axis in range(3)],
            "max": [round(max(coordinate[axis] for coordinate in coordinates), 6) for axis in range(3)],
        }

    components.append(
        {
            "vertex_count": len(vertex_indices),
            "polygon_count": len(polygon_indices),
            "local_bounds": bounds(local_coordinates),
            "world_bounds": bounds(world_coordinates),
            "material_counts": dict(sorted(material_counts.items())),
        }
    )

components.sort(key=lambda component: component["polygon_count"], reverse=True)

# Mirror the runtime's virtual weld: Draco can split adjacent faces at UV seams,
# while equal rounded positions still belong to the same logical loose part.
parents = list(range(len(mesh.vertices)))
ranks = [0] * len(mesh.vertices)


def find(index):
    root = index
    while parents[root] != root:
        root = parents[root]
    while parents[index] != index:
        next_index = parents[index]
        parents[index] = root
        index = next_index
    return root


def union(first, second):
    first_root = find(first)
    second_root = find(second)
    if first_root == second_root:
        return
    if ranks[first_root] < ranks[second_root]:
        first_root, second_root = second_root, first_root
    parents[second_root] = first_root
    if ranks[first_root] == ranks[second_root]:
        ranks[first_root] += 1


coordinate_representatives = {}
for vertex in mesh.vertices:
    key = tuple(round(float(value) * 100000) for value in vertex.co)
    representative = coordinate_representatives.get(key)
    if representative is None:
        coordinate_representatives[key] = vertex.index
    else:
        union(vertex.index, representative)

for edge in mesh.edges:
    union(*edge.vertices)

logical_components = {}
for vertex in mesh.vertices:
    logical_components.setdefault(find(vertex.index), []).append(vertex.index)

logical_records = []
for vertex_indices in logical_components.values():
    coordinates = [mesh.vertices[index].co for index in vertex_indices]
    component_bounds = bounds(coordinates)
    logical_records.append(
        {
            "vertex_count": len(vertex_indices),
            "local_bounds": component_bounds,
        }
    )

overall_minimum = [min(vertex.co[axis] for vertex in mesh.vertices) for axis in range(3)]
overall_maximum = [max(vertex.co[axis] for vertex in mesh.vertices) for axis in range(3)]
overall_size = [
    overall_maximum[axis] - overall_minimum[axis] for axis in range(3)
]
depth_axis = overall_size.index(min(overall_size))
geometry_depth = overall_size[depth_axis]
card_front = max(
    logical_records,
    key=lambda component: (
        sorted(
            [
                component["local_bounds"]["max"][axis]
                - component["local_bounds"]["min"][axis]
                for axis in range(3)
            ],
            reverse=True,
        )[0]
        * sorted(
            [
                component["local_bounds"]["max"][axis]
                - component["local_bounds"]["min"][axis]
                for axis in range(3)
            ],
            reverse=True,
        )[1]
    ),
)
card_front_depth = card_front["local_bounds"]["max"][depth_axis]
masked_logical_components = []
for component in logical_records:
    minimum_depth = component["local_bounds"]["min"][depth_axis]
    maximum_depth = component["local_bounds"]["max"][depth_axis]
    component_depth = maximum_depth - minimum_depth
    extends_in_front = maximum_depth > card_front_depth + geometry_depth * 0.1
    is_detached_back_surface = (
        maximum_depth < card_front_depth - geometry_depth * 0.1
        and minimum_depth > overall_minimum[depth_axis] + geometry_depth * 0.2
        and component_depth < geometry_depth * 0.05
    )
    if extends_in_front or is_detached_back_surface:
        masked_logical_components.append(component)

report = {
    "source": str(source_path),
    "object": github.name,
    "location": [round(float(value), 6) for value in github.location],
    "dimensions": [round(float(value), 6) for value in github.dimensions],
    "materials": [slot.material.name if slot.material else None for slot in github.material_slots],
    "vertex_count": len(mesh.vertices),
    "polygon_count": len(mesh.polygons),
    "component_count": len(components),
    "components": components,
    "runtime_mask_audit": {
        "depth_axis": depth_axis,
        "logical_component_count_after_virtual_weld": len(logical_records),
        "masked_logical_component_count": len(masked_logical_components),
        "masked_vertex_count": sum(
            component["vertex_count"] for component in masked_logical_components
        ),
    },
}

output = root / "artifacts/final-room-audit/github-geometry.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("GITHUB_GEOMETRY", output)
print("OBJECT", github.name)
print("MATERIALS", report["materials"])
print("TOTAL", report["vertex_count"], report["polygon_count"], report["component_count"])
print("RUNTIME_MASK", json.dumps(report["runtime_mask_audit"], sort_keys=True))
for index, component in enumerate(components):
    print("COMPONENT", index, json.dumps(component, sort_keys=True))
