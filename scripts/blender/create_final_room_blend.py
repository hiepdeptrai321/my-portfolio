"""Create the single clean final room blend from My Room.blend.

The source already contains the user's final Facebook card and outside tree.
This script applies the approved Grounded Pastel Day atlases to the baked room,
removes obsolete source/baking meshes from the new copy, and keeps exactly the
baked room plus Facebook and Tree_3 as visible mesh content.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def walk_layer_collections(layer_collection):
    yield layer_collection
    for child in layer_collection.children:
        yield from walk_layer_collections(child)


source_blend = Path(bpy.data.filepath).resolve()
root = source_blend.parent.parent
output_blend = source_blend.parent / "My Room - FINAL.blend"
texture_root = root / "public/textures/room/grounded-pastel-test"
report_path = root / "artifacts/final-room-audit/final-room-create.json"

atlas_materials = {
    "First": (
        "FinalFirst_Baked",
        texture_root / "first-texture-set-day-grounded-test.webp",
    ),
    "Second": (
        "RealFinalSecond_Baked",
        texture_root / "second-texture-set-day-grounded-test.webp",
    ),
    "Third": (
        "FinalThird_Baked",
        texture_root / "third-texture-set-day-grounded-test.webp",
    ),
    "Fourth": (
        "FinalFourth_Baked",
        texture_root / "fourth-texture-set-day-grounded-test.webp",
    ),
}
baked_material_names = {material for material, _ in atlas_materials.values()}
required_special_objects = {
    "Facebook_Fifth_Raycaster_Pointer_Hover": {
        "location": (-1.012596, 4.177194, 6.151619),
    },
    "Tree_3": {
        "location": (-1.056770, 5.865587, -1.012815),
    },
}


def srgb_hex_to_linear(hex_color: str):
    channels = [int(hex_color[index : index + 2], 16) / 255.0 for index in (1, 3, 5)]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return (*linear, 1.0)


def configure_principled_material(
    material_name,
    *,
    base_color=None,
    metallic=0.0,
    roughness=0.6,
    specular=0.3,
    coat=0.0,
):
    material = bpy.data.materials.get(material_name)
    if material is None or material.node_tree is None:
        raise RuntimeError(f"Missing final special material: {material_name}")
    principled = next(
        (
            node
            for node in material.node_tree.nodes
            if node.bl_idname == "ShaderNodeBsdfPrincipled"
        ),
        None,
    )
    if principled is None:
        raise RuntimeError(f"Missing Principled node: {material_name}")
    if base_color is not None:
        linear_color = srgb_hex_to_linear(base_color)
        principled.inputs["Base Color"].default_value = linear_color
        material.diffuse_color = linear_color
    if principled.inputs.get("Weight") is not None:
        principled.inputs["Weight"].default_value = 1.0
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    if principled.inputs.get("Specular IOR Level") is not None:
        principled.inputs["Specular IOR Level"].default_value = specular
    if principled.inputs.get("Coat Weight") is not None:
        principled.inputs["Coat Weight"].default_value = coat

source_hash_before = sha256(source_blend)
material_reports = {}

for atlas_name, (material_name, texture_path) in atlas_materials.items():
    if not texture_path.is_file():
        raise FileNotFoundError(texture_path)
    material = bpy.data.materials.get(material_name)
    if material is None or material.node_tree is None:
        raise RuntimeError(f"Missing baked material: {material_name}")

    image_nodes = [
        node
        for node in material.node_tree.nodes
        if node.bl_idname == "ShaderNodeTexImage"
    ]
    emission_nodes = [
        node
        for node in material.node_tree.nodes
        if node.bl_idname == "ShaderNodeEmission"
    ]
    if not image_nodes or not emission_nodes:
        raise RuntimeError(f"Unexpected baked material nodes: {material_name}")

    image = bpy.data.images.load(str(texture_path), check_existing=False)
    image.name = f"Grounded_{atlas_name}_Day_FINAL"
    image.colorspace_settings.name = "sRGB"
    image.pack()

    image_node = image_nodes[0]
    image_node.name = "Grounded Pastel Day FINAL"
    image_node.label = f"{atlas_name} Grounded Day (packed)"
    image_node.image = image
    image_node.interpolation = "Linear"

    emission = emission_nodes[0]
    for link in list(material.node_tree.links):
        if link.to_node == emission and link.to_socket == emission.inputs["Color"]:
            material.node_tree.links.remove(link)
    material.node_tree.links.new(image_node.outputs["Color"], emission.inputs["Color"])
    material["grounded_pastel_mode"] = "day"
    material["grounded_pastel_texture"] = texture_path.name

    material_reports[atlas_name] = {
        "material": material_name,
        "texture": texture_path.relative_to(root).as_posix(),
        "texture_sha256": sha256(texture_path),
        "packed": image.packed_file is not None,
        "dimensions": list(image.size),
    }

for name, expected in required_special_objects.items():
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise RuntimeError(f"Required final object is missing: {name}")
    if any(abs(float(obj.location[index]) - expected["location"][index]) > 1e-4 for index in range(3)):
        raise RuntimeError(f"Unexpected transform for final object: {name}")

# Match the exact calm Facebook palette used by src/main.js and repair the GLB
# Principled weights so Facebook/tree shade correctly inside Blender as well.
configure_principled_material(
    "Material.001",
    base_color="#455A86",
    roughness=0.72,
    specular=0.25,
    coat=0.08,
)
configure_principled_material(
    "Material.f",
    base_color="#DED8D4",
    roughness=0.64,
    specular=0.25,
    coat=0.05,
)
configure_principled_material(
    "Tree_Green",
    roughness=0.58,
    specular=0.28,
    coat=0.10,
)
configure_principled_material(
    "Tree_Wood",
    roughness=0.68,
    specular=0.24,
    coat=0.03,
)

if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

baked_collection = bpy.data.collections.get("SimpleBake_Bakes")
if baked_collection is None:
    raise RuntimeError("Missing SimpleBake_Bakes collection")
baked_collection.hide_viewport = False
baked_collection.hide_render = False
for view_layer in bpy.context.scene.view_layers:
    for layer_collection in walk_layer_collections(view_layer.layer_collection):
        if layer_collection.name == "SimpleBake_Bakes":
            layer_collection.exclude = False
            layer_collection.hide_viewport = False

baked_objects = []
special_objects = []
obsolete_meshes = []
for obj in list(bpy.data.objects):
    if obj.type != "MESH":
        continue
    uses_baked_material = any(
        slot.material is not None and slot.material.name in baked_material_names
        for slot in obj.material_slots
    )
    if uses_baked_material:
        baked_objects.append(obj)
    elif obj.name in required_special_objects:
        special_objects.append(obj)
    else:
        obsolete_meshes.append(obj)

if len(baked_objects) != 165:
    raise RuntimeError(f"Expected 165 baked room meshes, found {len(baked_objects)}")
if {obj.name for obj in special_objects} != set(required_special_objects):
    raise RuntimeError("Facebook/Tree final-object set does not match expectations")

for obj in obsolete_meshes:
    bpy.data.objects.remove(obj, do_unlink=True)

# Each baked material accumulated historical atlas image nodes. They are not
# connected to the final emission output, but their missing paths still make the
# file look broken in Blender's dependency checks. Keep only the packed FINAL
# atlas node in each of the four live baked materials.
for material_name, _ in atlas_materials.values():
    material = bpy.data.materials[material_name]
    for node in list(material.node_tree.nodes):
        if (
            node.bl_idname == "ShaderNodeTexImage"
            and node.name != "Grounded Pastel Day FINAL"
        ):
            material.node_tree.nodes.remove(node)

# Replace the unavailable authoring HDRI with a neutral self-contained world.
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("Final Room World")
    bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes.clear()
world_output = world.node_tree.nodes.new("ShaderNodeOutputWorld")
background = world.node_tree.nodes.new("ShaderNodeBackground")
background.inputs["Color"].default_value = (0.055, 0.055, 0.055, 1.0)
background.inputs["Strength"].default_value = 0.35
world.node_tree.links.new(background.outputs["Background"], world_output.inputs["Surface"])

daylight_data = bpy.data.lights.get("Final Daylight")
if daylight_data is None:
    daylight_data = bpy.data.lights.new("Final Daylight", type="SUN")
daylight_data.energy = 1.8
daylight_data.angle = math.radians(18.0)
daylight = bpy.data.objects.get("Final Daylight")
if daylight is None:
    daylight = bpy.data.objects.new("Final Daylight", daylight_data)
    bpy.context.scene.collection.objects.link(daylight)
daylight.rotation_euler = (
    math.radians(28.0),
    math.radians(-24.0),
    math.radians(-38.0),
)

fill_data = bpy.data.lights.get("Final Fill")
if fill_data is None:
    fill_data = bpy.data.lights.new("Final Fill", type="SUN")
fill_data.energy = 0.65
fill_data.angle = math.radians(50.0)
fill = bpy.data.objects.get("Final Fill")
if fill is None:
    fill = bpy.data.objects.new("Final Fill", fill_data)
    bpy.context.scene.collection.objects.link(fill)
fill.rotation_euler = (
    math.radians(-24.0),
    math.radians(32.0),
    math.radians(142.0),
)

for obj in baked_objects + special_objects:
    obj.hide_viewport = False
    obj.hide_render = False
    if bpy.context.view_layer.objects.get(obj.name) is not None:
        obj.hide_set(False)
    parent = obj.parent
    while parent is not None:
        parent.hide_viewport = False
        parent.hide_render = False
        if bpy.context.view_layer.objects.get(parent.name) is not None:
            parent.hide_set(False)
        parent = parent.parent

for collection in list(bpy.data.collections):
    if not collection.objects and not collection.children:
        bpy.data.collections.remove(collection)

for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
    for datablock in list(datablocks):
        if datablock.users == 0:
            datablocks.remove(datablock)

for image in list(bpy.data.images):
    if not image.name.startswith("Grounded_"):
        bpy.data.images.remove(image, do_unlink=True)

bpy.ops.object.select_all(action="DESELECT")
facebook = bpy.data.objects["Facebook_Fifth_Raycaster_Pointer_Hover"]
facebook.select_set(True)
bpy.context.view_layer.objects.active = facebook

readme = bpy.data.texts.get("FINAL_ROOM_README") or bpy.data.texts.new(
    "FINAL_ROOM_README"
)
readme.clear()
readme.write(
    "My Room - FINAL\n"
    "===============\n\n"
    "Single clean Grounded Pastel Day room file.\n"
    "Includes the final Facebook_Fifth_Raycaster_Pointer_Hover and Tree_3.\n"
    "The obsolete Twitter card and authoring/source meshes are not included.\n"
    "All four 4096x4096 Grounded Pastel room atlases are packed.\n"
)

for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.shading.type = "MATERIAL"

bpy.ops.wm.save_as_mainfile(filepath=str(output_blend), compress=True)

report = {
    "source": str(source_blend),
    "source_sha256_before": source_hash_before,
    "source_sha256_after": sha256(source_blend),
    "source_unchanged": source_hash_before == sha256(source_blend),
    "output": str(output_blend),
    "output_sha256": sha256(output_blend),
    "output_size_bytes": output_blend.stat().st_size,
    "baked_room_meshes": len(baked_objects),
    "special_objects": sorted(obj.name for obj in special_objects),
    "removed_obsolete_meshes": len(obsolete_meshes),
    "final_mesh_count": sum(1 for obj in bpy.data.objects if obj.type == "MESH"),
    "materials": material_reports,
}
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("FINAL_ROOM_BLEND", output_blend)
print("FINAL_ROOM_REPORT", report_path)
print("SOURCE_UNCHANGED", report["source_unchanged"])
print("BAKED_ROOM_MESHES", report["baked_room_meshes"])
print("SPECIAL_OBJECTS", report["special_objects"])
print("REMOVED_OBSOLETE_MESHES", report["removed_obsolete_meshes"])
print("FINAL_MESH_COUNT", report["final_mesh_count"])
print("OUTPUT_SHA256", report["output_sha256"])
