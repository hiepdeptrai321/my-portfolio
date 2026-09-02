"""Compare saved SimpleBake output groups with the original Day source objects."""

from __future__ import annotations

from pathlib import Path

import bpy


MATERIAL_GROUPS = (
    ("First", "FinalFirst_Baked"),
    ("Second", "RealFinalSecond_Baked"),
    ("Third", "FinalThird_Baked"),
    ("Fourth", "FinalFourth_Baked"),
)


export_blend = Path(bpy.data.filepath).resolve()
day_source = export_blend.parent / "Before Baking.blend"
grounded_source = export_blend.parent / "Before Baking - Grounded Pastel Test.blend"
night_source = export_blend.parent / "For Night Time Baking.blend"


def library_object_names(path: Path) -> set[str]:
    with bpy.data.libraries.load(str(path), link=False) as (data_from, _data_to):
        return set(data_from.objects)


day_names = library_object_names(day_source)
grounded_names = library_object_names(grounded_source)
night_names = library_object_names(night_source)
baked_collection = bpy.data.collections["SimpleBake_Bakes"]

for atlas_name, material_name in MATERIAL_GROUPS:
    baked_objects = sorted(
        [
            obj
            for obj in baked_collection.objects
            if obj.type == "MESH"
            and any(material and material.name == material_name for material in obj.data.materials)
        ],
        key=lambda obj: obj.name,
    )
    source_names = [
        obj.name.removesuffix("_Baked") if obj.name.endswith("_Baked") else obj.name
        for obj in baked_objects
    ]
    missing_day = sorted(name for name in source_names if name not in day_names)
    missing_grounded = sorted(name for name in source_names if name not in grounded_names)
    missing_night = sorted(name for name in source_names if name not in night_names)
    print(
        "ATLAS_MEMBERSHIP",
        atlas_name,
        "material",
        material_name,
        "expected",
        len(source_names),
        "day_present",
        len(source_names) - len(missing_day),
        "day_missing",
        missing_day,
        "grounded_present",
        len(source_names) - len(missing_grounded),
        "grounded_missing",
        missing_grounded,
        "night_present",
        len(source_names) - len(missing_night),
        "night_missing",
        missing_night,
    )
    print("ATLAS_SOURCE_NAMES", atlas_name, source_names)
