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

import bmesh
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
    "blush_white": "#EADDE3",
    "lavender_mist": "#D8C7DD",
    "mauve_gray": "#8F8193",
    "muted_plum": "#74617F",
    "mauve": "#A582A4",
    "soft_lavender": "#BBA8CC",
    "fan_lilac": "#CBB3DB",
    "lavender_glow": "#D8B5EE",
    "glass": "#D9CBE5",
    "logo_deep_mauve": "#62546D",
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
    "blush_white": make_principled_material("PC_Case_Blush_White", PALETTE["blush_white"], 0.34, emission=0.36),
    "lavender_mist": make_principled_material("PC_Case_Lavender_Trim", PALETTE["lavender_mist"], 0.4, emission=0.34),
    "mauve_gray": make_principled_material("PC_Interior_Mauve_Gray", PALETTE["mauve_gray"], 0.72, emission=0.28),
    "muted_plum": make_principled_material("PC_GPU_Muted_Plum", PALETTE["muted_plum"], 0.68, emission=0.4),
    "mauve": make_principled_material("PC_Motherboard_Mauve", PALETTE["mauve"], 0.7, emission=0.48),
    "soft_lavender": make_principled_material("PC_Internal_Soft_Lavender", PALETTE["soft_lavender"], 0.65, emission=0.48),
    "fan_lilac": make_principled_material("PC_Fan_Pastel_Lilac", PALETTE["fan_lilac"], 0.58, emission=0.54),
    "led": make_emission_material("PC_LED_Lavender", PALETTE["lavender_glow"], 2.2),
    "halo": make_emission_material("PC_LED_Lavender_Halo", PALETTE["lavender_glow"], 0.7, 0.35),
    "glass": make_glass_material(),
    "logo_deep_mauve": make_principled_material("PC_Logo_Deep_Mauve", PALETTE["logo_deep_mauve"], 0.5, emission=0.22),
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
    "blush_white": {43, 242, 444},
    "lavender_mist": {2740, 2860},
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


def is_front_logo_component(polygon_indices):
    vertex_indices = {
        vertex_index
        for polygon_index in polygon_indices
        for vertex_index in pc.data.polygons[polygon_index].vertices
    }
    coordinates = [
        pc.matrix_world @ pc.data.vertices[index].co
        for index in vertex_indices
    ]
    minimum = Vector(
        tuple(min(point[axis] for point in coordinates) for axis in range(3))
    )
    maximum = Vector(
        tuple(max(point[axis] for point in coordinates) for axis in range(3))
    )
    dimensions = maximum - minimum
    center = (minimum + maximum) * 0.5
    return (
        dimensions.x < 0.01
        and -1.31 < center.x < -1.29
        and 3.5 < center.y < 3.8
        and 4.0 < center.z < 4.3
    )


for component_id, polygon_indices in component_polygons.items():
    role = (
        "logo_deep_mauve"
        if is_front_logo_component(polygon_indices)
        else role_for_component.get(component_id, "soft_lavender")
    )
    component_assignment[str(component_id)] = role
    for polygon_index in polygon_indices:
        pc.data.polygons[polygon_index].material_index = material_indices[role]


def remove_coincident_case_faces(obj, preserved_material_index):
    mesh = obj.data
    mesh.calc_loop_triangles()
    signature_to_polygons = defaultdict(set)

    for triangle in mesh.loop_triangles:
        points = []
        for vertex_index in triangle.vertices:
            point = obj.matrix_world @ mesh.vertices[vertex_index].co
            points.append(tuple(round(float(value), 6) for value in point))
        signature_to_polygons[tuple(sorted(points))].add(triangle.polygon_index)

    polygon_indices_to_remove = set()
    for polygon_indices in signature_to_polygons.values():
        if len(polygon_indices) < 2:
            continue

        ordered = sorted(
            polygon_indices,
            key=lambda index: (
                mesh.polygons[index].material_index != preserved_material_index,
                index,
            ),
        )
        polygon_indices_to_remove.update(ordered[1:])

    if not polygon_indices_to_remove:
        return []

    editable_mesh = bmesh.new()
    editable_mesh.from_mesh(mesh)
    editable_mesh.faces.ensure_lookup_table()
    bmesh.ops.delete(
        editable_mesh,
        geom=[editable_mesh.faces[index] for index in polygon_indices_to_remove],
        context="FACES_ONLY",
    )
    editable_mesh.to_mesh(mesh)
    editable_mesh.free()
    mesh.update()
    return sorted(polygon_indices_to_remove)


