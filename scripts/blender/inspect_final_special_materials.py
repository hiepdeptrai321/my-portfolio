"""Inspect final Facebook/tree material nodes and non-mesh scene objects."""

import json
from pathlib import Path

import bpy


blend = Path(bpy.data.filepath).resolve()
root = blend.parent.parent
material_names = (
    "Tree_Green",
    "Tree_Wood",
    "Material.001",
    "Material.f",
    "Tinta_1.002",
    "Tinta_3.001",
    "Tinta_3.002",
)
materials = {}
for name in material_names:
    material = bpy.data.materials.get(name)
    if material is None:
        materials[name] = None
        continue
    node_records = []
    if material.node_tree:
        for node in material.node_tree.nodes:
            inputs = {}
            for socket in node.inputs:
                value = getattr(socket, "default_value", None)
                if isinstance(value, (int, float, str, bool)):
                    inputs[socket.name] = value
                elif value is not None:
                    try:
                        inputs[socket.name] = [float(item) for item in value]
                    except (TypeError, ValueError):
                        pass
            node_records.append(
                {
                    "name": node.name,
                    "type": node.bl_idname,
                    "inputs": inputs,
                }
            )
    materials[name] = {
        "diffuse_color": [float(value) for value in material.diffuse_color],
        "nodes": node_records,
        "links": [
            {
                "from": link.from_node.name,
                "from_socket": link.from_socket.name,
                "to": link.to_node.name,
                "to_socket": link.to_socket.name,
            }
            for link in material.node_tree.links
        ]
        if material.node_tree
        else [],
    }

report = {
    "blend": str(blend),
    "non_mesh_objects": [
        {
            "name": obj.name,
            "type": obj.type,
            "hide_viewport": obj.hide_viewport,
            "hide_render": obj.hide_render,
        }
        for obj in bpy.data.objects
        if obj.type != "MESH"
    ],
    "materials": materials,
}
output = root / "artifacts/final-room-audit/final-special-materials.json"
output.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("FINAL_SPECIAL_MATERIALS", output)
print("NON_MESH", report["non_mesh_objects"])
for name, material in materials.items():
    print("MATERIAL", name, "exists", material is not None)
    if material:
        print("DIFFUSE", material["diffuse_color"])
        print("LINKS", material["links"])
