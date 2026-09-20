"""Reopen the backup and final blend, compare unaffected scene data, then verify."""
import bpy, json, hashlib, runpy, sys
from mathutils import Vector
from pathlib import Path

root=Path.cwd().resolve()
out=root/'artifacts/pc-reference-match'
final=root/'blender files/My Room - FINAL.blend'
backup=out/'backup/My Room - before-reference-match.blend'
polish='--polish' in sys.argv
studio='--studio' in sys.argv or polish
if studio:backup=out/'backup/My Room - before-studio-reference.blend'
if polish:backup=out/'backup/My Room - before-polish.blend'

def pc_geometry():
    return {o.name:digest(sorted(tuple(round(c,6) for c in o.matrix_world @ v.co) for v in o.data.vertices))
        for o in bpy.data.collections['PC Reference Match'].objects if o.type=='MESH'}

def digest(value):
    return hashlib.sha256(repr(value).encode()).hexdigest()

def snapshot():
    objects={}
    for o in bpy.data.objects:
        if studio and o.name=='Plane.020_Baked':continue
        if o.name.startswith(('PC_Upgrade_','PC_Reference_')) or o.name=='Point':continue
        record={'type':o.type,'transform':list(map(tuple,o.matrix_world)),
                'hidden':[o.hide_render,o.hide_viewport]}
        if o.type=='MESH':
            record['positions']=digest([tuple(v.co) for v in o.data.vertices])
            record['topology']=digest([tuple(p.vertices) for p in o.data.polygons])
            record['uvs']={uv.name:digest([tuple(v.uv) for v in uv.data]) for uv in o.data.uv_layers}
            if o.name!='Plane.020_Baked':
                record['materials']=[m.name if m else None for m in o.data.materials]
                record['face_materials']=digest([p.material_index for p in o.data.polygons])
        if o.type=='CAMERA':
            record['camera']=[o.data.type,o.data.lens,o.data.ortho_scale]
        objects[o.name]=record
    images={i.name:{'size':list(i.size),'packed':bool(i.packed_file),
                   'data':hashlib.sha256(i.packed_file.data).hexdigest() if i.packed_file else i.filepath}
            for i in bpy.data.images if i.type!='RENDER_RESULT'}
    materials={}
    for m in bpy.data.materials:
        if m.name.startswith('PC_'):continue
        nodes=[]
        if m.node_tree:
            for n in m.node_tree.nodes:
                values={}
                for s in n.inputs:
                    if hasattr(s,'default_value'):
                        val=s.default_value
                        try:val=list(val)
                        except TypeError:pass
                        values[s.identifier]=val
                nodes.append((n.name,n.bl_idname,values,getattr(getattr(n,'image',None),'name',None)))
            links=[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]
            materials[m.name]=digest((nodes,links))
    s=bpy.context.scene
    return {'objects':objects,'images':images,'materials':materials,
            'camera':s.camera.name,'color_management':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma],
            'render':[s.render.engine,s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage]}

bpy.ops.wm.open_mainfile(filepath=str(backup))
before=snapshot()
if polish:pc_before=pc_geometry()
bpy.ops.wm.open_mainfile(filepath=str(final))
after=snapshot()
differences={}
for key in before:
    if before[key]!=after[key]:
        if isinstance(before[key],dict):
            differences[key]=[n for n in set(before[key])|set(after[key]) if before[key].get(n)!=after[key].get(n)]
        else: differences[key]={'before':before[key],'after':after[key]}
fan_mount={}
if polish:
    pc_after=pc_geometry()
    changed=sorted(n for n in set(pc_before)|set(pc_after) if pc_before.get(n)!=pc_after.get(n))
    allowed=('PC_Reference_Rear_Fan_','PC_Reference_Upper_Rear_Fan_','PC_Reference_Lower_Rear_Fan_')
    unexpected=[n for n in changed if not n.startswith(allowed)]
    if unexpected:differences['pc_geometry_outside_fan']=unexpected
    frame=bpy.data.objects['PC_Reference_Rear_Fan_Frame']
    rear=bpy.data.objects['PC_Reference_Rear_Panel']
    rotor=bpy.data.objects['PC_Reference_Upper_Rear_Fan_Rotor']
    frame_back=min((frame.matrix_world @ Vector(v)).x for v in frame.bound_box)
    rear_inside=max((rear.matrix_world @ Vector(v)).x for v in rear.bound_box)
    fan_axis=(rotor.matrix_world.to_3x3() @ Vector((0,0,1))).normalized()
    normal_alignment=abs(fan_axis.dot(Vector((1,0,0))))
    fan_mount={'gap':frame_back-rear_inside,'normal_alignment':normal_alignment,
        'changed_geometry':changed,'other_pc_geometry_preserved':not unexpected}
    if abs(frame_back-rear_inside)>.0001 or normal_alignment<.99999:
        differences['rear_fan_mount']=fan_mount
report={'passed':not differences,'differences':differences,
        'unrelated_objects_compared':len(before['objects'])-(0 if studio else 1),'images_compared':len(before['images']),
        'non_pc_materials_compared':len(before['materials']),
        'base_pc_geometry_and_uvs_preserved':not studio and before['objects']['Plane.020_Baked']==after['objects']['Plane.020_Baked'],
        'pc_rebuilt_to_studio_references':studio,
        'pc_polish':polish,'rear_fan_mount':fan_mount,
        'backup_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),
        'final_sha256':hashlib.sha256(final.read_bytes()).hexdigest()}
(out/'preservation-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PC_PRESERVATION',json.dumps(report))
assert not differences, differences
runpy.run_path(str(root/'scripts/blender/verify_final_room_blend.py'),run_name='__main__')
