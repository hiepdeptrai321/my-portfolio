"""Finish the Xbox controller in the final blend and export it for the web."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


CONTROLLER_NAME = "Xbox_Controller_Raycaster_Hover"
CONTROLLER_SOURCE_NAME = "Object_5"
CONTROLLER_MATERIAL_NAME = "Xbox_Controller_Material"
LINKEDIN_NAME = "LinkedIn_Fourth_Raycaster_Pointer_Hover"
LINKEDIN_SOURCE_NAME = "Objeto_1_Tinta (1)_0"
SHELF_NAME = "Plane.041_Baked"
STAND_ROOT_NAME = "stand_fore_controller_Xbox.obj.cleaner.materialmerger.gles"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def world_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [min(corner[axis] for corner in corners) for axis in range(3)],
        "max": [max(corner[axis] for corner in corners) for axis in range(3)],
    }


def detach_preserving_world_transform(obj):
    matrix_world = obj.matrix_world.copy()
    obj.parent = None
    obj.matrix_world = matrix_world
    bpy.context.view_layer.update()


def descendants(root_object):
    result = []
    stack = [root_object]
    while stack:
        current = stack.pop()
        result.append(current)
        stack.extend(current.children)
    return result


blend_path = Path(bpy.data.filepath).resolve()
root = blend_path.parent.parent
output_glb = root / "public/models/xbox-controller.glb"
report_path = root / "artifacts/final-room-audit/xbox-controller-export.json"

if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

controller = bpy.data.objects.get(CONTROLLER_NAME) or bpy.data.objects.get(
    CONTROLLER_SOURCE_NAME
)
if controller is None or controller.type != "MESH":
    raise RuntimeError("Xbox controller mesh was not found")
if len(controller.data.vertices) != 25656 or len(controller.data.polygons) != 43119:
    raise RuntimeError(
        f"Unexpected Xbox geometry: {len(controller.data.vertices)} vertices, "
        f"{len(controller.data.polygons)} polygons"
    )

shelf = bpy.data.objects.get(SHELF_NAME)
if shelf is None or shelf.type != "MESH":
    raise RuntimeError("Target shelf was not found")

# Detach the controller from its imported wrapper hierarchy. Keep its authored
# world scale, remove the accidental two-degree lean, and seat it just above
# the shelf so the handles no longer intersect the wood.
detach_preserving_world_transform(controller)
world_location, _, world_scale = controller.matrix_world.decompose()
controller.location = world_location
controller.rotation_mode = "XYZ"
controller.rotation_euler = (0.0, 0.0, 0.0)
controller.scale = world_scale
controller.name = CONTROLLER_NAME
controller.data.name = f"{CONTROLLER_NAME}_Mesh"
bpy.context.view_layer.update()

shelf_top = world_bounds(shelf)["max"][2]
controller_bottom = world_bounds(controller)["min"][2]
controller.location.z += shelf_top + 0.003 - controller_bottom
bpy.context.view_layer.update()

# Keep the model's packed color atlas, including the colored ABXY buttons, but
# normalize the physically implausible imported Principled values.
material = controller.active_material
if material is None or material.node_tree is None:
    raise RuntimeError("Xbox controller material is missing")
material.name = CONTROLLER_MATERIAL_NAME
principled = material.node_tree.nodes.get("Principled BSDF")
if principled is None:
    raise RuntimeError("Xbox controller Principled BSDF node is missing")

for link in list(material.node_tree.links):
    if link.to_node == principled and link.to_socket.name in {"Roughness", "Specular Tint"}:
        material.node_tree.links.remove(link)

principled.inputs["Metallic"].default_value = 0.0
principled.inputs["Roughness"].default_value = 0.68
principled.inputs["IOR"].default_value = 1.46
principled.inputs["Specular IOR Level"].default_value = 0.28
principled.inputs["Coat Weight"].default_value = 0.08
principled.inputs["Coat Roughness"].default_value = 0.35

# Restore the semantic LinkedIn name before removing now-unused import Empty
# wrappers. This keeps the authoritative blend easy to edit later.
linkedin = bpy.data.objects.get(LINKEDIN_NAME) or bpy.data.objects.get(
    LINKEDIN_SOURCE_NAME
)
if linkedin is not None and linkedin.type == "MESH":
    detach_preserving_world_transform(linkedin)
    linkedin.name = LINKEDIN_NAME
    linkedin.data.name = f"{LINKEDIN_NAME}_Mesh"

# The imported stand is a separate, double-controller desktop holder hundreds
# of units outside the room. It is not used by the shelf composition.
removed_stand_objects = []
stand_root = bpy.data.objects.get(STAND_ROOT_NAME)
if stand_root is not None:
    for obj in reversed(descendants(stand_root)):
        removed_stand_objects.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)

# With the controller and LinkedIn detached, only RootNode remains meaningful
# because it parents the outside tree.
removed_empty_objects = []
for obj in list(bpy.data.objects):
    if obj.type == "EMPTY" and obj.name != "RootNode":
        removed_empty_objects.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)

bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), compress=True)

bpy.ops.object.select_all(action="DESELECT")
controller.select_set(True)
bpy.context.view_layer.objects.active = controller
output_glb.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=str(output_glb),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
    export_materials="EXPORT",
    export_cameras=False,
    export_lights=False,
    export_draco_mesh_compression_enable=True,
    export_draco_mesh_compression_level=6,
)

final_bounds = world_bounds(controller)
report = {
    "blend": str(blend_path),
    "blend_size_bytes": blend_path.stat().st_size,
    "blend_sha256": sha256(blend_path),
    "object": controller.name,
    "mesh": controller.data.name,
    "location": [round(float(value), 6) for value in controller.location],
    "rotation": [round(float(value), 6) for value in controller.rotation_euler],
    "scale": [round(float(value), 6) for value in controller.scale],
    "dimensions": [round(float(value), 6) for value in controller.dimensions],
    "world_bounds": {
        key: [round(float(value), 6) for value in values]
        for key, values in final_bounds.items()
    },
    "shelf": shelf.name,
    "shelf_top": round(float(shelf_top), 6),
    "shelf_gap": round(float(final_bounds["min"][2] - shelf_top), 6),
    "vertices": len(controller.data.vertices),
    "polygons": len(controller.data.polygons),
    "material": material.name,
    "material_values": {
        "metallic": principled.inputs["Metallic"].default_value,
        "roughness": principled.inputs["Roughness"].default_value,
        "ior": principled.inputs["IOR"].default_value,
        "specular_ior_level": principled.inputs["Specular IOR Level"].default_value,
        "coat_weight": principled.inputs["Coat Weight"].default_value,
        "coat_roughness": principled.inputs["Coat Roughness"].default_value,
    },
    "removed_stand_objects": sorted(removed_stand_objects),
    "removed_empty_objects": sorted(removed_empty_objects),
    "remaining_type_counts": {
        object_type: sum(1 for obj in bpy.data.objects if obj.type == object_type)
        for object_type in sorted({obj.type for obj in bpy.data.objects})
    },
    "output_glb": str(output_glb),
    "output_size_bytes": output_glb.stat().st_size,
    "output_sha256": sha256(output_glb),
}
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("XBOX_OBJECT", report["object"])
print("XBOX_LOCATION", report["location"])
print("XBOX_ROTATION", report["rotation"])
print("XBOX_DIMENSIONS", report["dimensions"])
print("XBOX_SHELF_GAP", report["shelf_gap"])
print("XBOX_MATERIAL", report["material"], json.dumps(report["material_values"]))
print("REMOVED_STAND", json.dumps(report["removed_stand_objects"]))
print("REMOVED_EMPTIES", len(report["removed_empty_objects"]))
print("REMAINING_TYPES", json.dumps(report["remaining_type_counts"], sort_keys=True))
print("XBOX_GLB", output_glb)
print("XBOX_GLB_SIZE", report["output_size_bytes"])
print("XBOX_GLB_SHA256", report["output_sha256"])
print("BLEND_SHA256", report["blend_sha256"])
