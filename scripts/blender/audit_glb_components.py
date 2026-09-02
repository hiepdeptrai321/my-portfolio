"""Import a GLB into a clean scene and write its object/material inventory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True)
args = parser.parse_args(arguments)

root = Path.cwd().resolve()
model = (root / args.model).resolve()
if not model.is_file():
    raise FileNotFoundError(model)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(model))

records = []
for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    bounds = []
    if obj.type == "MESH":
        bounds = [
            [round(float(value), 6) for value in (obj.matrix_world @ Vector(corner))]
            for corner in obj.bound_box
        ]
    records.append(
        {
            "name": obj.name,
            "type": obj.type,
            "location": [round(float(value), 6) for value in obj.location],
            "rotation": [round(float(value), 6) for value in obj.rotation_euler],
            "scale": [round(float(value), 6) for value in obj.scale],
            "parent": obj.parent.name if obj.parent else None,
            "materials": [
                slot.material.name if slot.material else None
                for slot in obj.material_slots
            ],
            "world_bounds": bounds,
        }
    )

report = {
    "model": str(model),
    "objects": records,
    "materials": sorted(material.name for material in bpy.data.materials),
    "images": sorted(image.name for image in bpy.data.images),
}
output = root / "artifacts/final-room-audit" / f"{model.stem}-glb.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("GLB_COMPONENT_AUDIT", output)
print("OBJECTS", len(records), "MESHES", sum(1 for item in records if item["type"] == "MESH"))
for record in records:
    print(
        "OBJECT",
        record["name"],
        record["type"],
        "location",
        record["location"],
        "materials",
        record["materials"],
    )
print("MATERIALS", report["materials"])
print("IMAGES", report["images"])
