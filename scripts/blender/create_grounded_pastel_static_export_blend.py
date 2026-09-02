"""Create one deterministic Grounded Pastel Day or Night export-preview blend.

Usage:
  blender --background "For Export.blend" --python this_script.py -- --mode day
  blender --background "For Export.blend" --python this_script.py -- --mode night
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy


def parse_args() -> argparse.Namespace:
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("day", "night"), required=True)
    return parser.parse_args(arguments)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


args = parse_args()
mode = args.mode
mode_title = mode.title()
source_blend = Path(bpy.data.filepath).resolve()
root = source_blend.parent.parent
test_root = root / "public/textures/room/grounded-pastel-test"
output_blend = source_blend.parent / f"For Export - Grounded Pastel {mode_title}.blend"
report_path = (
    root
    / f"artifacts/grounded-pastel-no-rebake/grounded-pastel-{mode}-blend-create.json"
)

atlas_materials = {
    "First": {
        "material": "FinalFirst_Baked",
        "texture": test_root / f"first-texture-set-{mode}-grounded-test.webp",
    },
    "Second": {
        "material": "RealFinalSecond_Baked",
        "texture": test_root / f"second-texture-set-{mode}-grounded-test.webp",
    },
    "Third": {
        "material": "FinalThird_Baked",
        "texture": test_root / f"third-texture-set-{mode}-grounded-test.webp",
    },
    "Fourth": {
        "material": "FinalFourth_Baked",
        "texture": test_root / f"fourth-texture-set-{mode}-grounded-test.webp",
    },
}

baked_collection_name = "SimpleBake_Bakes"
baked_material_names = {
    definition["material"] for definition in atlas_materials.values()
}

source_hash_before = sha256(source_blend)
material_reports = {}

for atlas_name, definition in atlas_materials.items():
    texture_path = definition["texture"]
    if not texture_path.is_file():
        raise FileNotFoundError(texture_path)
    material = bpy.data.materials.get(definition["material"])
    if material is None or material.node_tree is None:
        raise RuntimeError(f"Missing baked node material: {definition['material']}")

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
        raise RuntimeError(f"Unexpected material nodes: {material.name}")

    image = bpy.data.images.load(str(texture_path), check_existing=False)
    image.name = f"Grounded_{atlas_name}_{mode_title}"
    image.colorspace_settings.name = "sRGB"
    image.pack()

    image_node = image_nodes[0]
    image_node.name = f"Grounded Pastel {mode_title}"
    image_node.label = f"{atlas_name} Grounded {mode_title} (packed)"
    image_node.image = image
    image_node.interpolation = "Linear"

    emission = emission_nodes[0]
    for link in list(material.node_tree.links):
        if link.to_node == emission and link.to_socket == emission.inputs["Color"]:
            material.node_tree.links.remove(link)
    material.node_tree.links.new(image_node.outputs["Color"], emission.inputs["Color"])

    material["grounded_pastel_mode"] = mode
    material["grounded_pastel_texture"] = texture_path.name
    material_reports[atlas_name] = {
        "material": material.name,
        "texture": texture_path.relative_to(root).as_posix(),
        "texture_sha256": sha256(texture_path),
        "image": image.name,
        "packed": image.packed_file is not None,
        "dimensions": list(image.size),
        "object_users": sum(
            1
            for obj in bpy.data.objects
            if obj.type == "MESH"
            and any(slot.material == material for slot in obj.material_slots)
        ),
    }


def walk_layer_collections(layer_collection):
    yield layer_collection
    for child in layer_collection.children:
        yield from walk_layer_collections(child)


# For Export.blend is saved in authoring mode: the baked collection is excluded,
# while the source/target meshes are visible. That is useful for baking, but it
# makes missing source textures cover the preview in magenta. Keep all data in the
# safe copy, and change visibility only so the packed baked atlases are what users
# see when the file opens.
if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

baked_collection = bpy.data.collections.get(baked_collection_name)
if baked_collection is None:
    raise RuntimeError(f"Missing baked collection: {baked_collection_name}")
baked_collection.hide_viewport = False
baked_collection.hide_render = False

for view_layer in bpy.context.scene.view_layers:
    for layer_collection in walk_layer_collections(view_layer.layer_collection):
        if layer_collection.name == baked_collection_name:
            layer_collection.exclude = False
            layer_collection.hide_viewport = False

visibility_report = {
    "baked_meshes_visible": 0,
    "source_meshes_hidden": 0,
    "baked_collection": baked_collection_name,
}
baked_objects = []
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    uses_baked_material = any(
        slot.material is not None and slot.material.name in baked_material_names
        for slot in obj.material_slots
    )
    if uses_baked_material:
        obj.hide_viewport = False
        obj.hide_render = False
        if bpy.context.view_layer.objects.get(obj.name) is not None:
            obj.hide_set(False)
        baked_objects.append(obj)
        visibility_report["baked_meshes_visible"] += 1
    else:
        obj.hide_viewport = True
        obj.hide_render = True
        if bpy.context.view_layer.objects.get(obj.name) is not None:
            obj.hide_set(True)
        visibility_report["source_meshes_hidden"] += 1

if not baked_objects:
    raise RuntimeError("No mesh objects use the baked atlas materials")

bpy.ops.object.select_all(action="DESELECT")
baked_objects[0].select_set(True)
bpy.context.view_layer.objects.active = baked_objects[0]

readme = bpy.data.texts.get("GROUNDED_PASTEL_README")
if readme is None:
    readme = bpy.data.texts.new("GROUNDED_PASTEL_README")
else:
    readme.clear()
readme.write(
    f"Grounded Pastel {mode_title} Blend\n"
    f"{'=' * (23 + len(mode_title))}\n\n"
    "This is a safe copy of For Export.blend.\n"
    f"It contains the four exact Grounded Pastel {mode_title} test atlases.\n"
    "All four images are packed into this .blend.\n\n"
    "Use Material Preview or Rendered viewport shading to see the colors.\n"
    "Only the SimpleBake_Bakes meshes are visible; source baking meshes are kept but hidden.\n"
    "No geometry, UV, object name, production texture, or source blend was changed.\n"
)

for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.shading.type = "MATERIAL"

bpy.ops.wm.save_as_mainfile(filepath=str(output_blend), compress=True)

report = {
    "mode": mode,
    "source_blend": str(source_blend),
    "source_sha256_before": source_hash_before,
    "source_sha256_after": sha256(source_blend),
    "source_unchanged": source_hash_before == sha256(source_blend),
    "output_blend": str(output_blend),
    "output_sha256": sha256(output_blend),
    "output_size_bytes": output_blend.stat().st_size,
    "materials": material_reports,
    "visibility": visibility_report,
    "packed_grounded_images": sorted(
        image.name
        for image in bpy.data.images
        if image.name.startswith("Grounded_") and image.packed_file is not None
    ),
}
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("GROUNDED_STATIC_BLEND", output_blend)
print("GROUNDED_STATIC_REPORT", report_path)
print("MODE", mode)
print("SOURCE_UNCHANGED", report["source_unchanged"])
print("OUTPUT_SHA256", report["output_sha256"])
print("PACKED_IMAGES", len(report["packed_grounded_images"]))
print("VISIBILITY", json.dumps(visibility_report, sort_keys=True))
