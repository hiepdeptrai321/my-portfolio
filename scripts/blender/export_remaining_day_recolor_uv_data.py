"""Export canonical baked UV polygons for First/Second/Third Day recoloring.

This script uses the source materials only to identify semantic sub-parts. UVs
always come from the baked objects in ``For Export.blend``. It never saves or
modifies a Blender file and never invokes a bake operator.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict, deque
from pathlib import Path

import bpy


EXPORT_BLEND = Path(bpy.data.filepath).resolve()
DAY_SOURCE_BLEND = EXPORT_BLEND.parent / "Before Baking.blend"
NIGHT_SOURCE_BLEND = EXPORT_BLEND.parent / "For Night Time Baking.blend"
OUTPUT_PATH = (
    EXPORT_BLEND.parent.parent
    / "artifacts"
    / "grounded-pastel-no-rebake"
    / "remaining-day-recolor-uv-polygons.json"
)
BAKED_COLLECTION = "SimpleBake_Bakes"


ATLASES = {
    "first": {
        "label": "First Day",
        "baked_material": "FinalFirst_Baked",
        "groups": {
            "room-shell": {
                "target_family": "Warm Cream",
                "target_hex": "#F1E9DE",
                "strength": 0.90,
                "selections": [
                    {
                        "object": "Cube",
                        "materials": ["Room"],
                        "whole_baked_object": True,
                        "exclude_materials_by_geometry": ["Wood", "Outlet"],
                    }
                ],
            },
            "stone-structure": {
                "target_family": "Mist Gray",
                "target_hex": "#DCE2DE",
                "strength": 0.86,
                "selections": [
                    {
                        "object": "Cube.039",
                        "materials": ["Stone wall"],
                        "whole_baked_object": True,
                    }
                ],
            },
            "neutral-structure": {
                "target_family": "Mist Gray",
                "target_hex": "#DCE2DE",
                "strength": 0.88,
                "selections": [
                    {
                        "object": "Plane.001",
                        "materials": ["Base Gray.001"],
                        "whole_baked_object": True,
                    }
                ],
            },
            "cream-structure": {
                "target_family": "Warm Cream",
                "target_hex": "#F1E9DE",
                "strength": 0.88,
                "selections": [
                    {"object": "Cube.020", "materials": ["Base White.001"]}
                ],
            },
        },
    },
    "second": {
        "label": "Second Day",
        "baked_material": "RealFinalSecond_Baked",
        "groups": {
            "backdrop": {
                "target_family": "Mist Gray",
                "target_hex": "#DCE2DE",
                "strength": 0.88,
                "selections": [
                    {
                        "object": "Backdrop",
                        "materials": ["Backdrop.001"],
                        "whole_baked_object": True,
                    }
                ],
            },
            "poster-frame": {
                "target_family": "Deep Sage",
                "target_hex": "#405D52",
                "strength": 0.84,
                "selections": [
                    {"object": "Plane.122", "materials": ["Poster Frame"]}
                ],
            },
        },
    },
    "third": {
        "label": "Third Day",
        "baked_material": "FinalThird_Baked",
        "groups": {
            "piano-body": {
                "target_family": "Dusty Blue",
                "target_hex": "#8FA9B8",
                "strength": 0.90,
                "selections": [
                    {
                        "object": "Piano",
                        "materials": [
                            "Base Gray.001",
                            "Piano.001",
                            "Base Purple.001",
                        ],
                        "match_materials_by_geometry": True,
                    }
                ],
            },
            "welcome-mat": {
                "target_family": "Sage Green",
                "target_hex": "#718E7A",
                "strength": 0.88,
                "selections": [
                    {
                        "object": "Plane.019",
                        "materials": ["Welcome Mat.001", "Drawer Shelves.001"],
                        "whole_baked_object": True,
                    }
                ],
            },
        },
    },
}


def unbaked_name(name: str) -> str:
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


def polygon_uvs(
    mesh: bpy.types.Mesh,
    polygon: bpy.types.MeshPolygon,
    uv_layer: bpy.types.MeshUVLoopLayer,
) -> list[list[float]]:
    return [
        [
            round(float(uv_layer.data[loop_index].uv.x), 9),
            round(float(uv_layer.data[loop_index].uv.y), 9),
        ]
        for loop_index in polygon.loop_indices
    ]


def polygon_geometry_key(
    mesh: bpy.types.Mesh, polygon: bpy.types.MeshPolygon, precision: int = 5
) -> tuple[tuple[float, float, float], ...]:
    return tuple(
        sorted(
            (
                round(float(mesh.vertices[index].co.x), precision),
                round(float(mesh.vertices[index].co.y), precision),
                round(float(mesh.vertices[index].co.z), precision),
            )
            for index in polygon.vertices
        )
    )


def materials_by_geometry(
    source_mesh: bpy.types.Mesh, baked_mesh: bpy.types.Mesh
) -> tuple[dict[int, int], dict[str, int]]:
    source_candidates: dict[
        tuple[tuple[float, float, float], ...], deque[int]
    ] = defaultdict(deque)
    for source_polygon in source_mesh.polygons:
        source_candidates[polygon_geometry_key(source_mesh, source_polygon)].append(
            source_polygon.material_index
        )

    mapping: dict[int, int] = {}
    missing = 0
    for baked_polygon in baked_mesh.polygons:
        candidates = source_candidates.get(
            polygon_geometry_key(baked_mesh, baked_polygon)
        )
        if not candidates:
            missing += 1
            continue
        mapping[baked_polygon.index] = candidates.popleft()

    remaining_source = sum(len(candidates) for candidates in source_candidates.values())
    mapped_by_material = Counter(mapping.values())
    unmatched_source_by_material: Counter[int] = Counter()
    for candidates in source_candidates.values():
        unmatched_source_by_material.update(candidates)
    report = {
        "baked_polygon_count": len(baked_mesh.polygons),
        "mapped_baked_polygon_count": len(mapping),
        "missing_baked_polygon_count": missing,
        "unmatched_source_polygon_count": remaining_source,
        "mapped_by_material_index": {
            str(index): int(count) for index, count in sorted(mapped_by_material.items())
        },
        "unmatched_source_by_material_index": {
            str(index): int(count)
            for index, count in sorted(unmatched_source_by_material.items())
        },
    }
    return mapping, report


baked_collection = bpy.data.collections[BAKED_COLLECTION]
baked_objects_by_atlas: dict[str, dict[str, bpy.types.Object]] = {}
for atlas_key, atlas_definition in ATLASES.items():
    baked_material = atlas_definition["baked_material"]
    baked_objects_by_atlas[atlas_key] = {
        unbaked_name(obj.name): obj
        for obj in baked_collection.objects
        if obj.type == "MESH"
        and any(
            material and material.name == baked_material
            for material in obj.data.materials
        )
    }

required_names = sorted(
    {
        selection["object"]
        for atlas in ATLASES.values()
        for group in atlas["groups"].values()
        for selection in group["selections"]
    }
)
day_objects = load_objects(DAY_SOURCE_BLEND, required_names)
night_objects = load_objects(
    NIGHT_SOURCE_BLEND,
    [name for name in required_names if name not in day_objects],
)
source_objects = {**night_objects, **day_objects}

output_atlases: dict[str, object] = {}
for atlas_key, atlas_definition in ATLASES.items():
    baked_objects = baked_objects_by_atlas[atlas_key]
    output_groups: dict[str, object] = {}
    for group_name, group_definition in atlas_definition["groups"].items():
        group_polygons: list[list[list[float]]] = []
        selection_reports: list[dict[str, object]] = []

        for selection in group_definition["selections"]:
            object_name = selection["object"]
            source_object = source_objects.get(object_name)
            baked_object = baked_objects.get(object_name)
            if source_object is None or baked_object is None:
                raise RuntimeError(
                    f"{atlas_key}/{group_name}: missing source or baked object {object_name}"
                )

            source_mesh = source_object.data
            baked_mesh = baked_object.data
            uv_layer = baked_mesh.uv_layers.active
            if uv_layer is None:
                raise RuntimeError(f"{object_name}: baked object has no active UV layer")

            whole_baked_object = bool(selection.get("whole_baked_object"))
            selected_material_names = set(selection["materials"])
            selected_material_indices = {
                index
                for index, material in enumerate(source_mesh.materials)
                if material and material.name in selected_material_names
            }
            found_material_names = {
                material.name
                for index, material in enumerate(source_mesh.materials)
                if material and index in selected_material_indices
            }
            if found_material_names != selected_material_names and not whole_baked_object:
                raise RuntimeError(
                    f"{object_name}: expected {sorted(selected_material_names)}, "
                    f"found {sorted(found_material_names)}"
                )

            topology_matches = (
                len(source_mesh.polygons) == len(baked_mesh.polygons)
                and len(source_mesh.loops) == len(baked_mesh.loops)
            )
            geometry_matching = bool(selection.get("match_materials_by_geometry"))
            excluded_material_names = set(
                selection.get("exclude_materials_by_geometry", [])
            )
            geometry_report = None

            if whole_baked_object and excluded_material_names:
                excluded_material_indices = {
                    index
                    for index, material in enumerate(source_mesh.materials)
                    if material and material.name in excluded_material_names
                }
                found_excluded_material_names = {
                    material.name
                    for index, material in enumerate(source_mesh.materials)
                    if material and index in excluded_material_indices
                }
                if found_excluded_material_names != excluded_material_names:
                    raise RuntimeError(
                        f"{object_name}: expected exclusions "
                        f"{sorted(excluded_material_names)}, found "
                        f"{sorted(found_excluded_material_names)}"
                    )
                material_mapping, geometry_report = materials_by_geometry(
                    source_mesh, baked_mesh
                )
                selected_baked_polygons = [
                    polygon
                    for polygon in baked_mesh.polygons
                    if material_mapping.get(polygon.index)
                    not in excluded_material_indices
                ]
                uv_source = "baked-object:whole-minus-geometry-matched-exclusions"
            elif whole_baked_object:
                selected_baked_polygons = list(baked_mesh.polygons)
                uv_source = "baked-object:whole-object"
            elif topology_matches:
                selected_baked_polygons = [
                    baked_mesh.polygons[source_polygon.index]
                    for source_polygon in source_mesh.polygons
                    if source_polygon.material_index in selected_material_indices
                ]
                uv_source = "baked-object:source-polygon-index"
            elif geometry_matching:
                material_mapping, geometry_report = materials_by_geometry(
                    source_mesh, baked_mesh
                )
                expected_selected_count = sum(
                    1
                    for polygon in source_mesh.polygons
                    if polygon.material_index in selected_material_indices
                )
                mapped_selected_count = sum(
                    1
                    for material_index in material_mapping.values()
                    if material_index in selected_material_indices
                )
                geometry_report["expected_selected_polygon_count"] = (
                    expected_selected_count
                )
                geometry_report["mapped_selected_polygon_count"] = mapped_selected_count
                if mapped_selected_count < int(expected_selected_count * 0.995):
                    raise RuntimeError(
                        f"{object_name}: geometry mapping is not reliable: {geometry_report}"
                    )
                selected_baked_polygons = [
                    polygon
                    for polygon in baked_mesh.polygons
                    if material_mapping.get(polygon.index) in selected_material_indices
                ]
                uv_source = "baked-object:geometry-matched-source-material"
            else:
                raise RuntimeError(
                    f"{object_name}: topology differs; select whole_baked_object or "
                    "match_materials_by_geometry explicitly"
                )

            polygons = [
                polygon_uvs(baked_mesh, polygon, uv_layer)
                for polygon in selected_baked_polygons
            ]
            nondegenerate_polygons = [
                polygon
                for polygon in polygons
                if len({tuple(uv) for uv in polygon}) >= 3
            ]
            group_polygons.extend(nondegenerate_polygons)
            selection_reports.append(
                {
                    "object": object_name,
                    "materials": sorted(selected_material_names),
                    "source_origin": (
                        "Before Baking.blend"
                        if object_name in day_objects
                        else "For Night Time Baking.blend"
                    ),
                    "source_polygon_count": len(source_mesh.polygons),
                    "baked_polygon_count": len(baked_mesh.polygons),
                    "topology_matches": topology_matches,
                    "uv_source": uv_source,
                    "whole_baked_object": whole_baked_object,
                    "excluded_materials": sorted(excluded_material_names),
                    "selected_polygon_count": len(nondegenerate_polygons),
                    "geometry_mapping": geometry_report,
                }
            )

        output_groups[group_name] = {
            "target_family": group_definition["target_family"],
            "target_hex": group_definition["target_hex"],
            "strength": group_definition["strength"],
            "selections": selection_reports,
            "polygons": group_polygons,
        }

    output_atlases[atlas_key] = {
        "label": atlas_definition["label"],
        "baked_material": atlas_definition["baked_material"],
        "groups": output_groups,
    }

report = {
    "export_blend": str(EXPORT_BLEND),
    "day_source_blend": str(DAY_SOURCE_BLEND),
    "night_fallback_blend": str(NIGHT_SOURCE_BLEND),
    "atlases": output_atlases,
}
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("REMAINING_DAY_UV_DATA_WRITTEN", OUTPUT_PATH)
for atlas_key, atlas in output_atlases.items():
    for group_name, group in atlas["groups"].items():
        print(
            "REMAINING_DAY_UV_GROUP",
            atlas_key,
            group_name,
            len(group["polygons"]),
        )
