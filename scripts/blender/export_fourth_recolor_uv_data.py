"""Export UV polygons for the approved Fourth Day no-rebake recolor groups.

The baked mesh in ``For Export.blend`` is the canonical atlas-membership and
UV source. Original source material indices are used only to split semantic
parts that share one mesh. When a source mesh topology differs from its baked
copy, the source's saved ``SimpleBake`` UV layer is used explicitly.

This script never saves a .blend file and never invokes a bake operator.
"""

from __future__ import annotations

import json
from pathlib import Path

import bpy


EXPORT_BLEND = Path(bpy.data.filepath).resolve()
DAY_SOURCE_BLEND = EXPORT_BLEND.parent / "Before Baking.blend"
NIGHT_SOURCE_BLEND = EXPORT_BLEND.parent / "For Night Time Baking.blend"
OUTPUT_PATH = (
    EXPORT_BLEND.parent.parent
    / "artifacts"
    / "grounded-pastel-no-rebake"
    / "fourth-recolor-uv-polygons.json"
)
BAKED_COLLECTION = "SimpleBake_Bakes"
BAKED_MATERIAL = "FinalFourth_Baked"


GROUPS = {
    "drawer": {
        "target_family": "Sage Green",
        "target_hex": "#718E7A",
        "strength": 0.90,
        "selections": [{"object": "Plane.030", "materials": ["Drawer"]}],
    },
    "drawer-shelves": {
        "target_family": "Warm Cream",
        "target_hex": "#F1E9DE",
        "strength": 0.92,
        "selections": [
            {"object": "Plane.031", "materials": ["Drawer Shelves.001"]}
        ],
    },
    "computer": {
        "target_family": "Dusty Blue",
        "target_hex": "#8FA9B8",
        "strength": 0.90,
        "selections": [
            {"object": "Computer", "materials": ["Computer.001"]},
            {
                "object": "Plane.020",
                "materials": [
                    "Computer.001",
                    "Glass.001",
                    "Exhaust.001",
                    "Base Purple.001",
                ],
                "whole_baked_object": True,
            },
        ],
    },
    "chair-body": {
        "target_family": "Warm Cream",
        "target_hex": "#F1E9DE",
        "strength": 0.90,
        "selections": [
            {"object": "Chair Top", "materials": ["Base Gray.001"]},
            {"object": "Chair Legs", "materials": ["Base Gray.001"]},
        ],
    },
    "chair-cushion": {
        "target_family": "Soft Terracotta",
        "target_hex": "#D99478",
        "strength": 0.90,
        "selections": [
            {"object": "Chair Top", "materials": ["Chair Cushion"]}
        ],
    },
    "desk-pad": {
        "target_family": "Soft Terracotta",
        "target_hex": "#D99478",
        "strength": 0.88,
        "selections": [{"object": "Cube.002", "materials": ["Desk Pad"]}],
    },
    "keyboard-body": {
        "target_family": "Warm Cream",
        "target_hex": "#F1E9DE",
        "strength": 0.92,
        "selections": [{"object": "Cube.003", "materials": ["Keyboard"]}],
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
        [round(float(uv_layer.data[loop_index].uv.x), 9),
         round(float(uv_layer.data[loop_index].uv.y), 9)]
        for loop_index in polygon.loop_indices
    ]


baked_collection = bpy.data.collections[BAKED_COLLECTION]
baked_objects = {
    unbaked_name(obj.name): obj
    for obj in baked_collection.objects
    if obj.type == "MESH"
    and any(
        material and material.name == BAKED_MATERIAL
        for material in obj.data.materials
    )
}

required_names = sorted(
    {
        selection["object"]
        for group in GROUPS.values()
        for selection in group["selections"]
    }
)
day_objects = load_objects(DAY_SOURCE_BLEND, required_names)
missing_day_names = [name for name in required_names if name not in day_objects]
night_objects = load_objects(NIGHT_SOURCE_BLEND, missing_day_names)
source_objects = {**night_objects, **day_objects}

missing_baked = sorted(name for name in required_names if name not in baked_objects)
missing_source = sorted(name for name in required_names if name not in source_objects)
if missing_baked or missing_source:
    raise RuntimeError(
        f"Cannot export masks; missing baked={missing_baked}, source={missing_source}"
    )

output_groups: dict[str, object] = {}
for group_name, group_definition in GROUPS.items():
    group_polygons: list[list[list[float]]] = []
    selection_reports: list[dict[str, object]] = []

    for selection in group_definition["selections"]:
        object_name = selection["object"]
        selected_materials = set(selection["materials"])
        source_object = source_objects[object_name]
        baked_object = baked_objects[object_name]
        source_mesh = source_object.data
        baked_mesh = baked_object.data

        material_indices = {
            index
            for index, material in enumerate(source_mesh.materials)
            if material and material.name in selected_materials
        }
        found_materials = {
            material.name
            for index, material in enumerate(source_mesh.materials)
            if material and index in material_indices
        }
        if found_materials != selected_materials:
            raise RuntimeError(
                f"{object_name}: expected materials {sorted(selected_materials)}, "
                f"found {sorted(found_materials)}"
            )

        topology_matches = (
            len(source_mesh.polygons) == len(baked_mesh.polygons)
            and len(source_mesh.loops) == len(baked_mesh.loops)
        )
        requested_source_layer = selection.get("source_uv_layer")
        whole_baked_object = bool(selection.get("whole_baked_object"))

        if whole_baked_object:
            uv_source = "baked-object:whole-object"
            uv_layer = baked_mesh.uv_layers.active
            polygons = [
                polygon_uvs(baked_mesh, baked_polygon, uv_layer)
                for baked_polygon in baked_mesh.polygons
            ]
        elif topology_matches and not requested_source_layer:
            uv_source = "baked-object"
            uv_layer = baked_mesh.uv_layers.active
            source_polygons = [
                (source_polygon, baked_mesh.polygons[source_polygon.index])
                for source_polygon in source_mesh.polygons
                if source_polygon.material_index in material_indices
            ]
            polygons = [
                polygon_uvs(baked_mesh, baked_polygon, uv_layer)
                for _source_polygon, baked_polygon in source_polygons
            ]
        else:
            layer_name = requested_source_layer or "SimpleBake"
            uv_layer = source_mesh.uv_layers.get(layer_name)
            if uv_layer is None:
                raise RuntimeError(
                    f"{object_name}: topology differs and UV layer {layer_name!r} is absent"
                )
            uv_source = f"source-object:{layer_name}"
            selected_source_polygons = [
                polygon
                for polygon in source_mesh.polygons
                if polygon.material_index in material_indices
            ]
            polygons = [
                polygon_uvs(source_mesh, polygon, uv_layer)
                for polygon in selected_source_polygons
            ]

        nondegenerate_polygons = [
            polygon for polygon in polygons if len({tuple(uv) for uv in polygon}) >= 3
        ]
        group_polygons.extend(nondegenerate_polygons)
        selection_reports.append(
            {
                "object": object_name,
                "materials": sorted(selected_materials),
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
                "selected_polygon_count": len(nondegenerate_polygons),
            }
        )

    output_groups[group_name] = {
        "target_family": group_definition["target_family"],
        "target_hex": group_definition["target_hex"],
        "strength": group_definition["strength"],
        "selections": selection_reports,
        "polygons": group_polygons,
    }

report = {
    "export_blend": str(EXPORT_BLEND),
    "day_source_blend": str(DAY_SOURCE_BLEND),
    "night_source_blend": str(NIGHT_SOURCE_BLEND),
    "atlas": "Fourth Day",
    "canonical_baked_material": BAKED_MATERIAL,
    "groups": output_groups,
}

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("FOURTH_UV_DATA_WRITTEN", OUTPUT_PATH)
for group_name, group in output_groups.items():
    print("FOURTH_UV_GROUP", group_name, len(group["polygons"]))
