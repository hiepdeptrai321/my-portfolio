"""Write a concise component/material inventory for the currently opened blend."""

from __future__ import annotations

import json
import re
from pathlib import Path

import bpy


blend = Path(bpy.data.filepath).resolve()
root = blend.parent.parent
slug = re.sub(r"[^a-z0-9]+", "-", blend.stem.lower()).strip("-")
output = root / "artifacts/final-room-audit" / f"{slug}.json"
keywords = (
    "facebook",
    "linkedin",
    "github",
    "youtube",
    "twitter",
    "tree",
    "fifth",
    "raycaster",
)


def object_record(obj):
    return {
        "name": obj.name,
        "type": obj.type,
        "location": [round(float(value), 6) for value in obj.location],
        "rotation": [round(float(value), 6) for value in obj.rotation_euler],
        "scale": [round(float(value), 6) for value in obj.scale],
        "parent": obj.parent.name if obj.parent else None,
        "collections": sorted(collection.name for collection in obj.users_collection),
        "hide_viewport": obj.hide_viewport,
        "hide_render": obj.hide_render,
        "materials": [
            slot.material.name if slot.material else None for slot in obj.material_slots
        ],
    }


matches = [
    object_record(obj)
    for obj in bpy.data.objects
    if any(keyword in obj.name.lower() for keyword in keywords)
]
missing_images = []
for image in bpy.data.images:
    if image.source != "FILE" or image.packed_file is not None:
        continue
    resolved = Path(bpy.path.abspath(image.filepath))
    if not resolved.is_file():
        missing_images.append({"name": image.name, "filepath": image.filepath})

report = {
    "blend": str(blend),
    "object_count": len(bpy.data.objects),
    "mesh_count": sum(1 for obj in bpy.data.objects if obj.type == "MESH"),
    "collections": sorted(collection.name for collection in bpy.data.collections),
    "keyword_matches": matches,
    "baked_materials": [
        name
        for name in (
            "FinalFirst_Baked",
            "RealFinalSecond_Baked",
            "FinalThird_Baked",
            "FinalFourth_Baked",
        )
        if bpy.data.materials.get(name) is not None
    ],
    "grounded_images": sorted(
        image.name for image in bpy.data.images if image.name.startswith("Grounded_")
    ),
    "missing_external_images": missing_images,
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

print("SCENE_COMPONENT_AUDIT", output)
print("OBJECTS", report["object_count"], "MESHES", report["mesh_count"])
print("KEYWORD_MATCHES", len(matches))
for record in matches:
    print(
        "MATCH",
        record["name"],
        "collections",
        record["collections"],
        "hidden",
        record["hide_viewport"],
        record["hide_render"],
    )
print("BAKED_MATERIALS", report["baked_materials"])
print("GROUNDED_IMAGES", report["grounded_images"])
print("MISSING_IMAGES", len(missing_images))
