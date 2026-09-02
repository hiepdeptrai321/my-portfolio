"""Read-only audit of saved SimpleBake metadata and Blender bake prerequisites."""

from __future__ import annotations

import json
from pathlib import Path

import bpy


SIMPLEBAKE_KEYS = (
    "global_mode",
    "merged_bake",
    "merged_bake_name",
    "selected_col",
    "selected_s2a",
    "cycles_s2a",
    "s2a_opmode",
    "targetobj",
    "targetobj_cycles",
    "ray_distance",
    "cage_extrusion",
    "auto_match_mode",
    "imgwidth",
    "imgheight",
    "outputwidth",
    "outputheight",
    "everything32bitfloat",
    "everything_16bit",
    "use_alpha",
    "tex_per_mat",
    "new_uv_option",
    "prefer_existing_sbmap",
    "restore_orig_uv_map",
    "uvpackmargin",
    "unwrapmargin",
    "average_uv_size",
    "uvcorrectaspect",
    "save_bakes_external",
    "export_folder_per_object",
    "export_format",
    "export_path",
    "copy_and_apply",
    "hide_source_objects",
    "apply_bakes_to_original",
    "preserve_materials",
    "clear_image",
    "boosted_sample_count",
    "cyclesbake_cs",
    "export_cycles_col_space",
    "bgbake",
    "batch_name",
    "isolate_objects",
    "fg_status_message",
    "total_bake_images_number",
    "percent_complete",
)


def json_value(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, "name"):
        return value.name
    try:
        return [json_value(item) for item in value]
    except TypeError:
        return str(value)


def collection_items(group, key: str) -> list[dict[str, object]]:
    if key not in group:
        return []
    result = []
    for item in group[key]:
        result.append({name: json_value(item[name]) for name in item.keys()})
    return result


scene = bpy.context.scene
blend_path = Path(bpy.data.filepath).resolve()
simplebake = scene.get("SimpleBake_Props")
mesh_objects = [obj for obj in scene.objects if obj.type == "MESH"]

report: dict[str, object] = {
    "blend_file": str(blend_path),
    "blend_data_version": list(bpy.data.version),
    "blender_runtime": bpy.app.version_string,
    "render": {
        "engine": scene.render.engine,
        "cycles_samples": scene.cycles.samples,
        "cycles_device": scene.cycles.device,
        "bake_margin": scene.render.bake.margin,
        "bake_margin_type": scene.render.bake.margin_type,
        "bake_use_selected_to_active": scene.render.bake.use_selected_to_active,
        "bake_cage_extrusion": scene.render.bake.cage_extrusion,
        "bake_max_ray_distance": scene.render.bake.max_ray_distance,
        "bake_pass_direct": scene.render.bake.use_pass_direct,
        "bake_pass_indirect": scene.render.bake.use_pass_indirect,
        "bake_pass_color": scene.render.bake.use_pass_color,
        "view_transform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "exposure": scene.view_settings.exposure,
        "gamma": scene.view_settings.gamma,
    },
    "scene_markers": {
        key: json_value(scene[key])
        for key in scene.keys()
        if "grounded" in key.lower() or "simplebake" in key.lower()
    },
    "mesh_uv": {
        "mesh_object_count": len(mesh_objects),
        "without_uv": sorted(obj.name for obj in mesh_objects if not obj.data.uv_layers),
        "with_simplebake_uv": sorted(
            obj.name for obj in mesh_objects if obj.data.uv_layers.get("SimpleBake") is not None
        ),
        "active_uv_counts": {},
    },
    "images": [],
    "materials": {
        "count": len(bpy.data.materials),
        "without_nodes": [],
        "without_surface_output_link": [],
        "image_nodes_without_image": [],
    },
}

active_uv_counts: dict[str, int] = {}
for obj in mesh_objects:
    active = obj.data.uv_layers.active
    key = active.name if active else "<none>"
    active_uv_counts[key] = active_uv_counts.get(key, 0) + 1
report["mesh_uv"]["active_uv_counts"] = active_uv_counts

if simplebake is None:
    report["simplebake"] = None
else:
    report["simplebake"] = {
        "saved_keys": {key: json_value(simplebake[key]) for key in SIMPLEBAKE_KEYS if key in simplebake},
        "objects_list": collection_items(simplebake, "objects_list"),
        "presets_list": collection_items(simplebake, "presets_list"),
        "all_property_names": sorted(simplebake.keys()),
    }

for image in bpy.data.images:
    if image.source in {"GENERATED", "VIEWER"} or image.packed_file:
        absolute = ""
        exists = True
    else:
        absolute = str(Path(bpy.path.abspath(image.filepath)).resolve()) if image.filepath else ""
        exists = bool(absolute) and Path(absolute).exists()
    report["images"].append(
        {
            "name": image.name,
            "size": list(image.size),
            "source": image.source,
            "filepath": image.filepath,
            "absolute": absolute,
            "exists_or_packed": exists,
            "packed": image.packed_file is not None,
            "colorspace": image.colorspace_settings.name,
        }
    )

for material in bpy.data.materials:
    if not material.use_nodes or material.node_tree is None:
        report["materials"]["without_nodes"].append(material.name)
        continue
    outputs = [node for node in material.node_tree.nodes if node.type == "OUTPUT_MATERIAL"]
    if not any(output.inputs["Surface"].is_linked for output in outputs):
        report["materials"]["without_surface_output_link"].append(material.name)
    for node in material.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image is None:
            report["materials"]["image_nodes_without_image"].append(
                {"material": material.name, "node": node.name}
            )

print("SIMPLEBAKE_AUDIT_JSON_BEGIN")
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
print("SIMPLEBAKE_AUDIT_JSON_END")
