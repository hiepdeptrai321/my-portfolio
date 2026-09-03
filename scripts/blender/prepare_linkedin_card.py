"""Name the user's LinkedIn card and export it as a standalone web model."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy


SOURCE_NAME = "Objeto_1_Tinta (1)_0"
FINAL_NAME = "LinkedIn_Fourth_Raycaster_Pointer_Hover"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


blend = Path(bpy.data.filepath).resolve()
root = blend.parent.parent
output_glb = root / "public/models/linkedin-card.glb"
report_path = root / "artifacts/final-room-audit/linkedin-card-export.json"

linkedin = bpy.data.objects.get(FINAL_NAME) or bpy.data.objects.get(SOURCE_NAME)
if linkedin is None or linkedin.type != "MESH":
    raise RuntimeError("Could not find the visible LinkedIn card mesh")

expected_world_location = (-2.543337, 3.958757, 5.613009)
world_location = linkedin.matrix_world.translation
if any(
    abs(float(world_location[index]) - expected_world_location[index]) > 1e-4
    for index in range(3)
):
    raise RuntimeError(
        f"LinkedIn card transform is unexpected: {tuple(world_location)}"
    )

material_names = [
    slot.material.name if slot.material else None for slot in linkedin.material_slots
]
if material_names != ["Tinta_1.002", "Tinta_3.001", "Tinta_3.002"]:
    raise RuntimeError(f"Unexpected LinkedIn materials: {material_names}")

if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

# Detach the final card from the imported Sketchfab empty hierarchy while
# preserving its exact world transform. This produces one clean GLB mesh and
# makes later exports from the authoritative blend predictable.
world_matrix = linkedin.matrix_world.copy()
linkedin.parent = None
linkedin.matrix_world = world_matrix
linkedin.name = FINAL_NAME
linkedin.data.name = f"{FINAL_NAME}_Mesh"

removed_stray_meshes = []
for stray_name in ("Objeto_2_Tinta (3)_0", "Objeto_3_Tinta (3)_0"):
    stray = bpy.data.objects.get(stray_name)
    if stray is not None:
        removed_stray_meshes.append(stray.name)
        bpy.data.objects.remove(stray, do_unlink=True)

# Before the LinkedIn import, RootNode was the only Empty in the clean final
# scene and remains the parent of Tree_3. All other Empty objects are unused
# import wrappers after the visible LinkedIn mesh has been detached.
removed_import_empties = []
for obj in list(bpy.data.objects):
    if obj.type == "EMPTY" and obj.name != "RootNode":
        removed_import_empties.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)

bpy.ops.object.select_all(action="DESELECT")
linkedin.select_set(True)
bpy.context.view_layer.objects.active = linkedin

# Save the authoritative Blender file with the stable semantic object name.
bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)

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
)

report = {
    "blend": str(blend),
    "blend_sha256": sha256(blend),
    "object": linkedin.name,
    "mesh": linkedin.data.name,
    "world_location": [round(float(value), 6) for value in linkedin.matrix_world.translation],
    "dimensions": [round(float(value), 6) for value in linkedin.dimensions],
    "materials": material_names,
    "removed_stray_meshes": sorted(removed_stray_meshes),
    "removed_import_empties": len(removed_import_empties),
    "output_glb": str(output_glb),
    "output_size_bytes": output_glb.stat().st_size,
    "output_sha256": sha256(output_glb),
}
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("LINKEDIN_OBJECT", report["object"])
print("LINKEDIN_WORLD_LOCATION", report["world_location"])
print("LINKEDIN_MATERIALS", report["materials"])
print("REMOVED_STRAY_MESHES", report["removed_stray_meshes"])
print("REMOVED_IMPORT_EMPTIES", report["removed_import_empties"])
print("LINKEDIN_GLB", output_glb)
print("LINKEDIN_GLB_SIZE", report["output_size_bytes"])
print("LINKEDIN_GLB_SHA256", report["output_sha256"])
