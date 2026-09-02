"""Strictly verify the single clean My Room - FINAL.blend."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy


blend = Path(bpy.data.filepath).resolve()
root = blend.parent.parent
output = root / "artifacts/final-room-audit/final-room-verification.json"
baked_material_names = {
    "FinalFirst_Baked",
    "RealFinalSecond_Baked",
    "FinalThird_Baked",
    "FinalFourth_Baked",
}
special_names = {
    "Facebook_Fifth_Raycaster_Pointer_Hover",
    "Tree_3",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


errors = []
meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
baked = [
    obj
    for obj in meshes
    if any(
        slot.material is not None and slot.material.name in baked_material_names
        for slot in obj.material_slots
    )
]
special = [obj for obj in meshes if obj.name in special_names]
other = [obj for obj in meshes if obj not in baked and obj not in special]

if len(meshes) != 167:
    errors.append(f"Expected 167 meshes, found {len(meshes)}")
if len(baked) != 165:
    errors.append(f"Expected 165 baked room meshes, found {len(baked)}")
if {obj.name for obj in special} != special_names:
    errors.append("Facebook/Tree special-object set is incomplete")
if other:
    errors.append(f"Unexpected non-final meshes: {[obj.name for obj in other]}")
if any("twitter" in obj.name.lower() for obj in bpy.data.objects):
    errors.append("An obsolete Twitter object still exists")
if any(obj.hide_viewport or obj.hide_render for obj in meshes):
    errors.append("At least one final mesh is hidden")

material_reports = {}
for material_name in sorted(baked_material_names):
    material = bpy.data.materials.get(material_name)
    image_node = (
        material.node_tree.nodes.get("Grounded Pastel Day FINAL")
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
    linked = bool(
        image_node
        and emission
        and any(
            link.from_node == image_node
            and link.to_node == emission
            and link.to_socket == emission.inputs["Color"]
            for link in material.node_tree.links
        )
    )
    report = {
        "exists": material is not None,
        "image": image_node.image.name if image_node and image_node.image else None,
        "dimensions": list(image_node.image.size) if image_node and image_node.image else None,
        "packed": bool(image_node and image_node.image and image_node.image.packed_file),
        "linked_to_emission": linked,
    }
    material_reports[material_name] = report
    if not all((report["exists"], report["packed"], report["linked_to_emission"])):
        errors.append(f"Invalid final atlas material: {material_name}")
    if report["dimensions"] != [4096, 4096]:
        errors.append(f"Unexpected atlas size for {material_name}: {report['dimensions']}")

missing_images = []
for image in bpy.data.images:
    if image.source != "FILE" or image.packed_file is not None:
        continue
    if not Path(bpy.path.abspath(image.filepath)).is_file():
        missing_images.append(image.name)
if missing_images:
    errors.append(f"Missing external images: {missing_images}")

report = {
    "blend": str(blend),
    "sha256": sha256(blend),
    "size_bytes": blend.stat().st_size,
    "object_count": len(bpy.data.objects),
    "mesh_count": len(meshes),
    "baked_room_mesh_count": len(baked),
    "special_objects": sorted(obj.name for obj in special),
    "twitter_object_count": sum(
        1 for obj in bpy.data.objects if "twitter" in obj.name.lower()
    ),
    "missing_external_images": missing_images,
    "materials": material_reports,
    "errors": errors,
    "passed": not errors,
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("FINAL_ROOM_VERIFICATION", output)
print("PASSED", report["passed"])
print("SHA256", report["sha256"])
print("OBJECTS", report["object_count"], "MESHES", report["mesh_count"])
print("BAKED", report["baked_room_mesh_count"])
print("SPECIAL", report["special_objects"])
print("TWITTER", report["twitter_object_count"])
print("MISSING_IMAGES", len(missing_images))
if errors:
    for error in errors:
        print("ERROR", error)
    raise RuntimeError("Final room verification failed")