removed_coincident_polygons = remove_coincident_case_faces(
    pc,
    material_indices["blush_white"],
)

for obsolete_material_name in (
    "PC_Case_Warm_Off_White",
    "PC_Case_Soft_Light_Gray",
):
    obsolete_material = bpy.data.materials.get(obsolete_material_name)
    if obsolete_material and obsolete_material.users == 0:
        bpy.data.materials.remove(obsolete_material)


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
    materials["lavender_mist"],
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
    "PC_Upgrade_Left_Fan_Halo",
    (-2.482286, 3.196, 3.670829),
    0.147,
    0.026,
    materials["halo"],
)
add_torus(
    "PC_Upgrade_Left_Fan_Ring",
    (-2.482286, 3.193, 3.670829),
    0.145,
    0.013,
    materials["led"],
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
    "PC_Upgrade_Right_Fan_Halo",
    (-1.803861, 3.196, 3.670829),
    0.147,
    0.026,
    materials["halo"],
)
add_torus(
    "PC_Upgrade_Right_Fan_Ring",
    (-1.803861, 3.193, 3.670829),
    0.145,
    0.013,
    materials["led"],
)
add_rounded_box(
    "PC_Upgrade_Top_LED_Strip_Halo",
    (-2.20, 3.194, 4.315),
    (1.28, 0.025, 0.055),
    materials["halo"],
    0.024,
)
add_rounded_box(
    "PC_Upgrade_Top_LED_Strip",
    (-2.20, 3.191, 4.315),
    (1.24, 0.018, 0.022),
    materials["led"],
    0.010,
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
    point_light.data.energy = 55.0
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
    original_camera = scene.camera or bpy.data.objects.get("Camera")
    original_render_settings = {
        "engine": scene.render.engine,
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y,
        "resolution_percentage": scene.render.resolution_percentage,
        "file_format": scene.render.image_settings.file_format,
        "film_transparent": scene.render.film_transparent,
        "filepath": scene.render.filepath,
    }
    camera_data = bpy.data.cameras.new("PC_Upgrade_Preview_Camera")
    camera = bpy.data.objects.new("PC_Upgrade_Preview_Camera", camera_data)
    try:
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x = 1000
        scene.render.resolution_y = 1000
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.film_transparent = True
        scene.collection.objects.link(camera)
        target = Vector((-2.26, 3.57, 3.84))
        camera.location = target + Vector((3.2, -3.4, 1.7))
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = 3.3
        scene.camera = camera
        scene.render.filepath = str(artifact_dir / "pc-room-context-after.png")
        bpy.ops.render.render(write_still=True)
    finally:
        scene.camera = original_camera
        scene.render.engine = original_render_settings["engine"]
        scene.render.resolution_x = original_render_settings["resolution_x"]
        scene.render.resolution_y = original_render_settings["resolution_y"]
        scene.render.resolution_percentage = original_render_settings[
            "resolution_percentage"
        ]
        scene.render.image_settings.file_format = original_render_settings[
            "file_format"
        ]
        scene.render.film_transparent = original_render_settings[
            "film_transparent"
        ]
        scene.render.filepath = original_render_settings["filepath"]
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
    "removed_coincident_polygons": removed_coincident_polygons,
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
