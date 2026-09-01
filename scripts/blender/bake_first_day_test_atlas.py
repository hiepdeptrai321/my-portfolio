"""Bake one non-production Day atlas for the first room texture set.

This intentionally uses Blender's native Cycles COMBINED selected-to-active bake
as a compatibility test. It does not replace the missing SimpleBake workflow and
never writes into public/textures.
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

import bpy


TARGET_COLLECTION = "First Texture Set"
TARGET_OBJECT = "First"
SOURCE_OBJECT_NAMES = (
    "Clock",
    "Cube",
    "Cube.009",
    "Cube.016",
    "Cube.018",
    "Cube.019",
    "Cube.020",
    "Cube.021",
    "Cube.027",
    "Cube.028",
    "Cube.036",
    "Cube.037",
    "Cube.039",
    "Lamp",
    "Plane.001",
    "Plane.003",
    "Plane.037",
    "Plane.039",
    "Plane.040",
    "Plane.041",
    "Plane.063",
    "Plane.064",
    "Torus.001",
    "Vert.012",
)
ATLAS_SIZE = 4096
BAKE_MARGIN = 16
BAKE_SAMPLES = 50  # Saved SimpleBake "boosted_sample_count" value.


def mesh_uv_signature(objects: list[bpy.types.Object]) -> str:
    """Hash mesh topology, coordinates, transforms, and all UV coordinates."""

    digest = hashlib.sha256()
    for obj in sorted(objects, key=lambda item: item.name):
        if obj.type != "MESH":
            continue
        digest.update(obj.name.encode("utf-8"))
        for value in obj.matrix_world:
            digest.update(struct.pack("4d", *value))
        mesh = obj.data
        digest.update(struct.pack("3I", len(mesh.vertices), len(mesh.loops), len(mesh.polygons)))
        for vertex in mesh.vertices:
            digest.update(struct.pack("3d", *vertex.co))
        for polygon in mesh.polygons:
            digest.update(struct.pack("2I", polygon.loop_start, polygon.loop_total))
        for uv_layer in mesh.uv_layers:
            digest.update(uv_layer.name.encode("utf-8"))
            for loop_uv in uv_layer.data:
                digest.update(struct.pack("2d", *loop_uv.uv))
    return digest.hexdigest()


def make_target_material(image: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("Grounded Pastel First Day Test Target")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    image_node = nodes.new("ShaderNodeTexImage")
    image_node.name = "Grounded Pastel Test Atlas"
    image_node.image = image
    nodes.active = image_node
    return material


def main() -> None:
    source_blend = Path(bpy.data.filepath).resolve()
    repo_root = source_blend.parent.parent
    export_blend = repo_root / "blender files" / "For Export.blend"
    night_source_blend = repo_root / "blender files" / "For Night Time Baking.blend"
    output_dir = repo_root / "artifacts" / "grounded-pastel-test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_png = output_dir / "first-texture-set-day-test.png"
    output_blend = output_dir / "first-day-test-bake.blend"

    if not export_blend.exists():
        raise FileNotFoundError(export_blend)

    source_meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    signature_before = mesh_uv_signature(source_meshes)

    with bpy.data.libraries.load(str(export_blend), link=False) as (data_from, data_to):
        if TARGET_COLLECTION not in data_from.collections:
            raise RuntimeError(f"{TARGET_COLLECTION!r} is missing from {export_blend}")
        data_to.collections = [TARGET_COLLECTION]

    target_collection = data_to.collections[0]
    bpy.context.scene.collection.children.link(target_collection)
    target = bpy.data.objects.get(TARGET_OBJECT)
    sources = [bpy.data.objects.get(name) for name in SOURCE_OBJECT_NAMES]
    missing_sources = [name for name, obj in zip(SOURCE_OBJECT_NAMES, sources) if obj is None]
    recovered_sources: list[str] = []
    if missing_sources:
        with bpy.data.libraries.load(str(night_source_blend), link=False) as (data_from, data_to):
            unavailable = [name for name in missing_sources if name not in data_from.objects]
            if unavailable:
                raise RuntimeError(
                    f"Sources absent from both Day and Night source files: {unavailable}"
                )
            data_to.objects = missing_sources
        for recovered in data_to.objects:
            bpy.context.scene.collection.objects.link(recovered)
            recovered_sources.append(recovered.name)
            if recovered.name == "Plane.003" and bpy.data.materials.get("Wood"):
                for slot in recovered.material_slots:
                    slot.material = bpy.data.materials["Wood"]
        sources = [bpy.data.objects.get(name) for name in SOURCE_OBJECT_NAMES]
        missing_sources = [name for name, obj in zip(SOURCE_OBJECT_NAMES, sources) if obj is None]
    invalid_sources = [obj.name for obj in sources if obj is not None and obj.type != "MESH"]
    if target is None or target.type != "MESH" or not target.data.uv_layers:
        raise RuntimeError(f"Merged target {TARGET_OBJECT!r} or its existing UV layout is missing")
    if missing_sources or invalid_sources:
        raise RuntimeError(
            f"Bake pairing validation failed; missing sources={missing_sources}, "
            f"non-mesh sources={invalid_sources}"
        )
    sources = [obj for obj in sources if obj is not None]

    atlas = bpy.data.images.new(
        "Grounded Pastel First Day Test Atlas",
        width=ATLAS_SIZE,
        height=ATLAS_SIZE,
        alpha=True,
        float_buffer=True,
    )
    atlas.generated_color = (0.0, 0.0, 0.0, 0.0)
    atlas.colorspace_settings.name = "sRGB"
    target_material = make_target_material(atlas)

    target.data.materials.clear()
    target.data.materials.append(target_material)
    for polygon in target.data.polygons:
        polygon.material_index = 0
    target.hide_render = False
    target.hide_set(False)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = BAKE_SAMPLES
    scene.render.bake.target = "IMAGE_TEXTURES"
    scene.render.bake.margin = BAKE_MARGIN
    scene.render.bake.margin_type = "EXTEND"
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.cage_extrusion = 0.1
    scene.render.bake.max_ray_distance = 0.0
    scene.render.bake.use_pass_direct = True
    scene.render.bake.use_pass_indirect = True
    scene.render.bake.use_pass_color = True

    print(f"TEST_BAKE_CONFIG atlas={ATLAS_SIZE}x{ATLAS_SIZE} margin={BAKE_MARGIN} samples={BAKE_SAMPLES}")
    print(
        f"TEST_BAKE_GROUP sources={len(sources)} target={TARGET_OBJECT} "
        f"collection={TARGET_COLLECTION} uv={target.data.uv_layers.active.name}"
    )
    print(f"TEST_BAKE_RECOVERED_FROM_NIGHT_SOURCE {recovered_sources}")
    print(f"SOURCE_GEOMETRY_UV_SIGNATURE_BEFORE {signature_before}")

    bpy.ops.object.select_all(action="DESELECT")
    for source in sources:
        source.hide_set(False)
        source.hide_render = False
        source.select_set(True)
        print(f"TEST_BAKE_SOURCE {source.name}")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    print(f"TEST_BAKE_START {' + '.join(SOURCE_OBJECT_NAMES)} -> {TARGET_OBJECT}", flush=True)
    bpy.ops.object.bake(type="COMBINED", use_clear=True)
    print("TEST_BAKE_FINISHED", flush=True)

    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "16"
    scene.render.image_settings.compression = 15
    atlas.filepath_raw = str(output_png)
    atlas.file_format = "PNG"
    atlas.save_render(str(output_png), scene=scene)

    signature_after = mesh_uv_signature(source_meshes)
    if signature_after != signature_before:
        raise RuntimeError(
            "Source geometry or UVs changed during the test bake: "
            f"{signature_before} -> {signature_after}"
        )

    scene["grounded_pastel_test_bake"] = True
    scene["grounded_pastel_test_bake_source"] = str(source_blend)
    scene["grounded_pastel_test_bake_atlas"] = str(output_png)
    scene["grounded_pastel_test_bake_method"] = "Cycles COMBINED selected-to-active"
    scene["grounded_pastel_test_bake_geometry_uv_signature"] = signature_after
    bpy.ops.wm.save_as_mainfile(filepath=str(output_blend), check_existing=False)

    print(f"SOURCE_GEOMETRY_UV_SIGNATURE_AFTER {signature_after}")
    print(f"TEST_BAKE_OUTPUT {output_png}")
    print(f"TEST_BAKE_WORKSPACE {output_blend}")


if __name__ == "__main__":
    main()
