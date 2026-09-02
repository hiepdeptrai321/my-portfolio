"""Read-only audit of the four baked materials in For Export.blend."""

from __future__ import annotations

import json
from pathlib import Path

import bpy


ROOT = Path(bpy.data.filepath).resolve().parent.parent
OUTPUT = ROOT / "artifacts/grounded-pastel-no-rebake/export-material-node-audit.json"
EXPECTED = [
    "FinalFirst_Baked",
    "RealFinalSecond_Baked",
    "FinalThird_Baked",
    "FinalFourth_Baked",
]

report = {
    "blend": str(Path(bpy.data.filepath).resolve()),
    "materials": {},
}

for material_name in EXPECTED:
    material = bpy.data.materials.get(material_name)
    if material is None:
        report["materials"][material_name] = {"missing": True}
        continue

    nodes = []
    if material.use_nodes and material.node_tree:
        for node in material.node_tree.nodes:
            node_report = {
                "name": node.name,
                "label": node.label,
                "type": node.bl_idname,
            }
            if node.bl_idname == "ShaderNodeTexImage":
                node_report["image"] = node.image.name if node.image else None
                node_report["filepath"] = (
                    bpy.path.abspath(node.image.filepath) if node.image else None
                )
                node_report["colorspace"] = (
                    node.image.colorspace_settings.name if node.image else None
                )
            nodes.append(node_report)

    users = sorted(
        obj.name
        for obj in bpy.data.objects
        if obj.type == "MESH"
        and any(slot.material == material for slot in obj.material_slots)
    )
    report["materials"][material_name] = {
        "missing": False,
        "use_nodes": material.use_nodes,
        "node_count": len(nodes),
        "nodes": nodes,
        "links": (
            [
                {
                    "from_node": link.from_node.name,
                    "from_socket": link.from_socket.name,
                    "to_node": link.to_node.name,
                    "to_socket": link.to_socket.name,
                }
                for link in material.node_tree.links
            ]
            if material.node_tree
            else []
        ),
        "object_users": users,
        "object_user_count": len(users),
    }

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("EXPORT_MATERIAL_NODE_AUDIT", OUTPUT)
for name, item in report["materials"].items():
    print(
        "MATERIAL",
        name,
        "missing",
        item["missing"],
        "users",
        item.get("object_user_count", 0),
        "nodes",
        item.get("node_count", 0),
    )
