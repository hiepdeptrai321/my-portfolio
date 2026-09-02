"""Audit source materials and baked UV data for the Fourth room atlas.

Run this script with ``For Export.blend`` open. It only reads the original
``Before Baking.blend`` library and writes a JSON report; no .blend is saved.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import bpy


EXPORT_BLEND = Path(bpy.data.filepath).resolve()
SOURCE_BLEND = EXPORT_BLEND.parent / "Before Baking.blend"
NIGHT_BLEND = EXPORT_BLEND.parent / "For Night Time Baking.blend"
OUTPUT_PATH = (
    EXPORT_BLEND.parent.parent
    / "artifacts"
    / "grounded-pastel-no-rebake"
    / "fourth-atlas-source-audit.json"
)
BAKED_COLLECTION = "SimpleBake_Bakes"
BAKED_MATERIAL = "FinalFourth_Baked"


def source_name(name: str) -> str:
    return name.removesuffix("_Baked") if name.endswith("_Baked") else name


def material_details(material: bpy.types.Material | None) -> dict[str, object]:
    if material is None:
        return {"name": None}

    details: dict[str, object] = {
        "name": material.name,
        "diffuse_color": [round(float(value), 6) for value in material.diffuse_color],
    }
    if material.use_nodes and material.node_tree:
        principled = next(
            (
                node
                for node in material.node_tree.nodes
                if node.type == "BSDF_PRINCIPLED"
            ),
            None,
        )
        if principled:
            base_color = principled.inputs.get("Base Color")
            if base_color is not None:
                details["base_color"] = [
                    round(float(value), 6) for value in base_color.default_value
                ]
                details["base_color_linked"] = bool(base_color.is_linked)
    return details


def uv_layer_details(mesh: bpy.types.Mesh) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for layer in mesh.uv_layers:
        nondegenerate_by_material: Counter[int] = Counter()
        coordinates: list[tuple[float, float]] = []
        for polygon in mesh.polygons:
            polygon_uvs = [
                tuple(layer.data[loop_index].uv)
                for loop_index in polygon.loop_indices
            ]
            coordinates.extend(polygon_uvs)
            if len(set(polygon_uvs)) >= 3:
                nondegenerate_by_material[polygon.material_index] += 1
        summaries.append(
            {
                "name": layer.name,
                "nondegenerate_polygon_count": int(sum(nondegenerate_by_material.values())),
                "nondegenerate_by_material_index": {
                    str(index): int(count)
                    for index, count in sorted(nondegenerate_by_material.items())
                },
                "bounds": (
                    [
                        round(min(uv[0] for uv in coordinates), 9),
                        round(min(uv[1] for uv in coordinates), 9),
                        round(max(uv[0] for uv in coordinates), 9),
                        round(max(uv[1] for uv in coordinates), 9),
                    ]
                    if coordinates
                    else None
                ),
            }
        )
    return summaries


baked_collection = bpy.data.collections[BAKED_COLLECTION]
baked_objects = sorted(
    [
        obj
        for obj in baked_collection.objects
        if obj.type == "MESH"
        and any(
            material and material.name == BAKED_MATERIAL
            for material in obj.data.materials
        )
    ],
    key=lambda obj: obj.name,
)

source_names = [source_name(obj.name) for obj in baked_objects]
with bpy.data.libraries.load(str(SOURCE_BLEND), link=False) as (data_from, data_to):
    available_names = set(data_from.objects)
    data_to.objects = [name for name in source_names if name in available_names]

loaded_source_objects = {
    requested_name: loaded_object
    for requested_name, loaded_object in zip(
        [name for name in source_names if name in available_names], data_to.objects
    )
    if loaded_object is not None
}

missing_day_names = [name for name in source_names if name not in loaded_source_objects]
with bpy.data.libraries.load(str(NIGHT_BLEND), link=False) as (data_from, data_to):
    available_night_names = set(data_from.objects)
    requested_night_name_strings = [
        name for name in missing_day_names if name in available_night_names
    ]
    data_to.objects = list(requested_night_name_strings)

loaded_night_objects = {
    requested_name: loaded_object
    for requested_name, loaded_object in zip(
        requested_night_name_strings, data_to.objects
    )
    if loaded_object is not None
}

rows: list[dict[str, object]] = []
for baked_object in baked_objects:
    requested_name = source_name(baked_object.name)
    source_object = loaded_source_objects.get(requested_name) or loaded_night_objects.get(
        requested_name
    )
    baked_uv_layer = baked_object.data.uv_layers.active

    row: dict[str, object] = {
        "source_name": requested_name,
        "baked_name": baked_object.name,
        "baked_polygon_count": len(baked_object.data.polygons),
        "baked_uv_layers": [layer.name for layer in baked_object.data.uv_layers],
        "baked_active_uv": baked_uv_layer.name if baked_uv_layer else None,
        "baked_uv_details": uv_layer_details(baked_object.data),
    }

    if source_object is None:
        row["source_missing"] = True
        rows.append(row)
        continue

    material_counts = Counter(
        polygon.material_index for polygon in source_object.data.polygons
    )
    row.update(
        {
            "source_missing": False,
            "source_origin": (
                "Before Baking.blend"
                if requested_name in loaded_source_objects
                else "For Night Time Baking.blend"
            ),
            "source_polygon_count": len(source_object.data.polygons),
            "source_dimensions": [
                round(float(value), 6) for value in source_object.dimensions
            ],
            "source_location": [
                round(float(value), 6) for value in source_object.location
            ],
            "source_parent": source_object.parent.name if source_object.parent else None,
            "source_modifiers": [
                {
                    "name": modifier.name,
                    "type": modifier.type,
                    "show_viewport": bool(modifier.show_viewport),
                    "show_render": bool(modifier.show_render),
                }
                for modifier in source_object.modifiers
            ],
            "source_uv_layers": [layer.name for layer in source_object.data.uv_layers],
            "source_uv_details": uv_layer_details(source_object.data),
            "source_active_uv": (
                source_object.data.uv_layers.active.name
                if source_object.data.uv_layers.active
                else None
            ),
            "materials": [
                {
                    **material_details(material),
                    "slot_index": slot_index,
                    "polygon_count": int(material_counts.get(slot_index, 0)),
                }
                for slot_index, material in enumerate(source_object.data.materials)
            ],
        }
    )
    rows.append(row)

report = {
    "export_blend": str(EXPORT_BLEND),
    "source_blend": str(SOURCE_BLEND),
    "night_fallback_blend": str(NIGHT_BLEND),
    "atlas": "Fourth",
    "baked_material": BAKED_MATERIAL,
    "object_count": len(rows),
    "source_missing": sorted(
        row["source_name"] for row in rows if row.get("source_missing")
    ),
    "source_missing_in_day_resolved_from_night": sorted(loaded_night_objects),
    "objects": rows,
}

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print("FOURTH_AUDIT_WRITTEN", OUTPUT_PATH)
print("FOURTH_AUDIT_OBJECTS", len(rows))
print("FOURTH_AUDIT_SOURCE_MISSING", report["source_missing"])
