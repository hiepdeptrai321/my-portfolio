"""Verify a static Grounded Pastel Day/Night blend and its geometry/UV signature."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

import bpy


blend = Path(bpy.data.filepath).resolve()
root = blend.parent.parent
mode = "night" if "night" in blend.stem.lower() else "day"
mode_title = mode.title()
slug = re.sub(r"[^a-z0-9]+", "-", blend.stem.lower()).strip("-")
output = root / f"artifacts/grounded-pastel-no-rebake/{slug}-verification.json"
materials = [
    "FinalFirst_Baked",
    "RealFinalSecond_Baked",
    "FinalThird_Baked",
    "FinalFourth_Baked",
]
material_name_set = set(materials)


def feed_text(digest, value: str) -> None:
    encoded = value.encode("utf-8")
    digest.update(struct.pack("<I", len(encoded)))
    digest.update(encoded)


digest = hashlib.sha256()
counts = {
    "object_count": len(bpy.data.objects),
    "mesh_object_count": 0,
    "vertex_count": 0,
    "polygon_count": 0,
    "uv_loop_count": 0,
}
for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    feed_text(digest, obj.name)
    feed_text(digest, obj.type)
    feed_text(digest, obj.parent.name if obj.parent else "")
    digest.update(struct.pack("<3f", *[float(v) for v in obj.location]))
    digest.update(struct.pack("<3f", *[float(v) for v in obj.rotation_euler]))
    digest.update(struct.pack("<3f", *[float(v) for v in obj.scale]))
    if obj.type != "MESH":
        continue
    counts["mesh_object_count"] += 1
    mesh = obj.data
    feed_text(digest, mesh.name)
    counts["vertex_count"] += len(mesh.vertices)
    counts["polygon_count"] += len(mesh.polygons)
    for vertex in mesh.vertices:
        digest.update(struct.pack("<3f", *[float(v) for v in vertex.co]))
    for polygon in mesh.polygons:
        digest.update(struct.pack("<I", len(polygon.vertices)))
        for index in polygon.vertices:
            digest.update(struct.pack("<I", int(index)))
        digest.update(struct.pack("<I", int(polygon.material_index)))
    for slot in obj.material_slots:
        feed_text(digest, slot.material.name if slot.material else "")
    for layer in mesh.uv_layers:
        feed_text(digest, layer.name)
        counts["uv_loop_count"] += len(layer.data)
        for entry in layer.data:
            digest.update(struct.pack("<2f", *[float(v) for v in entry.uv]))

material_reports = {}
for material_name in materials:
    material = bpy.data.materials.get(material_name)
    image_node = (
        material.node_tree.nodes.get(f"Grounded Pastel {mode_title}")
        if material and material.node_tree
        else None
    )
    emission = (
        next(
            (
                node
                for node in material.node_tree.nodes
                if node.bl_idname == "ShaderNodeEmission"
            ),
            None,
        )
        if material and material.node_tree
        else None
    )
    linked_to_emission = bool(
        image_node
        and emission
        and any(
            link.from_node == image_node
            and link.to_node == emission
            and link.to_socket == emission.inputs["Color"]
            for link in material.node_tree.links
        )
    )
    material_reports[material_name] = {
        "exists": material is not None,
        "image_node": image_node is not None,
        "image": image_node.image.name if image_node and image_node.image else None,
        "dimensions": (
            list(image_node.image.size) if image_node and image_node.image else None
        ),
        "packed": bool(
            image_node and image_node.image and image_node.image.packed_file
        ),
        "linked_to_emission": linked_to_emission,
        "mode_property": material.get("grounded_pastel_mode") if material else None,
    }

visibility = {
    "baked_mesh_total": 0,
    "baked_mesh_viewport_enabled": 0,
    "baked_mesh_render_enabled": 0,
    "source_mesh_total": 0,
    "source_mesh_viewport_hidden": 0,
    "source_mesh_render_hidden": 0,
}
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    uses_baked_material = any(
        slot.material is not None and slot.material.name in material_name_set
        for slot in obj.material_slots
    )
    if uses_baked_material:
        visibility["baked_mesh_total"] += 1
        if not obj.hide_viewport:
            visibility["baked_mesh_viewport_enabled"] += 1
        if not obj.hide_render:
            visibility["baked_mesh_render_enabled"] += 1
    else:
        visibility["source_mesh_total"] += 1
        if obj.hide_viewport:
            visibility["source_mesh_viewport_hidden"] += 1
        if obj.hide_render:
            visibility["source_mesh_render_hidden"] += 1

baked_layer_collection_states = []
for view_layer in bpy.context.scene.view_layers:
    pending = [view_layer.layer_collection]
    while pending:
        layer_collection = pending.pop()
        if layer_collection.name == "SimpleBake_Bakes":
            baked_layer_collection_states.append(
                {
                    "view_layer": view_layer.name,
                    "exclude": layer_collection.exclude,
                    "hide_viewport": layer_collection.hide_viewport,
                }
            )
        pending.extend(layer_collection.children)

verification = {
    "blend": str(blend),
    "mode": mode,
    "structure_sha256": digest.hexdigest().upper(),
    "structure_counts": counts,
    "has_embedded_readme": bpy.data.texts.get("GROUNDED_PASTEL_README") is not None,
    "materials": material_reports,
    "visibility": visibility,
    "baked_layer_collections": baked_layer_collection_states,
    "packed_grounded_images": sorted(
        image.name
        for image in bpy.data.images
        if image.name.startswith("Grounded_") and image.packed_file is not None
    ),
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(verification, indent=2), encoding="utf-8")

print("STATIC_BLEND_VERIFICATION", output)
print("MODE", mode)
print("STRUCTURE_SHA256", verification["structure_sha256"])
print("COUNTS", json.dumps(counts, sort_keys=True))
print("PACKED_GROUNDED_IMAGES", len(verification["packed_grounded_images"]))
print("VISIBILITY", json.dumps(visibility, sort_keys=True))
print("BAKED_LAYER_COLLECTIONS", json.dumps(baked_layer_collection_states))
for name, report in material_reports.items():
    print(
        "VERIFY_MATERIAL",
        name,
        "image_node",
        report["image_node"],
        "packed",
        report["packed"],
        "dimensions",
        report["dimensions"],
        "linked",
        report["linked_to_emission"],
        "mode",
        report["mode_property"],
    )
