"""Audit collection and viewport visibility in an export blend."""

from __future__ import annotations

import json
import re
from pathlib import Path

import bpy


blend = Path(bpy.data.filepath).resolve()
root = blend.parent.parent
slug = re.sub(r"[^a-z0-9]+", "-", blend.stem.lower()).strip("-")
output = root / f"artifacts/grounded-pastel-no-rebake/{slug}-visibility.json"
baked_materials = {
    "FinalFirst_Baked",
    "RealFinalSecond_Baked",
    "FinalThird_Baked",
    "FinalFourth_Baked",
}


def layer_state(layer_collection):
    return {
        "name": layer_collection.name,
        "exclude": layer_collection.exclude,
        "hide_viewport": layer_collection.hide_viewport,
        "children": [layer_state(child) for child in layer_collection.children],
    }


collections = []
for collection in bpy.data.collections:
    direct_meshes = [obj for obj in collection.objects if obj.type == "MESH"]
    baked_users = [
        obj.name
        for obj in direct_meshes
        if any(
            slot.material and slot.material.name in baked_materials
            for slot in obj.material_slots
        )
    ]
    collections.append(
        {
            "name": collection.name,
            "hide_viewport": collection.hide_viewport,
            "hide_render": collection.hide_render,
            "direct_object_count": len(collection.objects),
            "direct_mesh_count": len(direct_meshes),
            "baked_material_mesh_count": len(baked_users),
            "children": [child.name for child in collection.children],
        }
    )

mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]
report = {
    "blend": str(blend),
    "collections": sorted(collections, key=lambda item: item["name"]),
    "layer_collections": [
        {
            "view_layer": view_layer.name,
            "tree": layer_state(view_layer.layer_collection),
        }
        for view_layer in bpy.context.scene.view_layers
    ],
    "mesh_counts": {
        "total": len(mesh_objects),
        "viewport_visible": sum(not obj.hide_get() for obj in mesh_objects),
        "render_visible": sum(not obj.hide_render for obj in mesh_objects),
        "using_baked_materials": sum(
            any(
                slot.material and slot.material.name in baked_materials
                for slot in obj.material_slots
            )
            for obj in mesh_objects
        ),
        "not_using_baked_materials": sum(
            not any(
                slot.material and slot.material.name in baked_materials
                for slot in obj.material_slots
            )
            for obj in mesh_objects
        ),
    },
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("EXPORT_VISIBILITY_AUDIT", output)
print("MESH_COUNTS", json.dumps(report["mesh_counts"], sort_keys=True))
for collection in report["collections"]:
    if collection["direct_mesh_count"] or collection["children"]:
        print(
            "COLLECTION",
            collection["name"],
            "meshes",
            collection["direct_mesh_count"],
            "baked",
            collection["baked_material_mesh_count"],
            "hide_viewport",
            collection["hide_viewport"],
            "hide_render",
            collection["hide_render"],
            "children",
            collection["children"],
        )
