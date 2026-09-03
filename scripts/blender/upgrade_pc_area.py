"""Upgrade only the PC area in the final Blender scene.

Run without ``--commit`` to render/export an in-memory preview. Run with
``--commit`` to save the verified result into My Room - FINAL.blend and export
the complete web replacement/details model to public/models/pc-upgrade.glb.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


COMMIT = "--commit" in sys.argv
root = Path.cwd().resolve()
artifact_dir = root / "artifacts/pc-upgrade"
artifact_dir.mkdir(parents=True, exist_ok=True)
report_path = artifact_dir / "pc-upgrade-report.json"
export_path = (
    root / "public/models/pc-upgrade.glb"
    if COMMIT
    else artifact_dir / "pc-upgrade-preview.glb"
)

PALETTE = {
    "warm_off_white": "#DDD8D4",
    "soft_light_gray": "#C9C8C6",
    "mauve_gray": "#8F8193",
    "muted_plum": "#74617F",
    "mauve": "#A582A4",
    "soft_lavender": "#BBA8CC",
    "fan_lilac": "#CBB3DB",
    "lavender_glow": "#D8B5EE",
    "glass": "#D9CBE5",
}


def srgb_channel_to_linear(value):
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def hex_to_linear_rgba(hex_color, alpha=1.0):
    normalized = hex_color.lstrip("#")
    channels = [int(normalized[index:index + 2], 16) / 255.0 for index in (0, 2, 4)]
    return tuple(srgb_channel_to_linear(value) for value in channels) + (alpha,)


def make_principled_material(name, hex_color, roughness=0.6, metallic=0.0, emission=0.08):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    color = hex_to_linear_rgba(hex_color)
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if shader.inputs.get("IOR"):
        shader.inputs["IOR"].default_value = 1.46
    if shader.inputs.get("Coat Weight"):
        shader.inputs["Coat Weight"].default_value = 0.08
    if shader.inputs.get("Coat Roughness"):
        shader.inputs["Coat Roughness"].default_value = 0.35
    if shader.inputs.get("Emission Color"):
        shader.inputs["Emission Color"].default_value = color
        shader.inputs["Emission Strength"].default_value = emission
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = color
    return material


def make_emission_material(name, hex_color, strength=2.0, alpha=1.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = hex_to_linear_rgba(hex_color, alpha)
    emission.inputs["Strength"].default_value = strength
    material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    material.diffuse_color = hex_to_linear_rgba(hex_color, alpha)
    return material


def make_glass_material():
    name = "PC_Glass_Cool_Tint"
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = hex_to_linear_rgba(PALETTE["glass"], 0.1)
    shader.inputs["Roughness"].default_value = 0.12
    shader.inputs["IOR"].default_value = 1.45
    if shader.inputs.get("Transmission Weight"):
        shader.inputs["Transmission Weight"].default_value = 0.65
    shader.inputs["Alpha"].default_value = 0.1
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = hex_to_linear_rgba(PALETTE["glass"], 0.1)
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    return material


materials = {
    "warm_off_white": make_principled_material("PC_Case_Warm_Off_White", PALETTE["warm_off_white"], 0.36, emission=0.42),
    "soft_light_gray": make_principled_material("PC_Case_Soft_Light_Gray", PALETTE["soft_light_gray"], 0.42, emission=0.35),
    "mauve_gray": make_principled_material("PC_Interior_Mauve_Gray", PALETTE["mauve_gray"], 0.72, emission=0.28),
    "muted_plum": make_principled_material("PC_GPU_Muted_Plum", PALETTE["muted_plum"], 0.68, emission=0.4),
    "mauve": make_principled_material("PC_Motherboard_Mauve", PALETTE["mauve"], 0.7, emission=0.48),
    "soft_lavender": make_principled_material("PC_Internal_Soft_Lavender", PALETTE["soft_lavender"], 0.65, emission=0.48),
    "fan_lilac": make_principled_material("PC_Fan_Pastel_Lilac", PALETTE["fan_lilac"], 0.58, emission=0.54),
    "led": make_emission_material("PC_LED_Lavender", PALETTE["lavender_glow"], 2.2),
    "halo": make_emission_material("PC_LED_Lavender_Halo", PALETTE["lavender_glow"], 0.7, 0.35),
    "glass": make_glass_material(),
}


def remove_previous_upgrade():
    for obj in list(bpy.data.objects):
        if obj.name.startswith("PC_Upgrade_"):
            bpy.data.objects.remove(obj, do_unlink=True)
    collection = bpy.data.collections.get("PC Upgrade")
    if collection:
        bpy.data.collections.remove(collection)


remove_previous_upgrade()
upgrade_collection = bpy.data.collections.new("PC Upgrade")
bpy.context.scene.collection.children.link(upgrade_collection)


def move_to_upgrade_collection(obj):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    upgrade_collection.objects.link(obj)


def connected_components(mesh):
    parent = list(range(len(mesh.vertices)))
    rank = [0] * len(parent)

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1

    for edge in mesh.edges:
        union(edge.vertices[0], edge.vertices[1])

    polygon_components = defaultdict(list)
    for polygon in mesh.polygons:
        polygon_components[find(polygon.vertices[0])].append(polygon.index)
    return polygon_components


pc = bpy.data.objects.get("Plane.020_Baked")
if not pc or pc.type != "MESH":
    raise RuntimeError("Plane.020_Baked was not found")

original_baked_material = bpy.data.materials.get("FinalFourth_Baked")
pc.data.materials.clear()
pc.data.materials.append(original_baked_material)
material_indices = {}
for role, material in materials.items():
    pc.data.materials.append(material)
    material_indices[role] = len(pc.data.materials) - 1

component_roles = {
    "warm_off_white": {43, 242, 444},
    "soft_light_gray": {575, 2740, 2860},
    "mauve_gray": {2758},
    "mauve": {635, 657, 957, 1275},
    "muted_plum": {1482, 1810, 1836},
    "fan_lilac": {2134, 2432},
}
role_for_component = {
    component_id: role
    for role, component_ids in component_roles.items()
    for component_id in component_ids
}
component_polygons = connected_components(pc.data)
component_assignment = {}
for component_id, polygon_indices in component_polygons.items():
    role = role_for_component.get(component_id, "soft_lavender")
    component_assignment[str(component_id)] = role
    for polygon_index in polygon_indices:
        pc.data.polygons[polygon_index].material_index = material_indices[role]


def add_rounded_box(name, location, dimensions, material, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    modifier = obj.modifiers.new("Soft rounded corners", "BEVEL")
    modifier.width = bevel
    modifier.segments = 3
    modifier.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.data.materials.append(material)
    move_to_upgrade_collection(obj)
    return obj


motherboard = add_rounded_box(
    "PC_Upgrade_Motherboard",
    (-2.57, 3.27, 4.07),
    (0.68, 0.055, 0.48),
    materials["mauve"],
    0.035,
)
add_rounded_box(
    "PC_Upgrade_CPU_Block",
    (-2.61, 3.235, 4.11),
    (0.20, 0.04, 0.18),
    materials["soft_light_gray"],
    0.028,
)
add_rounded_box(
    "PC_Upgrade_RAM_Block_1",
    (-2.38, 3.235, 4.15),
    (0.055, 0.04, 0.24),
    materials["soft_lavender"],
    0.014,
)
add_rounded_box(
    "PC_Upgrade_RAM_Block_2",
    (-2.29, 3.235, 4.15),
    (0.055, 0.04, 0.24),
    materials["fan_lilac"],
    0.014,
)
add_rounded_box(
    "PC_Upgrade_GPU_Block",
    (-2.145, 3.31, 3.67),
    (1.16, 0.12, 0.36),
    materials["muted_plum"],
    0.045,
)


def add_torus(
    name,
    location,
    major_radius,
    minor_radius,
    material,
    rotation=(math.pi / 2.0, 0.0, 0.0),
):
    bpy.ops.mesh.primitive_torus_add(
        align="WORLD",
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=40,
        minor_segments=10,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    move_to_upgrade_collection(obj)
    return obj


add_torus(
    "PC_Upgrade_Left_Fan_Ring",
    (-2.482286, 3.193, 3.670829),
    0.145,
    0.013,
    materials["soft_light_gray"],
)
add_torus(
    "PC_Upgrade_RGB_Fan_Halo",
    (-2.14389, 3.196, 3.670829),
    0.147,
    0.026,
    materials["halo"],
)
add_torus(
    "PC_Upgrade_RGB_Fan_Ring",
    (-2.14389, 3.193, 3.670829),
    0.145,
    0.013,
    materials["led"],
)
add_torus(
    "PC_Upgrade_Right_Fan_Ring",
    (-1.803861, 3.193, 3.670829),
    0.145,
    0.013,
    materials["soft_light_gray"],
)
add_torus(
    "PC_Upgrade_Top_Fan_Halo",
    (-2.76, 3.205, 4.12),
    0.132,
    0.023,
    materials["halo"],
)
add_torus(
    "PC_Upgrade_Top_Fan_Ring",
    (-2.76, 3.202, 4.12),
    0.13,
    0.012,
    materials["led"],
)
add_rounded_box(
    "PC_Upgrade_LED_Strip_Halo",
    (-2.20, 3.194, 3.34),
    (1.28, 0.025, 0.055),
    materials["halo"],
    0.024,
)
add_rounded_box(
    "PC_Upgrade_LED_Strip",
    (-2.20, 3.191, 3.34),
    (1.24, 0.018, 0.022),
    materials["led"],
    0.010,
)


def add_cable(name, points, material, thickness=0.014):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 8
    curve.bevel_depth = thickness
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    upgrade_collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj.select_set(False)
    return obj


add_cable(
    "PC_Upgrade_Cable_Hint_1",
    [(-1.91, 3.55, 4.30), (-1.74, 3.46, 4.24), (-1.60, 3.39, 4.10)],
    materials["fan_lilac"],
)
add_cable(
    "PC_Upgrade_Cable_Hint_2",
    [(-1.86, 3.56, 4.23), (-1.71, 3.47, 4.13), (-1.58, 3.40, 4.02)],
    materials["soft_lavender"],
    0.012,
)

glass = add_rounded_box(
    "PC_Upgrade_Glass_Panel",
    (-2.20, 3.174, 3.83),
    (1.43, 0.018, 1.10),
    materials["glass"],
    0.055,
)

point_light = bpy.data.objects.get("Point")
if point_light and point_light.type == "LIGHT":
    point_light.data.color = hex_to_linear_rgba(PALETTE["lavender_glow"])[0:3]
    point_light.data.energy = 42.0
    point_light.data.shadow_soft_size = 0.38


def create_web_replacement():
    replacement = pc.copy()
    replacement.data = pc.data.copy()
    replacement.name = "PC_Upgrade_Case_Replacement"
    upgrade_collection.objects.link(replacement)
    return replacement


replacement = create_web_replacement()

bpy.ops.object.select_all(action="DESELECT")
export_objects = [
    obj
    for obj in upgrade_collection.objects
    if obj.type == "MESH"
]
for obj in export_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = replacement
export_path.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=str(export_path),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_materials="EXPORT",
    export_draco_mesh_compression_enable=True,
    export_draco_mesh_compression_level=6,
)

# The duplicate exists only because the website replaces the atlas-colored PC
# with a complete clean model. The Blender file keeps Plane.020_Baked itself.
bpy.data.objects.remove(replacement, do_unlink=True)


def render_preview():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    camera_data = bpy.data.cameras.new("PC_Upgrade_Preview_Camera")
    camera = bpy.data.objects.new("PC_Upgrade_Preview_Camera", camera_data)
    scene.collection.objects.link(camera)
    target = Vector((-2.26, 3.57, 3.84))
    camera.location = target + Vector((3.2, -3.4, 1.7))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 3.3
    scene.camera = camera
    scene.render.filepath = str(artifact_dir / "pc-room-context-after.png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)


render_preview()

report = {
    "blend": bpy.data.filepath,
    "committed": COMMIT,
    "source_pc_object": pc.name,
    "source_pc_geometry": {
        "vertices": len(pc.data.vertices),
        "polygons": len(pc.data.polygons),
        "uv_layers": [layer.name for layer in pc.data.uv_layers],
    },
    "component_material_roles": component_assignment,
    "palette": PALETTE,
    "added_objects": sorted(obj.name for obj in upgrade_collection.objects),
    "export": str(export_path),
    "preview": str(artifact_dir / "pc-room-context-after.png"),
    "point_light": {
        "name": point_light.name if point_light else None,
        "energy": point_light.data.energy if point_light else None,
        "color": [round(float(value), 6) for value in point_light.data.color]
        if point_light
        else None,
    },
}
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

if COMMIT:
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)

print("PC_UPGRADE_REPORT", report_path)
print("PC_UPGRADE_EXPORT", export_path)
print("PC_UPGRADE_PREVIEW", report["preview"])
print("PC_UPGRADE_COMMITTED", COMMIT)
