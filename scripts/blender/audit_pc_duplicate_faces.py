"""Report exact coincident triangles inside the final PC case mesh."""

from collections import Counter, defaultdict

import bpy


pc = bpy.data.objects.get("Plane.020_Baked")
if not pc or pc.type != "MESH":
    raise RuntimeError("Plane.020_Baked was not found")

mesh = pc.data
mesh.calc_loop_triangles()
triangles = defaultdict(list)

for triangle in mesh.loop_triangles:
    points = []
    for vertex_index in triangle.vertices:
        point = pc.matrix_world @ mesh.vertices[vertex_index].co
        points.append(tuple(round(float(value), 6) for value in point))
    triangles[tuple(sorted(points))].append(triangle.polygon_index)

duplicates = {
    key: polygon_indices
    for key, polygon_indices in triangles.items()
    if len(polygon_indices) > 1
}

print("PC_DUPLICATE_FACE_AUDIT")
print("TOTAL_TRIANGLES", len(mesh.loop_triangles))
print("DUPLICATE_TRIANGLE_KEYS", len(duplicates))
print("EXTRA_COINCIDENT_TRIANGLES", sum(len(items) - 1 for items in duplicates.values()))
material_pairs = Counter()
for polygon_indices in duplicates.values():
    material_pairs.update(
        [tuple(sorted(mesh.polygons[index].material_index for index in polygon_indices))]
    )
print("DUPLICATE_MATERIAL_PAIRS", dict(sorted(material_pairs.items())))
for polygon_indices in list(duplicates.values())[:20]:
    material_indices = [mesh.polygons[index].material_index for index in polygon_indices]
    print("DUPLICATE_POLYGONS", polygon_indices, "MATERIAL_INDICES", material_indices)
