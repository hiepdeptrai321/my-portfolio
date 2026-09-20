"""Visually inspect the actual GLB and its baked atlas, without a browser.

This is an unlit GLB preview; it does not reproduce WebGL glass or LED halos.
It checks exported geometry, UV packing and embedded texture colors.
"""
import bpy, warnings
from pathlib import Path
from mathutils import Vector
warnings.filterwarnings('ignore', category=DeprecationWarning)

root=Path.cwd().resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(root/'public/models/pc-upgrade.glb'))
scene=bpy.context.scene
for mat in bpy.data.materials:
    tree=mat.node_tree
    output=next(n for n in tree.nodes if n.type=='OUTPUT_MATERIAL')
    if mat.name=='PC_Glass_Cool_Tint':
        # The preview verifies the atlas through a completely clear pane.
        transparent=tree.nodes.new('ShaderNodeBsdfTransparent')
        tree.links.new(transparent.outputs[0],output.inputs['Surface'])
        continue
    emission=tree.nodes.new('ShaderNodeEmission')
    if mat.name=='PC_Reference_Baked_Day':
        image=next(n for n in tree.nodes if n.type=='TEX_IMAGE')
        tree.links.new(image.outputs['Color'],emission.inputs['Color'])
    else:
        emission.inputs['Color'].default_value=(.88,.68,1,1)
    tree.links.new(emission.outputs[0],output.inputs['Surface'])
camera_data=bpy.data.cameras.new('Export Preview')
camera=bpy.data.objects.new(camera_data.name,camera_data)
scene.collection.objects.link(camera)
target=Vector((-2.27,3.57,4.12))
camera.location=target+Vector((7,-9,2.6))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO';camera_data.ortho_scale=2.7
scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=32
scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='OPTIX'
scene.cycles.device='GPU'
scene.world=bpy.data.worlds.new('Preview Background');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.15,.14,.17,1)
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.render.resolution_x=1080;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(root/'artifacts/pc-reference-match/pc-web-export-preview.png')
bpy.ops.render.render(write_still=True)
