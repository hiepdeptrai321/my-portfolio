"""Audit the existing PC-area objects in My Room - FINAL.blend."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


root = Path.cwd().resolve()
output = root / "artifacts/pc-upgrade/pc-area-audit.json"
output.parent.mkdir(parents=True, exist_ok=True)


def rounded(values):
    return [round(float(value), 6) for value in values]


def world_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = Vector((min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners)))
    maximum = Vector((max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners)))
    return [rounded(minimum), rounded(maximum)]


def material_report(material):
    result = {
        "name": material.name,
        "use_nodes": material.use_nodes,
        "surface_render_method": getattr(material, "surface_render_method", None),
    }
    if material.use_nodes and material.node_tree:
        result["nodes"] = [
            {
                "name": node.name,
                "type": node.bl_idname,
                "image": node.image.name if hasattr(node, "image") and node.image else None,
            }
            for node in material.node_tree.nodes
        ]
    return result


keywords = ("computer", "fan", "glass", "plane.020")
matches = []
for obj in bpy.data.objects:
    if obj.type != "MESH" or not any(keyword in obj.name.lower() for keyword in keywords):
        continue
    matches.append(
        {
            "name": obj.name,
            "location": rounded(obj.location),
            "rotation": rounded(obj.rotation_euler),
            "scale": rounded(obj.scale),
            "dimensions": rounded(obj.dimensions),
            "world_bounds": world_bounds(obj),
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
            "collections": [collection.name for collection in obj.users_collection],
            "parent": obj.parent.name if obj.parent else None,
        }
    )

pc_bounds = None
if matches:
    mins = [Vector(item["world_bounds"][0]) for item in matches]
    maxs = [Vector(item["world_bounds"][1]) for item in matches]
    minimum = Vector((min(v.x for v in mins), min(v.y for v in mins), min(v.z for v in mins)))
    maximum = Vector((max(v.x for v in maxs), max(v.y for v in maxs), max(v.z for v in maxs)))
    pc_bounds = [rounded(minimum), rounded(maximum)]

used_material_names = {
    name for item in matches for name in item["materials"] if name is not None
}
report = {
    "blend": bpy.data.filepath,
    "pc_bounds": pc_bounds,
    "objects": matches,
    "materials": [
        material_report(bpy.data.materials[name]) for name in sorted(used_material_names)
    ],
}

output.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("PC_AREA_AUDIT", output)
print("PC_BOUNDS", pc_bounds)
for item in matches:
    print("PC_OBJECT", item["name"], item["world_bounds"], item["materials"])
