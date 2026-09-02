"""Audit First/Second/Third baked membership against original source materials.

Run with ``For Export.blend`` open. The script is read-only with respect to all
Blender files and writes a JSON audit beneath the no-rebake artifact directory.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import bpy


EXPORT_BLEND = Path(bpy.data.filepath).resolve()
DAY_SOURCE_BLEND = EXPORT_BLEND.parent / "Before Baking.blend"
NIGHT_SOURCE_BLEND = EXPORT_BLEND.parent / "For Night Time Baking.blend"
OUTPUT_PATH = (
    EXPORT_BLEND.parent.parent
    / "artifacts"
    / "grounded-pastel-no-rebake"
    / "remaining-day-atlas-source-audit.json"
)
BAKED_COLLECTION = "SimpleBake_Bakes"
ATLASES = {
    "First": "FinalFirst_Baked",
    "Second": "RealFinalSecond_Baked",
    "Third": "FinalThird_Baked",
}


def source_name(name: str) -> str:
    return name.removesuffix("_Baked") if name.endswith("_Baked") else name


def load_objects(path: Path, names: list[str]) -> dict[str, bpy.types.Object]:
    with bpy.data.libraries.load(str(path), link=False) as (data_from, data_to):
        available = set(data_from.objects)
        requested = [name for name in names if name in available]
        data_to.objects = list(requested)
    return {
        requested_name: loaded_object
        for requested_name, loaded_object in zip(requested, data_to.objects)
        if loaded_object is not None
    }


def material_details(
    material: bpy.types.Material | None, polygon_count: int, slot_index: int
) -> dict[str, object]:
    if material is None:
        return {
            "name": None,
            "slot_index": slot_index,
            "polygon_count": polygon_count,
        }

    details: dict[str, object] = {
        "name": material.name,
        "slot_index": slot_index,
        "polygon_count": polygon_count,
        "diffuse_color": [round(float(value), 6) for value in material.diffuse_color],
    }
    if material.node_tree:
        principled = next(
            (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"),
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


def uv_details(mesh: bpy.types.Mesh) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for layer in mesh.uv_layers:
        coordinates: list[tuple[float, float]] = []
        nondegenerate_by_material: Counter[int] = Counter()
        for polygon in mesh.polygons:
            polygon_uvs = [
                tuple(layer.data[loop_index].uv)
                for loop_index in polygon.loop_indices
            ]
            coordinates.extend(polygon_uvs)
            if len(set(polygon_uvs)) >= 3:
                nondegenerate_by_material[polygon.material_index] += 1
        output.append(
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
    return output


baked_collection = bpy.data.collections[BAKED_COLLECTION]
atlas_baked_objects: dict[str, list[bpy.types.Object]] = {}
all_source_names: set[str] = set()
for atlas_name, baked_material_name in ATLASES.items():
    atlas_objects = sorted(
        [
            obj
            for obj in baked_collection.objects
            if obj.type == "MESH"
            and any(
                material and material.name == baked_material_name
                for material in obj.data.materials
            )
        ],
        key=lambda obj: obj.name,
    )
    atlas_baked_objects[atlas_name] = atlas_objects
    all_source_names.update(source_name(obj.name) for obj in atlas_objects)

day_objects = load_objects(DAY_SOURCE_BLEND, sorted(all_source_names))
missing_day_names = sorted(name for name in all_source_names if name not in day_objects)
night_objects = load_objects(NIGHT_SOURCE_BLEND, missing_day_names)
source_objects = {**night_objects, **day_objects}

atlas_reports: dict[str, object] = {}
for atlas_name, baked_objects in atlas_baked_objects.items():
    rows: list[dict[str, object]] = []
    for baked_object in baked_objects:
        requested_name = source_name(baked_object.name)
        source_object = source_objects.get(requested_name)
        row: dict[str, object] = {
            "source_name": requested_name,
            "baked_name": baked_object.name,
            "baked_polygon_count": len(baked_object.data.polygons),
            "baked_loop_count": len(baked_object.data.loops),
            "baked_active_uv": (
                baked_object.data.uv_layers.active.name
                if baked_object.data.uv_layers.active
                else None
            ),
            "baked_uv_details": uv_details(baked_object.data),
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
                    if requested_name in day_objects
                    else "For Night Time Baking.blend"
                ),
                "source_polygon_count": len(source_object.data.polygons),
                "source_loop_count": len(source_object.data.loops),
                "topology_matches_baked": (
                    len(source_object.data.polygons) == len(baked_object.data.polygons)
                    and len(source_object.data.loops) == len(baked_object.data.loops)
                ),
                "source_dimensions": [
                    round(float(value), 6) for value in source_object.dimensions
                ],
                "source_location": [
                    round(float(value), 6) for value in source_object.location
                ],
                "source_active_uv": (
                    source_object.data.uv_layers.active.name
                    if source_object.data.uv_layers.active
                    else None
                ),
                "source_uv_details": uv_details(source_object.data),
                "materials": [
                    material_details(
                        material,
                        int(material_counts.get(slot_index, 0)),
                        slot_index,
                    )
                    for slot_index, material in enumerate(source_object.data.materials)
                ],
            }
        )
        rows.append(row)

    atlas_reports[atlas_name] = {
        "baked_material": ATLASES[atlas_name],
        "object_count": len(rows),
        "missing": sorted(row["source_name"] for row in rows if row["source_missing"]),
        "resolved_from_night": sorted(
            row["source_name"]
            for row in rows
            if row.get("source_origin") == "For Night Time Baking.blend"
        ),
        "objects": rows,
    }

report = {
    "export_blend": str(EXPORT_BLEND),
    "day_source_blend": str(DAY_SOURCE_BLEND),
    "night_fallback_blend": str(NIGHT_SOURCE_BLEND),
    "atlases": atlas_reports,
}
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print("REMAINING_DAY_AUDIT_WRITTEN", OUTPUT_PATH)
for atlas_name, atlas in atlas_reports.items():
    print(
        "REMAINING_DAY_AUDIT",
        atlas_name,
        "objects",
        atlas["object_count"],
        "missing",
        atlas["missing"],
        "resolved_from_night",
        atlas["resolved_from_night"],
    )
