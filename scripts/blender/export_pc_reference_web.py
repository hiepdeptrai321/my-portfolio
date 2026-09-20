"""Bake the verified PC's diffuse lighting and export its web replacement.

Only the in-memory export copy is modified. The authoring blend and room
atlases are never saved or overwritten. Keep glass and LED cores separate.
"""
import bpy, json, hashlib, math, warnings
from pathlib import Path
warnings.filterwarnings('ignore', category=DeprecationWarning)

root=Path.cwd().resolve()
out=root/'artifacts/pc-reference-match'
source=Path(bpy.data.filepath)
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
scene=bpy.context.scene
case=bpy.data.objects['Plane.020_Baked']
collection=bpy.data.collections['PC Reference Match']
glass=bpy.data.objects['PC_Reference_Glass_Panel']
leds=[o for o in collection.objects if o.type=='MESH' and any(m and m.name=='PC_LED_Lavender' for m in o.data.materials)]
solids=[case]+[o for o in collection.objects if o.type=='MESH' and o not in [case,glass]+leds]
source_objects=sorted(o.name for o in solids+[glass]+leds)

bpy.ops.object.select_all(action='DESELECT')
for o in solids:
    bpy.context.view_layer.objects.active=o
    o.select_set(True)
    for modifier in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
    o.select_set(False)
for o in solids:o.select_set(True)
bpy.context.view_layer.objects.active=case
bpy.ops.object.join()
case.name='PC_Reference_Case_Replacement'
bpy.ops.object.material_slot_remove_unused()
assert all(m.name.startswith('PC_') for m in case.data.materials)

# Unwrap an export-only atlas after applying edge modifiers.
while case.data.uv_layers:case.data.uv_layers.remove(case.data.uv_layers[0])
case.data.uv_layers.new(name='PC_Baked_UV')
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(70),island_margin=.002,area_weight=.6)
bpy.ops.object.mode_set(mode='OBJECT')
atlas_size=4096 if collection.get('reference_version')=='studio-v2' else 2048
atlas=bpy.data.images.new('PC_Reference_Day_Lighting',width=atlas_size,height=atlas_size,alpha=False,float_buffer=True)
atlas.colorspace_settings.name='sRGB'
for m in case.data.materials:
    if m is None:continue
    # The unused original atlas material must not receive export-only nodes.
    if not m.name.startswith('PC_'):continue
    node=m.node_tree.nodes.new('ShaderNodeTexImage')
    node.image=atlas
    m.node_tree.nodes.active=node
    node.select=True
    # Cycles accumulates these contact rays over all 64 bake samples. Four
    # rays per hit keep the 4K bake practical without changing AO strength.
    for shader_node in m.node_tree.nodes:
        if shader_node.type=='AMBIENT_OCCLUSION':shader_node.samples=4

scene.render.engine='CYCLES'
scene.cycles.samples=64
scene.cycles.use_denoising=True
scene.cycles.max_bounces=6
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='OPTIX'
scene.cycles.device='GPU'
scene.render.bake.use_selected_to_active=False
scene.render.bake.margin=6
scene.render.bake.use_pass_direct=True
scene.render.bake.use_pass_indirect=True
scene.render.bake.use_pass_color=True
scene.render.bake.use_pass_emit=True
scene.render.bake.use_pass_diffuse=True
scene.render.bake.use_pass_glossy=False
scene.render.bake.use_pass_transmission=False
glass.hide_render=True
print('PC_WEB_BAKE_START',flush=True)
bpy.ops.object.bake(type='COMBINED')
texture_path=out/'pc-day-lighting.png'
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.image_settings.color_depth='8'
# Store AgX display colors, just like the existing baked room textures.
atlas.save_render(str(texture_path),scene=scene)

image=bpy.data.images.load(str(texture_path),check_existing=False)
image.name='PC_Reference_Day_Lighting_sRGB'
image.pack()
mat=bpy.data.materials.new('PC_Reference_Baked_Day')
mat.use_nodes=True
shader=mat.node_tree.nodes.get('Principled BSDF')
shader.inputs['Roughness'].default_value=.5
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
mat.node_tree.links.new(node.outputs['Color'],shader.inputs['Base Color'])
case.data.materials.clear();case.data.materials.append(mat)
for face in case.data.polygons:face.material_index=0
glass.hide_render=False
bpy.ops.object.select_all(action='DESELECT')
for o in [case,glass]+leds:o.select_set(True)
bpy.context.view_layer.objects.active=case
export=root/'public/models/pc-upgrade.glb'
bpy.ops.export_scene.gltf(filepath=str(export),export_format='GLB',use_selection=True,
    export_apply=True,export_materials='EXPORT',export_extras=True,
    export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,
    export_draco_position_quantization=16,export_draco_texcoord_quantization=16)
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
report={'source_blend':str(source),'source_sha256':source_hash,'source_unchanged':True,
        'source_meshes':source_objects,'export_meshes':[o.name for o in [case,glass]+leds],
        'export':str(export),'sha256':hashlib.sha256(export.read_bytes()).hexdigest(),
        'bytes':export.stat().st_size,'texture':str(texture_path),'texture_size':[atlas_size,atlas_size],
        'refinement':collection.get('refinement_version'),'uv_quantization_bits':16}
(out/'web-export-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PC_WEB_EXPORT',json.dumps(report),flush=True)
