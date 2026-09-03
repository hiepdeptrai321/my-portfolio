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
    "LinkedIn_Fourth_Raycaster_Pointer_Hover",
    "Tree_3",
    "Xbox_Controller_Raycaster_Hover",
}
pc_upgrade_names = {
    "PC_Upgrade_Motherboard",
    "PC_Upgrade_CPU_Block",
    "PC_Upgrade_RAM_Block_1",
    "PC_Upgrade_RAM_Block_2",
    "PC_Upgrade_GPU_Block",
    "PC_Upgrade_Left_Fan_Ring",
    "PC_Upgrade_RGB_Fan_Halo",
    "PC_Upgrade_RGB_Fan_Ring",
    "PC_Upgrade_Right_Fan_Ring",
    "PC_Upgrade_Top_Fan_Halo",
    "PC_Upgrade_Top_Fan_Ring",
    "PC_Upgrade_LED_Strip_Halo",
    "PC_Upgrade_LED_Strip",
    "PC_Upgrade_Cable_Hint_1",
    "PC_Upgrade_Cable_Hint_2",
    "PC_Upgrade_Glass_Panel",
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
special = [
    obj for obj in meshes if obj.name in special_names or obj.name in pc_upgrade_names
]
other = [obj for obj in meshes if obj not in baked and obj not in special]

if len(meshes) != 181:
    errors.append(f"Expected 181 meshes, found {len(meshes)}")
if len(baked) != 161:
    errors.append(f"Expected 161 baked room meshes, found {len(baked)}")
if {obj.name for obj in special} != special_names | pc_upgrade_names:
    errors.append("Final special-object set is incomplete")
if other:
    errors.append(f"Unexpected non-final meshes: {[obj.name for obj in other]}")
obsolete_social_objects = [
    obj.name
    for obj in bpy.data.objects
    if "twitter" in obj.name.lower() or "youtube" in obj.name.lower()
]
if obsolete_social_objects:
    errors.append(f"Obsolete social objects still exist: {obsolete_social_objects}")
if any(obj.hide_viewport or obj.hide_render for obj in meshes):
    errors.append("At least one final mesh is hidden")

empty_names = sorted(obj.name for obj in bpy.data.objects if obj.type == "EMPTY")
if empty_names != ["RootNode"]:
    errors.append(f"Unexpected Empty objects: {empty_names}")

controller = bpy.data.objects.get("Xbox_Controller_Raycaster_Hover")
controller_material = bpy.data.materials.get("Xbox_Controller_Material")
controller_image_node = (
    controller_material.node_tree.nodes.get("Image Texture")
    if controller_material and controller_material.node_tree
    else None
)
controller_report = {
    "exists": controller is not None,
    "vertices": len(controller.data.vertices) if controller else None,
    "polygons": len(controller.data.polygons) if controller else None,
    "location": [round(float(value), 6) for value in controller.location]
    if controller
    else None,
    "rotation": [round(float(value), 6) for value in controller.rotation_euler]
    if controller
    else None,
    "material": controller.active_material.name
    if controller and controller.active_material
    else None,
    "base_image": controller_image_node.image.name
    if controller_image_node and controller_image_node.image
    else None,
    "base_image_packed": bool(
        controller_image_node
        and controller_image_node.image
        and controller_image_node.image.packed_file
    ),
}
if not controller_report["exists"]:
    errors.append("Xbox controller is missing")
elif controller_report["vertices"] != 25656 or controller_report["polygons"] != 43119:
    errors.append("Xbox controller geometry changed unexpectedly")
if controller_report["rotation"] != [0.0, 0.0, 0.0]:
    errors.append(f"Xbox controller is not upright: {controller_report['rotation']}")
if controller_report["material"] != "Xbox_Controller_Material":
    errors.append(f"Unexpected Xbox material: {controller_report['material']}")
if not controller_report["base_image_packed"]:
    errors.append("Xbox base-color image is not packed")

pc_case = bpy.data.objects.get("Plane.020_Baked")
pc_collection = bpy.data.collections.get("PC Upgrade")
pc_report = {
    "case_exists": pc_case is not None,
    "case_vertices": len(pc_case.data.vertices) if pc_case else None,
    "case_polygons": len(pc_case.data.polygons) if pc_case else None,
    "case_materials": [
        slot.material.name if slot.material else None
        for slot in pc_case.material_slots
    ] if pc_case else [],
    "upgrade_collection_exists": pc_collection is not None,
    "upgrade_objects": sorted(obj.name for obj in pc_collection.objects)
    if pc_collection else [],
}
if not pc_case:
    errors.append("PC case Plane.020_Baked is missing")
elif (pc_report["case_vertices"], pc_report["case_polygons"]) != (2904, 2439):
    errors.append("PC case geometry changed unexpectedly")
if "PC_Case_Warm_Off_White" not in pc_report["case_materials"]:
    errors.append("PC case warm off-white material is missing")
if set(pc_report["upgrade_objects"]) != pc_upgrade_names:
    errors.append("PC upgrade object set is incomplete")

obsolete_controller_imports = [
    obj.name
    for obj in bpy.data.objects
    if obj.name == "Object_5"
    or "stand_fore_controller" in obj.name.lower()
]
if obsolete_controller_imports:
    errors.append(f"Obsolete controller imports still exist: {obsolete_controller_imports}")

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
    "empty_objects": empty_names,
    "obsolete_social_objects": obsolete_social_objects,
    "obsolete_controller_imports": obsolete_controller_imports,
    "missing_external_images": missing_images,
    "materials": material_reports,
    "xbox_controller": controller_report,
    "pc_upgrade": pc_report,
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
print("EMPTY_OBJECTS", report["empty_objects"])
print("OBSOLETE_SOCIAL_OBJECTS", report["obsolete_social_objects"])
print("OBSOLETE_CONTROLLER_IMPORTS", report["obsolete_controller_imports"])
print("XBOX_CONTROLLER", json.dumps(report["xbox_controller"], sort_keys=True))
print("MISSING_IMAGES", len(missing_images))
if errors:
    for error in errors:
        print("ERROR", error)
    raise RuntimeError("Final room verification failed")
