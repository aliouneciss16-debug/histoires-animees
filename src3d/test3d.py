import bpy, math, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=24; sc.cycles.use_denoising=True
try: sc.cycles.device='CPU'
except: pass
sc.render.resolution_x=540; sc.render.resolution_y=960
sc.render.filepath=sys.argv[-1]
sc.view_settings.view_transform='Standard'
def mat(c,r=0.5):
    m=bpy.data.materials.new("m"); m.use_nodes=True
    b=m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value=(*c,1); b.inputs["Roughness"].default_value=r
    return m
def sph(loc,sc_,c,r=0.5):
    bpy.ops.mesh.primitive_uv_sphere_add(location=loc,segments=48,ring_count=24); o=bpy.context.object
    o.scale=sc_; o.data.materials.append(mat(c,r)); bpy.ops.object.shade_smooth(); return o
def box(loc,sc_,c,r=0.7):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.scale=sc_; o.data.materials.append(mat(c,r))
    bev=o.modifiers.new("b","BEVEL"); bev.width=0.08; bev.segments=4; return o
# pièce
box((0,2,-0.1),(6,6,0.1),(0.55,0.36,0.22))
box((0,3.2,2),(6,0.1,2.2),(0.96,0.87,0.72))
box((-1.6,3.1,2.2),(1,0.05,0.9),(0.6,0.85,0.98),0.2)
box((1.5,3.1,2.0),(1.3,0.05,0.8),(0.1,0.1,0.14),0.2)
def person(x,s,skin,outfit,hair,face=True):
    sph((x,0,0.55*s+0.4),(0.45*s,0.3*s,0.6*s),outfit)
    sph((x,0,1.6*s+0.5),(0.4*s,0.38*s,0.44*s),skin)
    sph((x,0.02,1.82*s+0.5),(0.42*s,0.4*s,0.28*s),hair)
    for dx in (-0.14,0.14):
        sph((x+dx*s,-0.34*s,1.65*s+0.5),(0.09*s,0.04*s,0.1*s),(1,1,1),0.2)
        sph((x+dx*s,-0.38*s,1.65*s+0.5),(0.04*s,0.02*s,0.05*s),(0.05,0.03,0.02),0.2)
    sph((x,-0.38*s,1.5*s+0.5),(0.06*s,0.05*s,0.05*s),skin)
    sph((x,-0.34*s,1.38*s+0.5),(0.12*s,0.04*s,0.05*s),(0.5,0.1,0.12),0.3)
person(-1.5,1.0,(0.49,0.31,0.2),(0.17,0.44,0.75),(0.1,0.07,0.06))
person(-0.3,0.72,(0.52,0.34,0.23),(0.19,0.61,0.34),(0.1,0.07,0.06))
person(0.7,0.62,(0.6,0.4,0.27),(0.6,0.36,0.8),(0.1,0.07,0.06))
person(1.9,0.95,(0.56,0.37,0.25),(0.92,0.64,0.17),(0.84,0.26,0.46))
box((0,-0.65,0.35),(3.6,0.5,0.45),(0.78,0.38,0.22),0.6)
box((0,-0.25,0.55),(3.6,0.15,0.8),(0.7,0.32,0.18),0.6) if False else None
# lumières
bpy.ops.object.light_add(type='AREA',location=(0,-3,5)); l=bpy.context.object; l.data.energy=500; l.data.size=5
bpy.ops.object.light_add(type='AREA',location=(-3,-2,3)); l=bpy.context.object; l.data.energy=300; l.data.size=3
w=bpy.data.worlds.new("w"); w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.9,0.85,0.8,1); w.node_tree.nodes["Background"].inputs[1].default_value=0.6; sc.world=w
bpy.ops.object.camera_add(location=(0,-9.5,2.4),rotation=(math.radians(86),0,0)); cam=bpy.context.object; cam.data.lens=26; sc.camera=cam
bpy.ops.render.render(write_still=True)
