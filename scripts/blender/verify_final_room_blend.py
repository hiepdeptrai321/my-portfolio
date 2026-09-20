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
    "PC_Upgrade_Left_Fan_Halo",
    "PC_Upgrade_RGB_Fan_Halo",
    "PC_Upgrade_RGB_Fan_Ring",
    "PC_Upgrade_Right_Fan_Ring",
    "PC_Upgrade_Right_Fan_Halo",
    "PC_Upgrade_Top_LED_Strip_Halo",
    "PC_Upgrade_Top_LED_Strip",
    "PC_Upgrade_LED_Strip_Halo",
    "PC_Upgrade_LED_Strip",
    "PC_Upgrade_Cable_Hint_1",
    "PC_Upgrade_Cable_Hint_2",
    "PC_Upgrade_Glass_Panel",
}
reference_pc = bpy.data.collections.get("PC Reference Match") is not None
studio_pc = reference_pc and bpy.data.collections['PC Reference Match'].get('reference_version') == 'studio-v2'
if reference_pc:
    pc_upgrade_names = {
        "PC_Reference_Upper_Rear_Fan_Diffuser",
        "PC_Reference_Upper_Rear_Fan_Rotor",
        "PC_Reference_Upper_Rear_Fan_Hub",
        "PC_Reference_Lower_Rear_Fan_Rotor",
        "PC_Reference_Lower_Rear_Fan_Hub",
        "PC_Reference_Bottom_LED_Diffuser",
        "PC_Reference_Glass_Panel",
    } | {f"PC_Reference_GPU_{part}_{i}" for part in ("Fan", "Hub") for i in range(1, 4)} | {
        f"PC_Reference_Motherboard_Chip_{i}" for i in range(4)
    }
if studio_pc:
    pc_upgrade_names = {o.name for o in bpy.data.collections['PC Reference Match'].objects if o.type == 'MESH' and o.name != 'Plane.020_Baked'}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


errors = []
if studio_pc:
    required = {'PC_Reference_Top_Case', 'PC_Reference_Front_Panel', 'PC_Reference_Front_Perforations',
        'PC_Reference_Top_Mesh_Grille', 'PC_Reference_Floor_Mesh_Grille', 'PC_Reference_Glass_Panel',
        'PC_Reference_CPU_Cold_Plate', 'PC_Reference_RAM_Module_0', 'PC_Reference_RAM_Module_1',
        'PC_Reference_RAM_LED_0', 'PC_Reference_RAM_LED_1', 'PC_Reference_Cooling_Tube_0',
        'PC_Reference_Cooling_Tube_1', 'PC_Reference_GPU_Fan_1', 'PC_Reference_GPU_Fan_2',
        'PC_Reference_GPU_Fan_3', 'PC_Reference_Front_Heart_Cat_Silhouette',
        'PC_Reference_Top_LED_Diffuser', 'PC_Reference_Bottom_LED_Diffuser'}
    missing = required - pc_upgrade_names
    if missing: errors.append(f'Missing studio reference features: {sorted(missing)}')
scene = bpy.context.scene
if scene.camera is None or scene.camera.name != "Camera":
    errors.append(
        f"Expected active scene camera Camera, found "
        f"{scene.camera.name if scene.camera else None}"
    )
if scene.render.engine != "CYCLES":
    errors.append(f"Expected Cycles render engine, found {scene.render.engine}")
if (
    scene.render.resolution_x,
    scene.render.resolution_y,
    scene.render.resolution_percentage,
) != (2048, 2048, 100):
    errors.append(
        "Expected original render resolution 2048x2048 at 100%, found "
        f"{scene.render.resolution_x}x{scene.render.resolution_y} at "
        f"{scene.render.resolution_percentage}%"
    )
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

expected_mesh_count = 161 + len(special_names) + len(pc_upgrade_names)
if len(meshes) != expected_mesh_count:
    errors.append(f"Expected {expected_mesh_count} meshes, found {len(meshes)}")
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
pc_collection = bpy.data.collections.get("PC Reference Match" if reference_pc else "PC Upgrade")
case_used_materials = sorted({
    pc_case.material_slots[polygon.material_index].material.name
    for polygon in pc_case.data.polygons
    if polygon.material_index < len(pc_case.material_slots)
    and pc_case.material_slots[polygon.material_index].material is not None
}) if pc_case else []
pc_report = {
    "case_exists": pc_case is not None,
    "case_vertices": len(pc_case.data.vertices) if pc_case else None,
    "case_polygons": len(pc_case.data.polygons) if pc_case else None,
    "case_materials": [
        slot.material.name if slot.material else None
        for slot in pc_case.material_slots
    ] if pc_case else [],
    "case_used_materials": case_used_materials,
    "upgrade_collection_exists": pc_collection is not None,
    "upgrade_objects": sorted(obj.name for obj in pc_collection.objects if obj.type == "MESH" and obj.name != 'Plane.020_Baked')
    if pc_collection else [],
}
if not pc_case:
    errors.append("PC case Plane.020_Baked is missing")
elif not studio_pc and (pc_report["case_vertices"], pc_report["case_polygons"]) != (2904, 2408):
    errors.append("PC case geometry changed unexpectedly")
if "PC_Case_Blush_White" not in pc_report["case_used_materials"]:
    errors.append("PC case blush-white material is missing")
if not studio_pc and "PC_Logo_Deep_Mauve" not in pc_report["case_used_materials"]:
    errors.append("PC front-logo deep-mauve material is missing")
