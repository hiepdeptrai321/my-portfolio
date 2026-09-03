"""Compare the current final blend with its Blender backup to locate a new controller import."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector


root = Path.cwd().resolve()
current_blend = (root / "blender files/My Room - FINAL.blend").resolve()
backup_blend = (root / "blender files/My Room - FINAL.blend1").resolve()


def object_record(obj):
    world_corners = (
        [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        if obj.type == "MESH"
        else []
    )
    return {
        "name": obj.name,
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "children": sorted(child.name for child in obj.children),
        "location": [round(float(value), 6) for value in obj.location],
        "world_location": [
            round(float(value), 6) for value in obj.matrix_world.translation
        ],
        "rotation": [round(float(value), 6) for value in obj.rotation_euler],
        "scale": [round(float(value), 6) for value in obj.scale],
        "dimensions": [round(float(value), 6) for value in obj.dimensions],
        "world_bounds": {
            "min": [
                round(min(corner[axis] for corner in world_corners), 6)
                for axis in range(3)
            ],
            "max": [
                round(max(corner[axis] for corner in world_corners), 6)
                for axis in range(3)
            ],
        }
        if world_corners
        else None,
        "materials": [
            slot.material.name if slot.material else None for slot in obj.material_slots
        ],
        "collections": sorted(collection.name for collection in obj.users_collection),
        "hide_viewport": obj.hide_viewport,
        "hide_render": obj.hide_render,
    }


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    return {obj.name: object_record(obj) for obj in bpy.data.objects}


current = snapshot(current_blend)
backup = snapshot(backup_blend) if backup_blend.is_file() else {}
added_names = sorted(set(current) - set(backup))
removed_names = sorted(set(backup) - set(current))
keywords = ("xbox", "controller", "gamepad", "joystick", "console")
keyword_names = sorted(
    name for name in current if any(keyword in name.lower() for keyword in keywords)
)

# Generic imported objects are often nested below a newly added root Empty.
candidate_names = set(added_names) | set(keyword_names)
for name in list(candidate_names):
    obj_record_data = current.get(name)
    if not obj_record_data:
        continue
    parent_name = obj_record_data["parent"]
    while parent_name:
        candidate_names.add(parent_name)
        parent_name = current[parent_name]["parent"] if parent_name in current else None
    candidate_names.update(obj_record_data["children"])

report = {
    "current_blend": str(current_blend),
    "backup_blend": str(backup_blend) if backup_blend.is_file() else None,
    "current_object_count": len(current),
    "backup_object_count": len(backup),
    "current_type_counts": dict(sorted(Counter(item["type"] for item in current.values()).items())),
    "backup_type_counts": dict(sorted(Counter(item["type"] for item in backup.values()).items())),
    "added_names": added_names,
    "removed_names": removed_names,
    "keyword_names": keyword_names,
    "candidates": [current[name] for name in sorted(candidate_names) if name in current],
}

output = root / "artifacts/final-room-audit/xbox-controller-audit.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("XBOX_AUDIT", output)
print("COUNTS", report["backup_object_count"], "->", report["current_object_count"])
print("TYPE_COUNTS", json.dumps(report["current_type_counts"], sort_keys=True))
print("ADDED", len(added_names), json.dumps(added_names))
print("REMOVED", len(removed_names), json.dumps(removed_names))
print("KEYWORDS", json.dumps(keyword_names))
for record in report["candidates"]:
    print(
        "CANDIDATE",
        record["name"],
        record["type"],
        "parent=",
        record["parent"],
        "world=",
        record["world_location"],
        "dimensions=",
        record["dimensions"],
        "materials=",
        record["materials"],
    )
