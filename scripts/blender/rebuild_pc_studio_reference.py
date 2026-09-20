"""Rebuild the PC from the user's four pearl/lavender studio references.

The room stays in place. --commit saves the reviewed PC; --final increases
preview quality. --front and --room select useful validation views.
"""
import bpy, bmesh, math, json, sys, warnings, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
warnings.filterwarnings('ignore', category=DeprecationWarning)
ROOT=Path.cwd().resolve()
OUT=ROOT/'artifacts/pc-reference-match'
FINAL='--final' in sys.argv
COMMIT='--commit' in sys.argv
scene=bpy.context.scene
PREFIX='PC_Reference_'

def unrelated():
    return {o.name:hashlib.sha256(repr((o.type,list(map(tuple,o.matrix_world)),
        [(tuple(v.co)) for v in o.data.vertices] if o.type=='MESH' else [],
        [tuple(p.vertices) for p in o.data.polygons] if o.type=='MESH' else [],
        [m.name if m else '' for m in o.data.materials] if o.type=='MESH' else [])).encode()).hexdigest()
        for o in bpy.data.objects if o.name!='Plane.020_Baked' and o.name!='Point'
        and not o.name.startswith(('PC_Reference_','PC_Upgrade_'))}
original=unrelated()
for o in list(bpy.data.objects):
    if o.name=='Plane.020_Baked' or o.name.startswith(('PC_Reference_','PC_Upgrade_')):
        bpy.data.objects.remove(o,do_unlink=True)
for name in ['PC Reference Match','PC Reference Light Receivers','PC Upgrade']:
    if bpy.data.collections.get(name):bpy.data.collections.remove(bpy.data.collections[name])
col=bpy.data.collections.new('PC Reference Match');scene.collection.children.link(col)
col['reference_version']='studio-v2'
col['refinement_version']='polish-v3'

