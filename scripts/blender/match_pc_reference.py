"""Restore the PC's modeled details and match the supplied blush/lilac reference.

Run from the project root with Blender's --background <blend> --python.
The default renders a preview only; --commit saves the verified authoring scene.
No web models, atlases, UVs, room geometry, or original camera are rewritten.
"""
from __future__ import annotations
import bpy, math, json, sys, hashlib, warnings
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
warnings.filterwarnings('ignore', category=DeprecationWarning)

ROOT = Path.cwd().resolve()
OUT = ROOT / 'artifacts/pc-reference-match'
OUT.mkdir(parents=True, exist_ok=True)
COMMIT = '--commit' in sys.argv
BEFORE = '--before' in sys.argv
FINAL = '--final' in sys.argv
scene = bpy.context.scene
pc = bpy.data.objects['Plane.020_Baked']

def linear(h):
    rgb = [int(h.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in rgb)+(1,)

def material(name, color, rough=.4, metallic=0, glow=0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    m.node_tree.nodes.clear()
    bs=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value=linear(color)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metallic
    bs.inputs['IOR'].default_value=1.46
    bs.inputs['Coat Weight'].default_value=.18
    bs.inputs['Coat Roughness'].default_value=.28
    bs.inputs['Emission Color'].default_value=linear(color)
    bs.inputs['Emission Strength'].default_value=glow
    out=m.node_tree.nodes.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    m.diffuse_color=linear(color)
    return m

def components(mesh):
    parents=list(range(len(mesh.vertices)))
    ranks=[0]*len(parents)
    def find(a):
        while parents[a]!=a:
            parents[a]=parents[parents[a]]
            a=parents[a]
        return a
    for edge in mesh.edges:
        a,b=map(find,edge.vertices)
        if a==b: continue
        if ranks[a]<ranks[b]: a,b=b,a
        parents[b]=a
        if ranks[a]==ranks[b]: ranks[a]+=1
    groups=defaultdict(list)
    for p in mesh.polygons: groups[find(p.vertices[0])].append(p)
    return groups

def unrelated_state():
    result={}
    for o in bpy.data.objects:
        if o==pc or o.name.startswith(('PC_Upgrade_','PC_Reference_')) or o.name=='Point': continue
        state={'type':o.type,'matrix':[list(row) for row in o.matrix_world],'hide':o.hide_render}
        if o.type=='MESH':
            state['geometry']=hashlib.sha256(str(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()
            state['materials']=[m.name if m else None for m in o.data.materials]
        result[o.name]=state
    return result

before_state=unrelated_state()
original_pc_geometry=hashlib.sha256(str(([tuple(v.co) for v in pc.data.vertices],[tuple(p.vertices) for p in pc.data.polygons])).encode()).hexdigest()
added=[]
removed=[]

if not BEFORE:
    for o in list(bpy.data.objects):
        if o.name.startswith(('PC_Upgrade_','PC_Reference_')):
            removed.append(o.name)
            bpy.data.objects.remove(o,do_unlink=True)
    col=bpy.data.collections.get('PC Reference Match') or bpy.data.collections.new('PC Reference Match')
    if col.name not in scene.collection.children: scene.collection.children.link(col)

    mats={
      'shell':material('PC_Case_Blush_White','#EDD4E4',.25),
      'trim':material('PC_Case_Lavender_Trim','#CBB0C9',.38),
      'interior':material('PC_Interior_Mauve_Gray','#AC91B4',.53),
      'gpu':material('PC_GPU_Muted_Plum','#A397AA',.48),
      'board':material('PC_Motherboard_Mauve','#D1B0CE',.48),
      'tube':material('PC_Internal_Soft_Lavender','#D7BEDD',.3),
      'fan':material('PC_Fan_Pastel_Lilac','#E5DCE9',.43),
      'logo':material('PC_Logo_Deep_Mauve','#9A819F',.5),
      'vent':material('PC_Reference_Vent_Recess','#A692AF',.52),
      'led':material('PC_LED_Lavender','#E9C6FA',.35,glow=2.0),
      'hub':material('PC_Reference_Fan_Hub','#B497C8',.36),
      'small_led':material('PC_Reference_Small_LED','#CD91E1',.42,glow=.3),
    }
    pc.data.materials.clear()
    # Retain the original baked slot for project tooling; no PC polygon uses it.
    pc.data.materials.append(bpy.data.materials['FinalFourth_Baked'])
    slots={}
    for role,m in mats.items():
        pc.data.materials.append(m); slots[role]=len(pc.data.materials)-1
    roles={43:'shell',242:'shell',444:'shell',2860:'trim',2740:'trim',2758:'interior',
           635:'board',1275:'interior',657:'tube',957:'tube',1482:'gpu',1810:'gpu',1836:'gpu',
           2134:'fan',2432:'fan',575:'logo'}
    mapping={}
    for cid,polys in components(pc.data).items():
        role=roles.get(cid,'tube')
        if cid in range(1311,1370,8): role='vent'
        mapping[str(cid)]=role
        for p in polys:
            p.material_index=slots[role]
            # Keep planar panels planar, interpolate round shell and tube sections.
            p.use_smooth = cid in {43,242,444,2860,657,957,1482,1810,1836,2134,2432}
    for name in ['PC Reference weighted normals','PC Reference edge softness']:
        if pc.modifiers.get(name): pc.modifiers.remove(pc.modifiers[name])
    bevel=pc.modifiers.new('PC Reference edge softness','BEVEL')
    bevel.width=.015; bevel.segments=4; bevel.limit_method='ANGLE'; bevel.angle_limit=.65
    bevel.harden_normals=True
    # A face-area normal modifier flattens the shell's curved highlight.
    # Use the authored normals and a small, reversible geometric bevel.

    def collect(o,name,mat):
        o.name='PC_Reference_'+name
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
        o.data.materials.append(mat)
        added.append(o.name)
        return o

    def box(name,loc,dims,mat,bevel=.012):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_cube_add(location=loc)
        o=bpy.context.object; o.dimensions=dims
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        if bevel:
            mod=o.modifiers.new('Rounded edges','BEVEL'); mod.width=bevel; mod.segments=4
            bpy.ops.object.modifier_apply(modifier=mod.name)
        for p in o.data.polygons: p.use_smooth=True
        mod=o.modifiers.new('Face normals','WEIGHTED_NORMAL');mod.keep_sharp=True
        return collect(o,name,mat)

    def torus(name,loc,r,thickness,mat,axis='Y'):
        bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=thickness,major_segments=64,minor_segments=12,location=loc,rotation=(math.pi/2,0,0) if axis=='Y' else (0,math.pi/2,0))
        o=bpy.context.object
        for p in o.data.polygons: p.use_smooth=True
        return collect(o,name,mat)

    def disc(name,loc,r,depth,mat,axis='Y'):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=depth,location=loc,rotation=(math.pi/2,0,0) if axis=='Y' else (0,math.pi/2,0))
        o=bpy.context.object
        for p in o.data.polygons: p.use_smooth=len(p.vertices)==4
        return collect(o,name,mat)

    # The reference's luminous fan is on the back wall, above the GPU.
    torus('Upper_Rear_Fan_Diffuser',(-2.855,3.355,4.103),.143,.023,mats['led'],'X')
    disc('Upper_Rear_Fan_Rotor',(-2.840,3.355,4.103),.118,.012,mats['fan'],'X')
    disc('Upper_Rear_Fan_Hub',(-2.828,3.355,4.103),.047,.016,mats['hub'],'X')
    disc('Lower_Rear_Fan_Rotor',(-3.021,3.564,3.762),.125,.014,mats['fan'],'X')
    disc('Lower_Rear_Fan_Hub',(-3.006,3.564,3.762),.047,.016,mats['hub'],'X')

    # Restore solid pale fan faces, with small colored hubs, instead of neon rings.
    for i,x in enumerate((-2.48415,-2.14378,-1.80342),1):
        disc(f'GPU_Fan_{i}',(x,3.190,3.67083),.126,.012,mats['fan'])
        disc(f'GPU_Hub_{i}',(x,3.179,3.67083),.023,.010,mats['small_led'])

    # Small motherboard details sit behind the original cooler and tubes.
    for i,(x,z,s) in enumerate([(-2.67,4.19,.052),(-2.48,4.26,.036),(-2.63,4.01,.04),(-2.40,4.09,.035)]):
        box(f'Motherboard_Chip_{i}',(x,3.497,z),(s,.014,s*.8),mats['interior'],.006)
    box('Bottom_LED_Diffuser',(-2.24,3.235,3.312),(1.35,.025,.015),mats['led'],.007)

    # One thin physical pane: low roughness, dielectric reflections and lilac tint.
    glass=material('PC_Glass_Cool_Tint','#FBF6FF',.08)
    shader=next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Transmission Weight'].default_value=1
    shader.inputs['IOR'].default_value=1.45
    shader.inputs['Specular IOR Level'].default_value=.32
    shader.inputs['Coat Weight'].default_value=.08
    box('Glass_Panel',(-2.20,3.165,3.828),(1.43,.006,1.092),glass,.012)

    def light(name,loc,target,energy,color,size):
        data=bpy.data.lights.new('PC_Reference_'+name,'AREA')
        data.energy=energy; data.color=linear(color)[:3]; data.shape='DISK'; data.size=size
        o=bpy.data.objects.new(data.name,data); col.objects.link(o)
        o.location=loc; o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
        added.append(o.name)
        return o
    light('Softbox_Key',(-3.0,1.7,5.8),(-2.2,3.5,3.85),90,'#FFF0E5',1.8)
    light('Softbox_Front',(.1,1.7,4.9),(-1.7,3.6,3.9),100,'#FBE5F6',2.8)
    light('Interior_Lilac',(-2.15,3.29,4.29),(-2.5,3.85,3.65),6,'#E3B6F3',.65)
    light('Rear_Fan_Bounce',(-2.98,3.56,4.10),(-1.8,3.6,3.9),1.5,'#DFB3FA',.27)
    light('GPU_Fill',(-2.2,3.12,3.91),(-2.2,3.6,3.5),1.5,'#F2DFF9',.8)
    point=bpy.data.objects.get('Point')
    if point:
        point.location=(-2.45,3.57,3.65)
        point.data.energy=1.5; point.data.color=linear('#DDC4EE')[:3]; point.data.shadow_soft_size=.28

    receivers=bpy.data.collections.get('PC Reference Light Receivers')
    if receivers: bpy.data.collections.remove(receivers)
    receivers=bpy.data.collections.new('PC Reference Light Receivers')
    receivers.objects.link(pc)
    for o in col.objects:
        if o.type=='MESH':receivers.objects.link(o)
    for o in list(col.objects)+([point] if point else []):
        if o.type=='LIGHT':o.light_linking.receiver_collection=receivers
    old_collection=bpy.data.collections.get('PC Upgrade')
    if old_collection and not old_collection.objects:
        bpy.data.collections.remove(old_collection)

assert before_state==unrelated_state(), 'An unrelated object changed'
assert original_pc_geometry==hashlib.sha256(str(([tuple(v.co) for v in pc.data.vertices],[tuple(p.vertices) for p in pc.data.polygons])).encode()).hexdigest(), 'Base PC geometry changed'

def render():
    camera_data=bpy.data.cameras.new('PC_Reference_Preview_Camera')
    camera=bpy.data.objects.new(camera_data.name,camera_data)
    scene.collection.objects.link(camera)
    target=Vector((-2.35,3.53,3.84))
    camera.location=target+Vector((6,-8,2.0))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.type='ORTHO';camera_data.ortho_scale=3.55
    original_camera=scene.camera
    settings={p:getattr(scene.render,p) for p in ['engine','resolution_x','resolution_y','resolution_percentage','filepath','film_transparent']}
    cycle_settings={p:getattr(scene.cycles,p) for p in ['samples','device','use_denoising','max_bounces','transparent_max_bounces']}
    original_format=scene.render.image_settings.file_format
    try:
        scene.camera=camera
        scene.render.engine='CYCLES'
        scene.render.resolution_x=1400 if FINAL else 1000
        scene.render.resolution_y=1120 if FINAL else 800
        scene.render.resolution_percentage=100
        scene.render.film_transparent=False
        scene.render.image_settings.file_format='PNG'
        scene.cycles.samples=192 if FINAL else 64
        scene.cycles.use_denoising=True
        scene.cycles.max_bounces=8
        scene.cycles.transparent_max_bounces=8
        prefs=bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices: d.use=d.type=='OPTIX'
        scene.cycles.device='GPU'
        label='before' if BEFORE else ('after' if FINAL else 'preview')
        scene.render.filepath=str(OUT/f'pc-{label}.png')
        bpy.ops.render.render(write_still=True)
    finally:
        scene.camera=original_camera
        for p,v in settings.items():setattr(scene.render,p,v)
        for p,v in cycle_settings.items():setattr(scene.cycles,p,v)
        scene.render.image_settings.file_format=original_format
        bpy.data.objects.remove(camera,do_unlink=True)
        bpy.data.cameras.remove(camera_data)

if '--no-render' not in sys.argv:
    render()
report={'blend':bpy.data.filepath,'committed':COMMIT,'added':added,'removed':removed,
        'unrelated_objects_unchanged':before_state==unrelated_state(),
        'original_pc_mesh_unchanged':True,'pc_vertices':len(pc.data.vertices),'pc_polygons':len(pc.data.polygons)}
if not BEFORE:
    report['component_materials']=mapping
    (OUT/'match-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if COMMIT:
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.object.select_all(action='DESELECT')
    pc.select_set(True);bpy.context.view_layer.objects.active=pc
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('PC_REFERENCE_RESULT',json.dumps(report))