if set(pc_report["upgrade_objects"]) != pc_upgrade_names:
    errors.append("PC upgrade object set is incomplete")

expected_pc_materials = {
    "PC_Upgrade_CPU_Block": "PC_Case_Lavender_Trim",
    "PC_Upgrade_Cable_Hint_1": "PC_Fan_Pastel_Lilac",
    "PC_Upgrade_Cable_Hint_2": "PC_Internal_Soft_Lavender",
    "PC_Upgrade_GPU_Block": "PC_GPU_Muted_Plum",
    "PC_Upgrade_Glass_Panel": "PC_Glass_Cool_Tint",
    "PC_Upgrade_LED_Strip": "PC_LED_Lavender",
    "PC_Upgrade_LED_Strip_Halo": "PC_LED_Lavender_Halo",
    "PC_Upgrade_Left_Fan_Halo": "PC_LED_Lavender_Halo",
    "PC_Upgrade_Left_Fan_Ring": "PC_LED_Lavender",
    "PC_Upgrade_Motherboard": "PC_Motherboard_Mauve",
    "PC_Upgrade_RAM_Block_1": "PC_Internal_Soft_Lavender",
    "PC_Upgrade_RAM_Block_2": "PC_Fan_Pastel_Lilac",
    "PC_Upgrade_RGB_Fan_Halo": "PC_LED_Lavender_Halo",
    "PC_Upgrade_RGB_Fan_Ring": "PC_LED_Lavender",
    "PC_Upgrade_Right_Fan_Halo": "PC_LED_Lavender_Halo",
    "PC_Upgrade_Right_Fan_Ring": "PC_LED_Lavender",
    "PC_Upgrade_Top_LED_Strip": "PC_LED_Lavender",
    "PC_Upgrade_Top_LED_Strip_Halo": "PC_LED_Lavender_Halo",
}
if reference_pc:
    expected_pc_materials = {
        "PC_Reference_Upper_Rear_Fan_Diffuser": "PC_LED_Lavender",
        "PC_Reference_Upper_Rear_Fan_Rotor": "PC_Fan_Pastel_Lilac",
        "PC_Reference_Upper_Rear_Fan_Hub": "PC_Reference_Fan_Hub",
        "PC_Reference_Lower_Rear_Fan_Rotor": "PC_Fan_Pastel_Lilac",
        "PC_Reference_Lower_Rear_Fan_Hub": "PC_Reference_Fan_Hub",
        "PC_Reference_Glass_Panel": "PC_Glass_Cool_Tint",
        "PC_Reference_Bottom_LED_Diffuser": "PC_LED_Lavender",
    }
    expected_pc_materials.update({f"PC_Reference_GPU_Fan_{i}": "PC_Fan_Pastel_Lilac" for i in range(1, 4)})
    expected_pc_materials.update({f"PC_Reference_GPU_Hub_{i}": "PC_Reference_Small_LED" for i in range(1, 4)})
    expected_pc_materials.update({f"PC_Reference_Motherboard_Chip_{i}": "PC_Interior_Mauve_Gray" for i in range(4)})
    glass = bpy.data.materials.get("PC_Glass_Cool_Tint")
    glass_shader = next((n for n in glass.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if glass else None
    if not glass_shader or glass_shader.inputs["Transmission Weight"].default_value < .99:
        errors.append("Reference PC glass must use physical transmission")
    shell = bpy.data.materials.get("PC_Case_Blush_White")
    shell_shader = next((n for n in shell.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if shell else None
    if not shell_shader or shell_shader.inputs["Emission Strength"].default_value != 0:
        errors.append("Reference PC shell must receive light without self-emission")
    if any(o.name.startswith("PC_Upgrade_") for o in bpy.data.objects):
        errors.append("Obsolete upgrade geometry still obscures the reference PC")
if studio_pc:
    expected_pc_materials = {
        'PC_Reference_Glass_Panel':'PC_Glass_Cool_Tint',
        'PC_Reference_Front_Panel':'PC_Case_Blush_White',
        'PC_Reference_Front_Perforations':'PC_Case_Blush_White',
        'PC_Reference_Front_Heart_Cat_Silhouette':'PC_Logo_Deep_Mauve',
        'PC_Reference_CPU_Cold_Plate':'PC_Internal_Soft_Lavender',
        'PC_Reference_Upper_Rear_Fan_Diffuser':'PC_LED_Lavender',
        'PC_Reference_Top_LED_Diffuser':'PC_LED_Lavender',
        'PC_Reference_Bottom_LED_Diffuser':'PC_LED_Lavender',
        'PC_Reference_RAM_LED_0':'PC_LED_Lavender',
        'PC_Reference_RAM_LED_1':'PC_LED_Lavender',
    }
    expected_pc_materials.update({f'PC_Reference_GPU_Fan_{i}':'PC_Fan_Pastel_Lilac' for i in range(1,4)})
pc_report["upgrade_materials"] = {}
for object_name, expected_material in expected_pc_materials.items():
    obj = bpy.data.objects.get(object_name)
    actual_materials = [
        slot.material.name for slot in obj.material_slots if slot.material
    ] if obj else []
    pc_report["upgrade_materials"][object_name] = actual_materials
    if actual_materials != [expected_material]:
        errors.append(
            f"Unexpected material on {object_name}: {actual_materials}; "
            f"expected {expected_material}"
        )

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
    "active_camera": scene.camera.name if scene.camera else None,
    "render_engine": scene.render.engine,
    "render_resolution": [
        scene.render.resolution_x,
        scene.render.resolution_y,
        scene.render.resolution_percentage,
    ],
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
