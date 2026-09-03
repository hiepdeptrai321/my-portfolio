"""Audit social-card objects in the current final Blender scene."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


blend = Path(bpy.data.filepath).resolve()
root = blend.parent.parent
records = []
for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    world_location = obj.matrix_world.translation
    dimensions = obj.dimensions
    record = {
        "name": obj.name,
        "type": obj.type,
        "location": [round(float(value), 6) for value in obj.location],
        "world_location": [round(float(value), 6) for value in world_location],
        "dimensions": [round(float(value), 6) for value in dimensions],
        "rotation": [round(float(value), 6) for value in obj.rotation_euler],
        "scale": [round(float(value), 6) for value in obj.scale],
        "parent": obj.parent.name if obj.parent else None,
        "collections": sorted(collection.name for collection in obj.users_collection),
        "materials": [
            slot.material.name if slot.material else None for slot in obj.material_slots
        ],
        "hide_viewport": obj.hide_viewport,
        "hide_render": obj.hide_render,
    }
    records.append(record)

keywords = ("linkedin", "youtube", "github", "facebook", "twitter", "social")
keyword_matches = [
    record
    for record in records
    if any(keyword in record["name"].lower() for keyword in keywords)
]
non_mesh = [record for record in records if record["type"] != "MESH"]
facebook = bpy.data.objects.get("Facebook_Fifth_Raycaster_Pointer_Hover")
near_facebook = []
if facebook is not None:
    origin = facebook.matrix_world.translation
    for record, obj in zip(records, sorted(bpy.data.objects, key=lambda item: item.name)):
        if (obj.matrix_world.translation - origin).length <= 3.0:
            near_facebook.append(record)

report = {
    "blend": str(blend),
    "object_count": len(records),
    "type_counts": {
        object_type: sum(1 for record in records if record["type"] == object_type)
        for object_type in sorted({record["type"] for record in records})
    },
    "keyword_matches": keyword_matches,
    "non_mesh_objects": non_mesh,
    "near_facebook": near_facebook,
    "all_objects": records,
}
output = root / "artifacts/final-room-audit/social-cards.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("SOCIAL_CARD_AUDIT", output)
print("TYPE_COUNTS", json.dumps(report["type_counts"], sort_keys=True))
print("KEYWORD_MATCHES", len(keyword_matches))
for record in keyword_matches:
    print("MATCH", record["name"], record["type"], record["world_location"])
print("NEAR_FACEBOOK", len(near_facebook))
