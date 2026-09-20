"""Inspect current PC shading and scene lighting without changing the blend."""
import bpy, json
from pathlib import Path
from mathutils import Vector

root = Path.cwd()
out = root / 'artifacts/pc-reference-match'
out.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
def vals(v):
    try: return [round(float(x), 5) for x in v]
    except TypeError: return v
def bounds(o):
    vs = [o.matrix_world @ Vector(v) for v in o.bound_box]
    return [[round(f(v[a] for v in vs), 5) for a in range(3)] for f in [min,max]]
report = {'blender':bpy.app.version_string, 'engine':scene.render.engine,
          'view':scene.view_settings.view_transform, 'look':scene.view_settings.look,
          'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma,
          'camera':scene.camera.name if scene.camera else None,
          'compositor':str(scene.compositing_node_group) if hasattr(scene,'compositing_node_group') else '',
          'world':[], 'lights':[], 'objects':[], 'materials':[]}
if scene.world and scene.world.node_tree:
    report['world']=[{'type':n.type,'inputs':{s.name:vals(s.default_value) for s in n.inputs if hasattr(s,'default_value')}} for n in scene.world.node_tree.nodes]
for o in bpy.data.objects:
    if o.type == 'LIGHT':
        report['lights'].append({'name':o.name,'type':o.data.type,'pos':vals(o.location),'rotation':vals(o.rotation_euler),'energy':o.data.energy,'color':vals(o.data.color),'size':getattr(o.data,'size',getattr(o.data,'shadow_soft_size',0)),'hide':o.hide_render})
    if o.type == 'MESH' and (o.name.startswith('PC_') or any(k in o.name.lower() for k in ['plane.020','computer_fan','computer_glass'])):
        report['objects'].append({'name':o.name,'bounds':bounds(o),'hide':o.hide_render,'hide_viewport':o.hide_get(),'materials':[m.name if m else None for m in o.data.materials],'modifiers':[(m.name,m.type) for m in o.modifiers]})
for m in bpy.data.materials:
    if m.name.startswith('PC_') or m.name in ['FinalFourth_Baked','Computer_Glass']:
        report['materials'].append({'name':m.name,'nodes':[{'type':n.type,'inputs':{s.name:vals(s.default_value) for s in n.inputs if hasattr(s,'default_value') and not s.is_linked}} for n in m.node_tree.nodes] if m.node_tree else []})
try:
    cp=bpy.context.preferences.addons['cycles'].preferences
    cp.get_devices()
    report['devices']=[(d.name,d.type) for d in cp.devices]
except Exception as e: report['devices']=str(e)
(out/'scene-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='materials'},indent=2))
