import hashlib
import struct

import bpy


PALETTE = {
    "deep_sage": "#405D52",
    "sage": "#718E7A",
    "dusty_blue": "#8FA9B8",
    "terracotta": "#D99478",
    "muted_yellow": "#D8BA68",
    "warm_cream": "#F1E9DE",
    "mist_gray": "#DCE2DE",
    "dusty_rose": "#D6A0A0",
}


MATERIAL_MAPPING = [
    ("Room", "Warm Cream / Mist Gray", "#F1E9DE / #DCE2DE"),
    ("Backdrop", "Mist Gray / Soft Sage", "#DCE2DE / #B8C9BD"),
    ("Base White", "Warm Cream", "#F1E9DE"),
    ("Base Gray", "Mist Gray", "#DCE2DE"),
    ("Base Purple", "Deep Sage", "#405D52"),
    ("Base Blue", "Dusty Blue", "#8FA9B8"),
    ("Base Blue Two", "Dusty Blue", "#8FA9B8"),
    ("Base Blue.001", "Dusty Blue", "#8FA9B8"),
    ("Chair Cushion", "Sage", "#718E7A"),
    ("Computer", "Dusty Blue", "#8FA9B8"),
    ("Drawer", "Mist Gray", "#DCE2DE"),
    ("Drawer Shelves", "Sage", "#718E7A"),
    ("Desk Pad", "Soft Terracotta", "#D99478"),
    ("Keyboard", "Warm Cream", "#F1E9DE"),
    ("Welcome Mat", "Deep Sage / Sage", "#405D52 / #718E7A"),
    ("Piano Stand", "Deep Sage", "#405D52"),
    ("Speaker", "Dusty Blue", "#8FA9B8"),
    ("Paper", "Soft Terracotta", "#D99478"),
    ("Book Cover One", "Dusty Blue", "#8FA9B8"),
    ("Book Cover Two", "Soft Terracotta", "#D99478"),
    ("Book Cover Four", "Sage", "#718E7A"),
    ("Flower Center", "Muted Yellow", "#D8BA68"),
    ("Flower Center Two", "Dusty Rose", "#D6A0A0"),
    ("Another Flower / Daylily / Lily", "Dusty Rose", "#D6A0A0"),
    ("Plant materials", "Deep Sage / Sage", "#405D52 / #718E7A"),
    ("Stone wall", "Mist Gray with existing moss", "#DCE2DE"),
    ("Wood / Light Wooden", "Existing natural wood", "Unchanged"),
]


def srgb_channel_to_linear(value):
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def hex_to_linear_rgba(hex_color):
    normalized = hex_color.lstrip("#")
    red = int(normalized[0:2], 16) / 255.0
    green = int(normalized[2:4], 16) / 255.0
    blue = int(normalized[4:6], 16) / 255.0
    return (
        srgb_channel_to_linear(red),
        srgb_channel_to_linear(green),
        srgb_channel_to_linear(blue),
        1.0,
    )


def set_principled_base_color(material_name, hex_color):
    material = bpy.data.materials.get(material_name)
    if material is None or material.node_tree is None:
        raise RuntimeError(f"Missing material or node tree: {material_name}")

    principled_nodes = [
        node
        for node in material.node_tree.nodes
        if node.type == "BSDF_PRINCIPLED"
    ]
    if not principled_nodes:
        raise RuntimeError(f"Missing Principled BSDF: {material_name}")

    base_color = principled_nodes[0].inputs.get("Base Color")
    if base_color is None or base_color.is_linked:
        raise RuntimeError(
            f"Base Color is linked and must be changed upstream: {material_name}"
        )

    base_color.default_value = hex_to_linear_rgba(hex_color)


def set_color_ramp(material_name, node_name, hex_colors):
    material = bpy.data.materials.get(material_name)
    if material is None or material.node_tree is None:
        raise RuntimeError(f"Missing material or node tree: {material_name}")

    node = material.node_tree.nodes.get(node_name)
    if node is None or node.type != "VALTORGB":
        raise RuntimeError(f"Missing color ramp {material_name}/{node_name}")

    elements = node.color_ramp.elements
    if len(elements) != len(hex_colors):
        raise RuntimeError(
            f"Color count mismatch for {material_name}/{node_name}: "
            f"{len(elements)} != {len(hex_colors)}"
        )

    for element, hex_color in zip(elements, hex_colors):
        element.color = hex_to_linear_rgba(hex_color)