def rgba(h):
    c=[int(h.strip('#')[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)+(1,)
def mat(name,color,rough=.35,metal=0,emission=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True;m.node_tree.nodes.clear()
    p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    for k,v in {'Base Color':rgba(color),'Roughness':rough,'Metallic':metal,
                'Coat Weight':.22,'Coat Roughness':.22,'Emission Color':rgba(color),'Emission Strength':emission}.items():
        p.inputs[k].default_value=v
    out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    m.diffuse_color=rgba(color)
    return m
M={
    'shell':mat('PC_Case_Blush_White','#F2ECE7',.28,.035),
    'trim':mat('PC_Case_Lavender_Trim','#CBC7D3',.38,.08),
    'board':mat('PC_Motherboard_Mauve','#C5B9D6',.46),
    'detail':mat('PC_Interior_Mauve_Gray','#ACA4BC',.42,.05),
    'dark':mat('PC_GPU_Muted_Plum','#8B829C',.43),
    'tube':mat('PC_Internal_Soft_Lavender','#DDD1E8',.34),
    'fan':mat('PC_Fan_Pastel_Lilac','#C4B7D1',.36,.14),
    'blade':mat('PC_Reference_Fan_Blade','#D9C9E4',.31,.10),
    'logo':mat('PC_Logo_Deep_Mauve','#9A7BAE',.43),
    'recess':mat('PC_Reference_Vent_Recess','#716B7D',.58),
    'silver':mat('PC_Reference_Fasteners','#9593A1',.3,.45),
    'mesh':mat('PC_Reference_Vent_Mesh','#ABA5B5',.46,.16),
    'bracket':mat('PC_Reference_Mounts','#BAB5C6',.36,.18),
    'led':mat('PC_LED_Lavender','#E6BAFF',.3,emission=4.5),
    'port':mat('PC_Reference_Port_Black','#26212D',.55),
    'vent_glow':mat('PC_Reference_Vent_Glow','#CDA6EC',.6,emission=.35),
}

# Short-range, low-strength contact shading adds readable seams without dark
# outlines. These nodes belong only to PC surfaces and bake into its atlas.
for key,m in M.items():
    if key in ('led','vent_glow'):continue
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    ao=m.node_tree.nodes.new('ShaderNodeAmbientOcclusion');ao.name='Soft PC contact occlusion'
    ao.inputs['Distance'].default_value=.045;ao.samples=16
    multiply=m.node_tree.nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY'
    multiply.inputs[0].default_value=.20 if key=='shell' else .30
    multiply.inputs[1].default_value=p.inputs['Base Color'].default_value[:]
    m.node_tree.links.new(ao.outputs['Color'],multiply.inputs[2])
    m.node_tree.links.new(multiply.outputs[0],p.inputs['Base Color'])

def own(o,name,m):
    o.name=PREFIX+name
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o)
    if m:o.data.materials.append(m)
    return o
def mesh(name,verts,faces,m,smooth=False):
    d=bpy.data.meshes.new(PREFIX+name);d.from_pydata(verts,[],faces);d.update()
    o=bpy.data.objects.new(PREFIX+name,d);col.objects.link(o)
    if m:d.materials.append(m)
    if smooth:
        for p in d.polygons:p.use_smooth=True
    return o
def apply(o,modifier):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.modifier_apply(modifier=modifier.name)
def bevel(o,width,segments=4):
    b=o.modifiers.new('Rounded machining','BEVEL');b.width=width;b.segments=segments;b.limit_method='ANGLE';b.harden_normals=True
    apply(o,b)
    for p in o.data.polygons:p.use_smooth=True
    n=o.modifiers.new('Surface normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=30
    apply(o,n)
    return o
def box(name,loc,dims,m,r=.01):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    own(o,name,m)
    if r:bevel(o,r,5)
    return o
def disc(name,loc,r,depth,m,axis='Y',vertices=48):
    rotation={'Y':(math.pi/2,0,0),'X':(0,math.pi/2,0),'Z':(0,0,0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc,rotation=rotation)
    o=own(bpy.context.object,name,m)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o
def ring(name,loc,r,t,m,axis='Y'):
    rotation={'Y':(math.pi/2,0,0),'X':(0,math.pi/2,0),'Z':(0,0,0)}[axis]
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=t,major_segments=64,minor_segments=10,location=loc,rotation=rotation)
    o=own(bpy.context.object,name,m)
    for p in o.data.polygons:p.use_smooth=True
    return o
def boolean(o,cutter):
    mod=o.modifiers.new('Machined opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    apply(o,mod);bpy.data.objects.remove(cutter,do_unlink=True)
    # Boolean topology invalidates the pre-cut custom normals.
    o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
    o.data.set_sharp_from_angle(angle=math.radians(40))
    n=o.modifiers.new('Normals after machining','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=50;apply(o,n)
def rr_points(cx,cy,w,d,r,n=12):
    pts=[]
    for x,y,a in [(cx+w/2-r,cy+d/2-r,0),(cx-w/2+r,cy+d/2-r,90),(cx-w/2+r,cy-d/2+r,180),(cx+w/2-r,cy-d/2+r,270)]:
        for j in range(n+1):
            t=math.radians(a+90*j/n);pts.append((x+r*math.cos(t),y+r*math.sin(t)))
    return pts
def lid(name,z,h,m):
    pts=rr_points(-2.26,3.575,1.98,.83,.145)
    n=len(pts);verts=[(x,y,z+s*h/2) for s in (-1,1) for x,y in pts]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,verts,faces,m)
    return bevel(o,.025,5)
def plane_point(center,u,v,axis):
    x,y,z=center
    return {'Z':(x+u,y+v,z),'Y':(x+u,y,z+v),'X':(x,y+u,z+v)}[axis]
def perforated(name,center,w,h,cols,rows,m,axis='Z',ratio=.31):
    # Real holes: each cell bridges its square outline to a circular opening.
    verts=[];faces=[];dx=w/cols;dy=h/rows;r=min(dx,dy)*ratio
    for row in range(rows):
        for c in range(cols):
            cx=-w/2+(c+.5)*dx;cy=-h/2+(row+.5)*dy
            start=len(verts)
            for radius in ('outer','inner'):
                for k in range(16):
                    a=math.tau*k/16
                    scale=min(dx/2/max(abs(math.cos(a)),1e-6),dy/2/max(abs(math.sin(a)),1e-6)) if radius=='outer' else r
                    verts.append(plane_point(center,cx+scale*math.cos(a),cy+scale*math.sin(a),axis))
            for k in range(16):
                q=(start+k,start+(k+1)%16,start+16+(k+1)%16,start+16+k)
                faces.append(q)
    o=mesh(name,verts,faces,m)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(o.data);bm.free()
    solid=o.modifiers.new('Sheet thickness','SOLIDIFY');solid.thickness=.0025;apply(o,solid)
    return o
def polygon(name,points,center,size,m,axis='Y'):
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))<0:points=list(reversed(points))
    vectors=[Vector((u*size,v*size,0)) for u,v in points]
    triangles=tessellate_polygon([vectors])
    lookup={tuple(v):i for i,v in enumerate(vectors)}
    faces=[tuple(v if isinstance(v,int) else lookup[tuple(v)] for v in t) for t in triangles]
    return mesh(name,[plane_point(center,v.x,v.y,axis) for v in vectors],faces,m)
def logo(name,center,size,axis='Y'):
    outline=[];a=(-.44,.12)
    segments=[((-.53,.27),(-.61,.57),(-.57,.60)),
        ((-.55,.66),(-.25,.46),(-.19,.40)),
        ((-.07,.47),(.07,.47),(.19,.40)),
        ((.25,.46),(.55,.66),(.57,.60)),
        ((.61,.57),(.53,.27),(.44,.12)),
        ((.42,-.03),(.31,-.10),(.25,-.15)),
        ((.21,-.25),(.22,-.36),(.17,-.44)),
        ((.10,-.60),(-.10,-.60),(-.17,-.44)),
        ((-.22,-.36),(-.21,-.25),(-.25,-.15)),
        ((-.31,-.10),(-.42,-.03),(-.44,.12))]
    for b,c,d in segments:
        for j in range(6):
            t=j/6
            outline.append(tuple((1-t)**3*a[k]+3*(1-t)**2*t*b[k]+3*(1-t)*t*t*c[k]+t**3*d[k] for k in (0,1)))
        a=d
    polygon(name+'_Silhouette',outline,center,size,M['logo'],axis)
    delta={'X':(.0007,0,0),'Y':(0,-.0007,0),'Z':(0,0,.0007)}[axis]
    front=tuple(a+b for a,b in zip(center,delta))
    for sign in (-1,1):polygon(name+f'_Ear_{sign}',[(sign*.43,.44),(sign*.27,.36),(sign*.38,.24)],front,size,M['shell'],axis)
    heart=[]
    for k in range(48):
        t=math.tau*k/48
        heart.append((16*math.sin(t)**3/70,(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))/70+.05))
    polygon(name+'_Heart',heart,front,size,M['shell'],axis)
def screw(name,loc,axis='Y',r=.012):
    disc(name,loc,r,.007,M['silver'],axis,24)
def cable(name,points,r=.038):
    d=bpy.data.curves.new(PREFIX+name,'CURVE');d.dimensions='3D';d.resolution_u=16;d.bevel_depth=r;d.bevel_resolution=4
    s=d.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for p,c in zip(s.bezier_points,points):p.co=c;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=bpy.data.objects.new(PREFIX+name,d);col.objects.link(o);d.materials.append(M['tube'])
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
    return bpy.context.object

# Pearl enclosure, taller proportions and four low feet, at the existing desk position.
base=lid('Lower_Case',3.26,.19,M['shell']);base.name='Plane.020_Baked'
base.data.materials.append(bpy.data.materials['FinalFourth_Baked'])
base['pc_reference_version']='studio-v2'
top=lid('Top_Case',5.045,.18,M['shell'])
cut=box('Temporary_Top_Cut',(-2.41,3.57,5.06),(1.34,.43,.35),None,.045)
boolean(top,cut)
perforated('Top_Mesh_Grille',(-2.41,3.57,5.116),1.31,.40,38,12,M['mesh'],ratio=.32)
box('Top_Grille_Recess',(-2.41,3.57,5.045),(1.34,.43,.009),M['recess'],.015)
for x in (-3.02,-1.50):
    for y in (3.32,3.82):disc(f'Foot_{x}_{y}',(x,y,3.12),.097,.10,M['trim'],'Z')

# Front wrap, with a field of ventilated holes below the logo.
path=[]
for cx,cy,start_angle in [(-1.415,3.305,270),(-1.415,3.845,0)]:
    for i in range(17):
        t=math.radians(start_angle+90*i/16);path.append((cx+.145*math.cos(t),cy+.145*math.sin(t)))
pn=len(path)
front=mesh('Front_Panel',[(x,y,z) for z in (3.355,4.953) for x,y in path],
    [(i,i+1,i+1+pn,i+pn) for i in range(pn-1)],M['shell'])
s=front.modifiers.new('Sheet metal','SOLIDIFY');s.thickness=.028;s.offset=-1;apply(front,s);bevel(front,.005,3)
boolean(front,box('Temporary_Front_Cut',(-1.30,3.575,3.85),(.35,.48,.65),None,.004))
perforated('Front_Perforations',(-1.2695,3.575,3.85),.480,.650,14,20,M['shell'],'X',.25)
box('Front_Vent_Inner_Glow',(-1.37,3.575,3.85),(.015,.48,.65),M['vent_glow'],.005)
logo('Front_Heart_Cat',(-1.260,3.575,4.60),.145,'X')
back=box('Rear_Panel',(-3.208,3.575,4.155),(.055,.72,1.57),M['trim'],.02)
box('Inner_Back_Wall',(-2.28,3.967,4.15),(1.82,.028,1.57),M['trim'],.02)
for x in (-3.164,-1.446):box(f'Glass_Pillar_{x}',(x,3.22,4.15),(.037,.065,1.60),M['bracket'],.010)
for x in (-3.105,-1.52):
    for z in (3.405,4.92):screw(f'Glass_Mount_{x}_{z}',(x,3.157,z),r=.013)

# Motherboard, raised cold plate, RAM slots, capacitors and circuit detail.
box('Motherboard',(-2.20,3.847,4.49),(1.24,.038,.86),M['board'],.025)
box('CPU_Mount',(-2.43,3.794,4.52),(.365,.057,.36),M['bracket'],.028)
box('CPU_Cold_Plate',(-2.43,3.754,4.52),(.324,.042,.318),M['tube'],.025)
logo('CPU_Heart_Cat',(-2.43,3.731,4.53),.12)
for x in (-2.559,-2.301):
    for z in (4.395,4.645):screw(f'CPU_Screw_{x}_{z}',(x,3.727,z),r=.011)
for i,x in enumerate((-2.735,-2.678,-2.621,-2.38,-2.321)):
    for j,z in enumerate((4.78,4.22)):
        disc(f'Capacitor_{i}_{j}',(x,3.802,z),.020,.050,M['detail'],'Y',24)
for i in range(5):
    box(f'VRM_{i}',(-2.735,3.796,4.30+i*.079),(.039,.04,.048),M['detail'],.006)
for i in range(3):
    box(f'Board_Heatsink_{i}',(-2.44,3.816,4.84-i*.015),(.48,.024,.012),M['trim'],.003)
for i in range(18):
    x=-2.73+(i%9)*.115;z=4.17+(i//9)*.70
    box(f'SMD_{i}',(x,3.822,z),(.020,.009,.011),M['silver'],.002)
for i,x in enumerate((-2.085,-1.999)):
    box(f'RAM_Socket_{i}',(x,3.798,4.49),(.064,.04,.59),M['bracket'],.007)
    box(f'RAM_Module_{i}',(x,3.737,4.51),(.057,.081,.54),M['detail'],.008)
    box(f'RAM_LED_{i}',(x,3.693,4.51),(.012,.008,.426),M['led'],.005)
box('Motherboard_Lower_Rail',(-2.25,3.783,4.105),(1.13,.065,.035),M['bracket'],.007)
for i in range(9):box(f'Radiator_Fin_{i}',(-1.645,3.81,4.37+i*.055),(.14,.044,.018),M['detail'],.004)
box('Radiator_Block',(-1.598,3.83,4.45),(.25,.10,.75),M['trim'],.025)
for i,dz in enumerate((0,-.19)):
    cable(f'Cooling_Tube_{i}',[(-1.902,3.575,4.79+dz),(-1.88,3.43,4.73+dz),(-1.73,3.39,4.70+dz),(-1.52,3.44,4.82+dz)],.041)

# The housing's rear face sits exactly on the rear panel's interior face.
# Keep the fan axis perpendicular to that panel, with no camera-facing tilt.
frame=box('Rear_Fan_Frame',(-3.1295,3.47,4.58),(.102,.50,.51),M['bracket'],.029)
boolean(frame,disc('Temporary_Fan_Cut',(-3.10,3.47,4.58),.217,.18,None,'X'))
ring('Upper_Rear_Fan_Diffuser',(-3.064,3.47,4.58),.216,.014,M['led'],'X')
disc('Upper_Rear_Fan_Rotor',(-3.075,3.47,4.58),.200,.014,M['fan'],'X')
disc('Upper_Rear_Fan_Hub',(-3.056,3.47,4.58),.069,.018,M['detail'],'X')
logo('Rear_Fan_Heart_Cat',(-3.045,3.47,4.58),.070,'X')
for y in (3.25,3.69):
    for z in (4.36,4.80):screw(f'Rear_Fan_Screw_{y}_{z}',(-3.073,y,z),'X')
disc('Lower_Rear_Fan_Rotor',(-3.1705,3.46,4.232),.071,.018,M['fan'],'X')
ring('Lower_Rear_Fan_LED',(-3.1555,3.46,4.232),.043,.006,M['led'],'X')
disc('Lower_Rear_Fan_Hub',(-3.1475,3.46,4.232),.018,.01,M['detail'],'X')

# Three quiet metallic lilac GPU fans in a proper open frame.
box('GPU_Body',(-2.255,3.442,3.891),(1.45,.24,.43),M['dark'],.028)
gpu_frame=box('GPU_Front_Frame',(-2.255,3.269,3.891),(1.45,.047,.452),M['dark'],.027)
for z in (3.682,4.100):box(f'GPU_Frame_Rail_{z}',(-2.255,3.240,z),(1.36,.026,.028),M['trim'],.008)
for i,x in enumerate((-2.713,-2.255,-1.797),1):
    boolean(gpu_frame,disc(f'Temporary_GPU_Cut_{i}',(x,3.27,3.891),.186,.16,None,'Y',64))
    disc(f'GPU_Fan_{i}',(x,3.257,3.891),.178,.014,M['fan'])
    ring(f'GPU_Fan_Rim_{i}',(x,3.249,3.891),.181,.006,M['detail'])
    # Keep a smooth rotor face, as in the softly blurred reference fans.
    disc(f'GPU_Hub_{i}',(x,3.225,3.891),.066,.018,M['shell'])
    logo(f'GPU_{i}_Heart_Cat',(x,3.214,3.891),.057)
for i,(x,z) in enumerate([(-2.914,4.066),(-1.596,4.066),(-2.914,3.719),(-1.596,3.719)]):
    box(f'GPU_Corner_{i}',(x,3.224,z),(.103,.025,.088),M['bracket'],.016)
    screw(f'GPU_Corner_Screw_{i}',(x,3.207,z),r=.009)
box('GPU_Top_Cover',(-2.255,3.44,4.128),(1.47,.36,.045),M['trim'],.018)
perforated('GPU_Top_Vents',(-2.30,3.44,4.153),1.15,.24,32,7,M['mesh'],ratio=.26)
logo('GPU_Badge',(-1.60,3.208,4.057),.036)

# Perforated PSU deck and PCI slot covers, visible through the side glass.
box('PSU_Shroud',(-2.30,3.57,3.435),(1.67,.64,.135),M['trim'],.035)
box('Floor_Vent_Recess',(-2.29,3.57,3.506),(1.40,.47,.007),M['recess'],.01)
perforated('Floor_Mesh_Grille',(-2.29,3.57,3.515),1.37,.445,36,12,M['mesh'],ratio=.35)
for i in range(5):
    z=3.63+i*.097
    box(f'PCI_Slot_{i}',(-3.169,3.58,z),(.016,.43,.076),M['bracket'],.01)
    perforated(f'PCI_Perforations_{i}',(-3.154,3.58,z),.355,.053,12,2,M['mesh'],'X',.28)

# Rear I/O ports and fasteners make the model complete when orbiting around it.
box('Rear_IO_Plate',(-3.242,3.57,4.47),(.022,.36,.59),M['shell'],.018)
for i in range(3):
    y=3.49+(i%2)*.105;z=4.56-(i//2)*.12
    box(f'USB_Port_{i}',(-3.256,y,z),(.01,.063,.040),M['port'],.002)
    box(f'USB_Insert_{i}',(-3.263,y,z),(.006,.047,.013),M['detail'],.001)
box('HDMI_Port',(-3.259,3.495,4.70),(.010,.069,.033),M['port'],.003)
for i,(color,y) in enumerate([('#DC9FAB',3.48),('#A4CBAA',3.56),('#95B8D3',3.64)]):
    audio=mat(f'PC_Reference_Audio_{i}',color,.4)
    ring(f'Audio_Jack_{i}',(-3.264,y,4.285),.017,.006,audio,'X')
box('Power_Inlet_Frame',(-3.246,3.57,4.86),(.025,.27,.16),M['detail'],.015)
box('Power_Inlet',(-3.265,3.57,4.86),(.02,.18,.108),M['port'],.012)
for y in (3.28,3.86):
    for z in (3.44,4.90):screw(f'Rear_Case_Screw_{y}_{z}',(-3.24,y,z),'X',.016)

# Two discreet top ports and a glowing power-button ring.
for i,x in enumerate((-1.61,-1.51,-1.41)):
    box(f'Top_Port_{i}',(x,3.475,5.137),(.060,.017,.004),M['port'],.003)
disc('Power_Button',(-1.475,3.665,5.137),.038,.007,M['trim'],'Z')
ring('Power_Button_LED',(-1.475,3.665,5.141),.038,.0025,M['led'],'Z')
box('Top_LED_Diffuser',(-2.36,3.205,4.925),(1.33,.019,.014),M['led'],.006)
box('Bottom_LED_Diffuser',(-2.30,3.152,3.261),(1.13,.009,.014),M['led'],.006)
glass=mat('PC_Glass_Cool_Tint','#FCF8FF',.025)
p=next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.45
p.inputs['Specular IOR Level'].default_value=.16;p.inputs['Coat Weight'].default_value=0
# The broad pane has flat normals: interpolating bevel normals across a thin
# glass box produces spurious wedge-shaped highlights and bent refractions.
box('Glass_Panel',(-2.305,3.153,4.153),(1.758,.006,1.573),glass,0)

def area(name,pos,target,power,color,size):
    d=bpy.data.lights.new(PREFIX+name,'AREA');d.energy=power;d.color=rgba(color)[:3];d.shape='DISK';d.size=size
    o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    if name in ('Interior_Lilac','Rear_Fan_Bounce','Lower_Lilac'):
        o.visible_glossy=False;o.visible_transmission=False
    return o
area('Softbox_Key',(-2.95,1.7,6.0),(-2.25,3.55,4.2),80,'#FFF4EF',2.2)
area('Softbox_Front',(.1,2.0,5.0),(-1.8,3.5,4.3),50,'#F6EFFA',2.0)
area('Interior_Lilac',(-2.3,3.30,4.89),(-2.3,3.8,4.0),25,'#C994F6',.7)
area('Rear_Fan_Bounce',(-2.83,3.30,4.63),(-2.1,3.65,4.3),6,'#D2A5F5',.30)
area('Lower_Lilac',(-2.35,3.40,3.56),(-2.3,3.8,4.2),8,'#CEA5EE',.70)
point=bpy.data.objects.get('Point')
if point:point.data.energy=.5;point.data.color=rgba('#DDC4F5')[:3];point.data.shadow_soft_size=.25;point.location=(-2.2,3.55,4.3)
receivers=bpy.data.collections.new('PC Reference Light Receivers')
for o in col.objects:
    if o.type=='MESH':receivers.objects.link(o)
for o in list(col.objects)+([point] if point else []):
    if o.type=='LIGHT':o.light_linking.receiver_collection=receivers
# Only the HDR LED cores cross this threshold; the existing baked room
# surfaces remain below it. Keep the original compositor connection intact.
tree=scene.compositing_node_group
glow=tree.nodes.get('PC Reference LED Bloom')
if glow is None:
    glow=tree.nodes.new('CompositorNodeGlare');glow.name='PC Reference LED Bloom'
    link=next(l for l in tree.links if l.to_node.type=='GROUP_OUTPUT')
    source_socket=link.from_socket;target_socket=link.to_socket
    tree.links.new(source_socket,glow.inputs['Image'])
    tree.links.new(glow.outputs['Image'],target_socket)
glow.inputs['Type'].default_value='Fog Glow'
glow.inputs['Threshold'].default_value=2.0
glow.inputs['Strength'].default_value=.16
glow.inputs['Size'].default_value=.20
assert original==unrelated(),'Unrelated room object changed'
print('PC_STUDIO_BUILT',len(col.objects),flush=True)

def render():
    settings={p:getattr(scene.render,p) for p in ['engine','resolution_x','resolution_y','resolution_percentage','film_transparent','filepath']}
    cycles={p:getattr(scene.cycles,p) for p in ['samples','device','use_denoising','max_bounces']}
    hide={o:o.hide_render for o in bpy.data.objects};original_camera=scene.camera;original_world=scene.world
    temporary=[]
    room='--room' in sys.argv;front='--front' in sys.argv
    data=bpy.data.cameras.new('PC_Studio_Preview');camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera);temporary.append(camera)
    target=Vector((-2.27,3.57,4.12))
    offset=Vector((7,-9,2.6)) if not front else Vector((.5,-10,1.2))
    camera.location=target+offset;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=3.65 if room else 2.70
    if not room:
        for o in bpy.data.objects:
            if o.type=='MESH' and o not in col.objects.values():o.hide_render=True
        floor=box('Temporary_Studio_Floor',(-2.2,3.5,3.045),(200,200,.04),mat('PC_Studio_Ground','#C1BEC7',.82),.01);temporary.append(floor)
        w=bpy.data.worlds.new('PC_Studio_World');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.38,.38,.40,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.30;scene.world=w
        for name,pos,power,size in [('Studio_Key',(-4,-.5,7),260,4),('Studio_Rim',(0,5,6),240,3)]:
            temporary.append(area(name,pos,target,power,'#FFFFFF',size))
    try:
        if '--no-glass' in sys.argv:bpy.data.objects['PC_Reference_Glass_Panel'].hide_render=True
        scene.camera=camera;scene.render.engine='CYCLES';scene.render.resolution_x=1440 if FINAL else 960;scene.render.resolution_y=scene.render.resolution_x if not room else int(scene.render.resolution_x*.8);scene.render.resolution_percentage=100;scene.render.film_transparent=False
        scene.cycles.samples=144 if FINAL else 48;scene.cycles.use_denoising=True;scene.cycles.max_bounces=8
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='OPTIX'
        scene.cycles.device='GPU'
        label='room' if room else ('front' if front else 'hero')
        scene.render.filepath=str(OUT/f'pc-studio-{label}.png');bpy.ops.render.render(write_still=True)
    finally:
        for o in temporary:bpy.data.objects.remove(o,do_unlink=True)
        for o,v in hide.items():o.hide_render=v
        scene.world=original_world;scene.camera=original_camera
        for k,v in settings.items():setattr(scene.render,k,v)
        for k,v in cycles.items():setattr(scene.cycles,k,v)
if '--no-render' not in sys.argv:render()
assert original==unrelated()
report={'version':'studio-v2','refinement':'polish-v3','committed':COMMIT,'unrelated_room_unchanged':True,
        'mesh_count':sum(o.type=='MESH' for o in col.objects),'objects':sorted(o.name for o in col.objects),
        'led_objects':sorted(o.name for o in col.objects if o.type=='MESH' and any(m and m.name=='PC_LED_Lavender' for m in o.data.materials))}
(OUT/'studio-build-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if COMMIT:
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.object.select_all(action='DESELECT');base.select_set(True);bpy.context.view_layer.objects.active=base
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('PC_STUDIO_RESULT',json.dumps(report),flush=True)