def geometry_uv_signature():
    digest = hashlib.sha256()

    for object_data in sorted(bpy.data.objects, key=lambda item: item.name):
        digest.update(object_data.name.encode("utf-8"))
        digest.update(object_data.type.encode("ascii"))

        if object_data.type != "MESH" or object_data.data is None:
            continue

        mesh = object_data.data
        digest.update(mesh.name.encode("utf-8"))
        digest.update(
            struct.pack(
                "<4I",
                len(mesh.vertices),
                len(mesh.edges),
                len(mesh.polygons),
                len(mesh.loops),
            )
        )

        for vertex in mesh.vertices:
            digest.update(struct.pack("<3f", *vertex.co))

        for polygon in mesh.polygons:
            digest.update(struct.pack("<I", len(polygon.vertices)))
            for vertex_index in polygon.vertices:
                digest.update(struct.pack("<I", vertex_index))

        for uv_layer in mesh.uv_layers:
            digest.update(uv_layer.name.encode("utf-8"))
            for loop_uv in uv_layer.data:
                digest.update(struct.pack("<2f", *loop_uv.uv))

    return digest.hexdigest()


before_signature = geometry_uv_signature()

direct_material_colors = {
    "Base White": PALETTE["warm_cream"],
    "Base Gray": PALETTE["mist_gray"],
    "Base Purple": PALETTE["deep_sage"],
    "Base Blue": PALETTE["dusty_blue"],
    "Base Blue Two": PALETTE["dusty_blue"],
    "Base Blue.001": PALETTE["dusty_blue"],
    "Chair Cushion": PALETTE["sage"],
    "Computer": PALETTE["dusty_blue"],
    "Drawer": PALETTE["mist_gray"],
    "Drawer Shelves": PALETTE["sage"],
    "Keyboard": PALETTE["warm_cream"],
    "Piano Stand": PALETTE["deep_sage"],
    "Speaker": PALETTE["dusty_blue"],
    "Paper": PALETTE["terracotta"],
    "Book Cover One": PALETTE["dusty_blue"],
    "Book Cover Two": PALETTE["terracotta"],
    "Book Cover Four": PALETTE["sage"],
    "Flower Center": PALETTE["muted_yellow"],
    "Flower Center Two": PALETTE["dusty_rose"],
}

for material_name, hex_color in direct_material_colors.items():
    set_principled_base_color(material_name, hex_color)

# Large room surfaces stay neutral, with subtle texture variation intact.
set_color_ramp("Room", "Color Ramp", ["#DED4C6", PALETTE["warm_cream"]])
set_color_ramp("Room", "Color Ramp.001", ["#8F9892", PALETTE["mist_gray"]])
set_color_ramp("Room", "Color Ramp.003", [PALETTE["mist_gray"], PALETTE["warm_cream"]])
set_color_ramp("Backdrop", "Color Ramp", ["#B8C9BD", PALETTE["mist_gray"]])

# Calm furniture and grounded accents use separate palette families.
set_color_ramp("Desk Pad", "Color Ramp", ["#B86F59", PALETTE["terracotta"]])
set_color_ramp("Welcome Mat", "Color Ramp", [PALETTE["deep_sage"], PALETTE["sage"]])

# Keep plants natural while harmonizing their greens toward sage.
for material_name in ("Hanging Plant", "Plant Stem"):
    set_color_ramp(material_name, "Color Ramp", [PALETTE["sage"], PALETTE["deep_sage"]])
    set_color_ramp(material_name, "Color Ramp.001", ["#30483F", PALETTE["deep_sage"]])

set_color_ramp("Plant Gradient", "Color Ramp", [PALETTE["sage"], PALETTE["deep_sage"]])

# Preserve small floral personality with one controlled dusty-rose family.
for material_name in ("Another Flower", "Daylily", "Lily"):
    set_color_ramp(material_name, "Color Ramp", ["#B97878", PALETTE["dusty_rose"]])

# Only the neutral stone ramp changes; existing moss/brown procedural ramps remain.
set_color_ramp("Stone wall", "ColorRamp.004", ["#AEB8B2", PALETTE["mist_gray"]])

after_signature = geometry_uv_signature()
if before_signature != after_signature:
    raise RuntimeError("Geometry or UV data changed while applying the palette")

bpy.context.scene["grounded_pastel_palette"] = {
    key: value for key, value in PALETTE.items()
}
bpy.context.scene["grounded_pastel_geometry_uv_signature"] = after_signature

print("GROUND_PASTEL_MATERIAL_MAPPING")
for original, new_color, hex_value in MATERIAL_MAPPING:
    print(f"{original} -> {new_color} -> {hex_value}")
print(f"GEOMETRY_UV_SIGNATURE={after_signature}")

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
