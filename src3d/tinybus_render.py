"""TINY BUS ADVENTURES : scène Blender (bpy). Usage :
python tinybus_render.py <mouth.json> <outdir> <first_frame> <last_frame> [--still t out.png]
Rendu à 12 images/s (dessin animé « on twos »), dupliquées ensuite à 30 fps par ffmpeg."""
import bpy, math, json, sys, os
from mathutils import Vector

RFPS = 10
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
MOUTH = json.load(open(args[0]))
OUTDIR = args[1]
STILL = None
if "--still" in args:
    i = args.index("--still"); STILL = (float(args[i + 1]), args[i + 2])
RES = (360, 640)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 8
sc.cycles.max_bounces = 3
sc.cycles.diffuse_bounces = 2
sc.cycles.glossy_bounces = 2
sc.cycles.transmission_bounces = 0
sc.cycles.caustics_reflective = False
sc.cycles.caustics_refractive = False
sc.cycles.use_denoising = True
sc.cycles.device = 'CPU'
sc.render.threads_mode = 'FIXED'; sc.render.threads = 1
sc.render.resolution_x, sc.render.resolution_y = RES
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'


def col(h):
    h = h.lstrip('#'); r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c ** 2.2
    return (f(r), f(g), f(b))


_mats = {}
def mat(hexc, rough=0.45, emit=0.0):
    k = (hexc, rough, emit)
    if k in _mats: return _mats[k]
    m = bpy.data.materials.new(hexc); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col(hexc), 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*col(hexc), 1); b.inputs["Emission Strength"].default_value = emit
    _mats[k] = m
    return m


def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(o)
    o.location = loc
    if parent: o.parent = parent
    return o


def sph(name, loc, scl, hexc, parent=None, rough=0.45, emit=0.0, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 0), segments=seg, ring_count=seg // 2)
    o = bpy.context.object; o.name = name; o.scale = scl
    o.data.materials.append(mat(hexc, rough, emit)); bpy.ops.object.shade_smooth()
    if parent: o.parent = parent
    o.location = loc
    return o


def box(name, loc, scl, hexc, rough=0.5, bevel=0.06, parent=None):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); o = bpy.context.object; o.name = name; o.scale = scl
    o.data.materials.append(mat(hexc, rough))
    bv = o.modifiers.new("b", "BEVEL"); bv.width = bevel; bv.segments = 4
    if parent: o.parent = parent
    o.location = loc
    return o


def cyl(name, loc, r, h, hexc, rough=0.4, emit=0.0, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(location=(0, 0, 0), radius=r, depth=h, vertices=48)
    o = bpy.context.object; o.name = name; o.data.materials.append(mat(hexc, rough, emit)); bpy.ops.object.shade_smooth()
    if parent: o.parent = parent
    o.location = loc
    return o


def torus(name, loc, R, r, hexc, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0), major_radius=R, minor_radius=r, major_segments=64, minor_segments=16)
    o = bpy.context.object; o.name = name; o.data.materials.append(mat(hexc, 0.4)); bpy.ops.object.shade_smooth()
    o.rotation_euler = rot
    if parent: o.parent = parent
    o.location = loc
    return o


# ---------------- décor : l'intérieur de Sunny ----------------
box("floor", (0, 0, -0.1), (5, 5, 0.1), "#c98a4b")
box("wallL", (-3.6, 0.5, 2.5), (0.1, 3.5, 3.5), "#ffd23a")
box("wallR", (3.6, 0.5, 2.5), (0.1, 3.5, 3.5), "#ffd23a")
box("ceiling", (0, 0.5, 5.6), (5, 3.5, 0.15), "#ffdb5c")
# pare-brise
sky = box("sky", (0, 3.1, 2.6), (3.4, 0.05, 3.2), "#8fd3ff", rough=1.0, bevel=0.0)
sky.data.materials[0] = mat("#8fd3ff", 1.0, 1.4)
for nm, (x, z, sx, sz) in dict(top=(0, 5.65, 3.5, 0.18), bot=(0, -0.35, 3.5, 0.2), l=(-3.5, 2.6, 0.18, 3.2), r=(3.5, 2.6, 0.18, 3.2), mid=(0, 2.6, 0.1, 3.2)).items():
    box("frame_" + nm, (x, 2.95, z), (sx, 0.12, sz), "#ffcc19")
# yeux de Sunny au-dessus du pare-brise
SUN = {}
for s, x in (("L", -1.0), ("R", 1.0)):
    e = empty("sunny_eye" + s, (x, 2.75, 4.95))
    sph("sw" + s, (0, 0, 0), (0.62, 0.15, 0.62), "#ffffff", e, 0.2)
    p = sph("sp" + s, (0, -0.14, 0), (0.28, 0.08, 0.34), "#1d1209", e, 0.2)
    sph("sh" + s, (0.08, -0.2, 0.1), (0.07, 0.03, 0.07), "#ffffff", e, 0.2)
    lid = sph("sl" + s, (0, -0.02, 0.0), (0.66, 0.17, 0.66), "#ffd23a", e, 0.5)
    SUN[s] = (e, p, lid)
# tableau de bord (devant les personnages)
dash = box("dash", (0, -1.2, -1.3), (3.6, 0.85, 1.9), "#ffbf1a", 0.45, 0.12)
box("dashtop", (0, -1.2, 0.62), (3.6, 0.85, 0.07), "#e9a30c", 0.5, 0.05)
wheel = torus("wheel", (-2.5, -1.28, 0.9), 0.55, 0.09, "#2b2b35", rot=(math.radians(65), 0, 0))
cyl("wheelpost", (-2.5, -1.2, 0.55), 0.1, 0.5, "#2b2b35")
# bouton rouge principal
def make_button(name, x, size, glow=True):
    base = cyl(name + "_base", (x, -1.1, 0.74), size * 1.35, 0.1, "#3a3a44", 0.3)
    dome = sph(name + "_dome", (x, -1.1, 0.8), (size, size, size * 0.7), "#ff1f1f", None, 0.15, emit=2.0)
    return base, dome
B1 = make_button("b1", 0.4, 0.42)
B2 = make_button("b2", -2.0, 0.3)
# petites lumières du tableau de bord
LEDS = []
for i, (x, c) in enumerate([(-1.2, "#3cff7a"), (-0.8, "#3aa8ff"), (1.3, "#ffe03a"), (1.7, "#ff3ad1"), (2.1, "#3cff7a"), (2.5, "#3aa8ff")]):
    LEDS.append(sph("led%d" % i, (x, -1.55, 0.3), (0.12, 0.05, 0.12), c, None, 0.3, emit=0.3))
for i in range(5):
    box("dial%d" % i, (-1.6 + i * 0.35, -2.07, -0.6), (0.14, 0.03, 0.14), "#ffe9a0", 0.4, 0.02)
# nuages et arc-en-ciel (décor derrière le pare-brise)
CLOUDS = []
for i in range(9):
    g = empty("cloud%d" % i, (0, 2.9, 0))
    for j, (dx, dz, s) in enumerate([(0, 0, 0.55), (0.55, -0.1, 0.42), (-0.5, -0.1, 0.4), (0.2, 0.3, 0.38)]):
        sph("cl%d_%d" % (i, j), (dx, 0, dz), (s * 1.2, s * 0.5, s * 0.7), "#ffffff", g, 1.0, emit=0.8)
    CLOUDS.append(g)
BIG = empty("bigcloud", (0, 2.7, -0.6))
for j, (dx, dz, s) in enumerate([(0, 0, 1.6), (1.4, -0.2, 1.2), (-1.4, -0.2, 1.2), (0.6, 0.5, 1.0), (-0.7, 0.5, 1.0), (2.2, -0.3, 0.9), (-2.2, -0.3, 0.9)]):
    sph("bc%d" % j, (dx, 0, dz), (s * 1.1, s * 0.6, s * 0.7), "#ffffff", BIG, 1.0, emit=0.9)
RAIN = empty("rainbow", (0, 2.9, 0.4))
for i, c in enumerate(["#ff3b3b", "#ff9a2e", "#ffe03a", "#3cd35a", "#3a9bff", "#8a4bff"]):
    torus("rb%d" % i, (0, 0, 0), 3.0 - i * 0.2, 0.11, c, RAIN, rot=(math.radians(90), 0, 0)).data.materials[0] = mat(c, 0.5, 0.7)
SPARK = [sph("spk%d" % i, (0, 2.0, 0), (0.1, 0.1, 0.1), "#fff6a8", None, 0.3, emit=3.0, seg=12) for i in range(14)]

# ---------------- personnages ----------------
CH = {}


def eyes(head, hexiris, xs=0.2, y=-0.43, z=0.08, r=0.15):
    out = []
    for s in (-1, 1):
        w = sph("ew", (s * xs, y, z), (r, r * 0.55, r * 1.15), "#ffffff", head, 0.2)
        ir = sph("ei", (s * xs, y - 0.07, z), (r * 0.72, r * 0.4, r * 0.85), hexiris, head, 0.2)
        sph("ep", (s * xs, y - 0.1, z), (r * 0.36, r * 0.25, r * 0.45), "#150d08", head, 0.2)
        sph("eh", (s * xs + r * 0.2, y - 0.13, z + r * 0.25), (r * 0.17, r * 0.1, r * 0.17), "#ffffff", head, 0.2)
        lid = sph("lid", (s * xs, y + 0.0, z), (r * 1.05, r * 0.6, r * 1.2), "#000000", head, 0.5)
        lid.hide_render = True
        out.append((w, ir, lid))
    return out


def brows(head, hexc, xs=0.2, y=-0.42, z=0.34):
    out = []
    for s in (-1, 1):
        b = sph("brow", (s * xs, y, z), (0.13, 0.04, 0.035), hexc, head, 0.5, seg=12)
        out.append(b)
    return out


def arm(root, side, hexc, handc):
    sh = empty("sh", (side * 0.55, 0.0, 0.1), root)
    sph("arm", (0, 0, -0.3), (0.13, 0.13, 0.34), hexc, sh)
    sph("hand", (0, 0, -0.64), (0.15, 0.15, 0.15), handc, sh)
    return sh


def character(name, x, kind):
    root = empty(name, (x, 0.0, 0.35))
    if kind == "bobo":
        fur, face, inner, iris = "#7a4a26", "#f3d9a8", "#f3d9a8", "#e8a020"
        body = sph("body", (0, 0, 0.35), (0.58, 0.5, 0.6), fur, root)
        sph("belly", (0, -0.3, 0.3), (0.38, 0.22, 0.42), face, root)
        head = empty("head", (0, 0, 1.2), root)
        sph("skull", (0, 0, 0), (0.62, 0.55, 0.55), fur, head)
        sph("facepatch", (0, -0.28, -0.05), (0.46, 0.3, 0.4), face, head)
        for s in (-1, 1):
            sph("ear", (s * 0.66, 0, 0.02), (0.22, 0.12, 0.22), fur, head)
            sph("earin", (s * 0.68, -0.07, 0.02), (0.14, 0.06, 0.14), "#f0b99a", head)
        sph("nose", (0, -0.55, -0.05), (0.06, 0.04, 0.045), "#4a2a14", head)
        neck = torus("neck", (0, 0, 0.95), 0.34, 0.1, "#ff8a1a", root); neck.rotation_euler = (0, 0, 0)
        sph("kerch", (0, -0.34, 0.8), (0.2, 0.08, 0.18), "#ff8a1a", root)
        eyef = eyes(head, iris, 0.2, -0.45, 0.1, 0.17); br = brows(head, "#4a2a14", 0.2, -0.43, 0.36)
        L, R = arm(root, -1, fur, face), arm(root, 1, fur, face)
        mz = (0, -0.5, -0.22); tail = None
    elif kind == "bobby":
        fur, face, iris = "#c98a3d", "#fff0cf", "#6b3f1f"
        body = sph("body", (0, 0, 0.35), (0.56, 0.5, 0.58), fur, root)
        sph("belly", (0, -0.3, 0.28), (0.34, 0.2, 0.4), face, root)
        head = empty("head", (0, 0, 1.2), root)
        sph("skull", (0, 0, 0), (0.6, 0.55, 0.54), fur, head)
        sph("muzzle", (0, -0.36, -0.14), (0.3, 0.26, 0.2), face, head)
        sph("nose", (0, -0.6, -0.08), (0.1, 0.06, 0.07), "#1a1210", head)
        for s in (-1, 1):
            e = sph("ear", (s * 0.58, -0.02, -0.12), (0.18, 0.1, 0.38), "#8a5624", head)
            e.rotation_euler = (0, math.radians(s * -18), 0)
        torus("collar", (0, 0, 0.9), 0.36, 0.09, "#2a7bff", root)
        sph("tag", (0, -0.4, 0.78), (0.09, 0.03, 0.09), "#ffe14a", root, 0.2)
        eyef = eyes(head, iris, 0.2, -0.46, 0.1, 0.17); br = brows(head, "#8a5624", 0.2, -0.44, 0.36)
        L, R = arm(root, -1, fur, face), arm(root, 1, fur, face)
        mz = (0, -0.56, -0.28)
    else:
        fur, face, iris = "#9aa3ad", "#ffffff", "#2ec27e"
        body = sph("body", (0, 0, 0.35), (0.5, 0.46, 0.56), fur, root)
        sph("belly", (0, -0.28, 0.28), (0.3, 0.2, 0.38), face, root)
        head = empty("head", (0, 0, 1.18), root)
        sph("skull", (0, 0, 0), (0.58, 0.53, 0.5), fur, head)
        sph("muzzle", (0, -0.35, -0.13), (0.26, 0.2, 0.17), face, head)
        sph("nose", (0, -0.52, -0.05), (0.06, 0.04, 0.045), "#ff8fb0", head)
        for s in (-1, 1):
            e = sph("ear", (s * 0.36, 0.0, 0.5), (0.2, 0.08, 0.28), fur, head)
            e.rotation_euler = (0, math.radians(s * 18), 0)
            sph("earin", (s * 0.36, -0.06, 0.48), (0.12, 0.04, 0.18), "#ff9fbf", head).rotation_euler = (0, math.radians(s * 18), 0)
            for k in (-1, 1):
                w = box("whisk", (s * 0.42, -0.45, -0.1 + k * 0.05), (0.2, 0.008, 0.008), "#ffffff", 0.5, 0.0, head)
                w.rotation_euler = (0, math.radians(k * s * 12), 0)
        torus("collar", (0, 0, 0.9), 0.33, 0.09, "#9a4bff", root)
        eyef = eyes(head, iris, 0.2, -0.44, 0.1, 0.17); br = brows(head, "#6c747d", 0.2, -0.42, 0.36)
        L, R = arm(root, -1, fur, face), arm(root, 1, fur, face)
        mz = (0, -0.52, -0.22)
    mouth = sph("mouth", mz, (0.12, 0.04, 0.03), "#6a1020", head, 0.3, seg=20)
    CH[name] = dict(root=root, head=head, body=body, eyes=eyef, brows=br, L=L, R=R, mouth=mouth, mz=mz)


character("mimi", -0.85, "mimi")
character("bobo", 0.4, "bobo")
character("bobby", 1.55, "bobby")

# ---------------- lumières, caméra ----------------
def light(kind, loc, energy, size=3.0, color=(1, 1, 1)):
    bpy.ops.object.light_add(type=kind, location=loc)
    l = bpy.context.object; l.data.energy = energy; l.data.color = color
    if kind == 'AREA': l.data.size = size
    return l
light('AREA', (0, -6, 6), 900, 6)
light('AREA', (-4, -3, 3), 300, 4)
light('POINT', (0.4, -1.5, 1.4), 40, color=(1, 0.2, 0.2))
REDL = bpy.context.object
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 0.95, 0.85, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.55
sc.world = w
bpy.ops.object.camera_add(location=(0, -6.5, 1.6)); CAM = bpy.context.object; sc.camera = CAM
TGT = empty("tgt", (0, 0, 1.2))
tc = CAM.constraints.new('TRACK_TO'); tc.target = TGT; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'


# ---------------- animation ----------------
def hide(o, v):
    o.hide_render = v
    for c in o.children_recursive: c.hide_render = v


def sm(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def K(t, pts):
    """interpolation douce entre (temps, valeur) ; valeurs numériques ou tuples."""
    if t <= pts[0][0]: return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1:
            k = sm((t - t0) / (t1 - t0) if t1 > t0 else 1)
            if isinstance(v0, (tuple, list)): return tuple(a + (b - a) * k for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * k
    return pts[-1][1]


EMO = {  # (inclinaison sourcils, hauteur sourcils, ouverture yeux, bouche min, bouche large)
    "neutral": (0, 0.0, 1.0, 0.05, 1.0),
    "curious": (-8, 0.05, 1.1, 0.12, 0.8),
    "worry": (20, 0.04, 1.15, 0.08, 1.2),
    "smirk": (-14, 0.0, 0.65, 0.25, 1.5),
    "scared": (22, 0.1, 1.35, 0.5, 1.0),
    "joy": (-6, 0.08, 0.8, 0.45, 1.7),
    "wow": (0, 0.14, 1.4, 0.6, 0.9),
    "stern": (-24, 0.0, 0.9, 0.05, 0.9),
}
EMOT = {  # chronologie des émotions par personnage
    "bobo": [(0, "neutral"), (3.2, "curious"), (6, "smirk"), (9, "smirk"), (12, "joy"), (15, "joy"), (21, "wow"), (24.5, "smirk"), (28, "smirk")],
    "mimi": [(0, "neutral"), (3, "worry"), (6, "stern"), (9, "worry"), (12, "scared"), (15, "scared"), (21, "wow"), (25, "stern"), (28, "worry")],
    "bobby": [(0, "neutral"), (6, "curious"), (12, "curious"), (15, "scared"), (18, "scared"), (21, "wow"), (25, "worry"), (28, "worry")],
}


def emo_at(name, t):
    seq = EMOT[name]; cur = seq[0]; nxt = None
    for i, e in enumerate(seq):
        if t >= e[0]: cur = e; nxt = seq[i + 1] if i + 1 < len(seq) else None
    a = EMO[cur[1]]
    if nxt:
        k = sm((t - cur[0]) / max(0.001, min(0.5, nxt[0] - cur[0]))) if t - cur[0] < 0.5 else 1.0
    return a


def mouth_amt(name, t):
    arr = MOUTH.get(name, [])
    i = int(t * RFPS)
    return arr[i] if 0 <= i < len(arr) else 0.0


def pose(t):
    # ---- caméra ----
    cam_pts = [(0, (0.4, -2.6, 1.05)), (2.4, (0.4, -2.2, 1.0)), (3.0, (0.35, -5.0, 1.55)), (21, (0.35, -5.0, 1.55)), (21.6, (0.35, -4.7, 1.55)),
               (25.2, (0.35, -4.9, 1.55)), (27.6, (0.3, -4.0, 1.5)), (28.3, (0.4, -2.8, 1.1)), (30, (0.4, -2.2, 1.0))]
    tgt_pts = [(0, (0.4, -1.1, 0.75)), (3.0, (0.35, 0, 1.25)), (27.6, (0.3, 0, 1.2)), (28.3, (0.4, -1.1, 0.75)), (30, (0.4, -1.1, 0.75))]
    cp = K(t, cam_pts); tp = K(t, tgt_pts)
    shake = 0.0
    if 15.0 <= t < 21.0: shake = 0.07 * (1 if t < 20 else max(0, 21 - t))
    if 12.4 <= t < 12.8: shake = 0.05
    CAM.location = (cp[0] + shake * math.sin(t * 47), cp[1], cp[2] + shake * math.cos(t * 53))
    TGT.location = tp
    CAM.data.lens = 24 if 2.9 < t < 27.8 else 38
    # ---- bouton ----
    pressed = sm((t - 12.2) / 0.15) * (1 - sm((t - 12.7) / 0.15))
    glow = 2.0 + 1.2 * math.sin(t * 9) if t < 12.2 or t > 13.5 else 5.0
    B1[1].location.z = 0.8 - 0.12 * pressed
    B1[1].data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = glow
    B2[1].data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = (2.0 + math.sin(t * 8)) if t > 24.5 else 0.0
    B2[0].hide_render = B2[1].hide_render = t < 24.5
    REDL.data.energy = 40 + 25 * math.sin(t * 9) + (200 if 12.2 < t < 13.5 else 0)
    for i, led in enumerate(LEDS):
        on = (12.3 < t < 15.5 and int(t * 10 + i) % 2 == 0) or (t < 12.2 and (i % 2 == 0))
        led.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 6.0 if on else 0.2
    # ---- ciel / vol / arc-en-ciel ----
    flying = 12.7 <= t < 21.2
    for i, c in enumerate(CLOUDS):
        sp = 2.0 if flying else 0.0
        if flying:
            speed = 14 + i * 2
            z = -0.5 + (i * 0.9) % 6.4
            ph = ((t - 12.7) * speed * 0.35 + i * 1.3) % 10
            c.location = (-5 + ph, 2.85, z + 0.1 * math.sin(t * 3 + i))
            hide(c, t < 12.7 or t > 21.2 or z > 4.2)
            c.scale = (1.3, 1, 1.0)
        else:
            hide(c, not (t < 12.7))
            if t < 12.7:
                c.location = (-3.2 + (i * 1.45) % 7, 2.85, 0.3 + (i * 0.8) % 5.0 + 0.05 * math.sin(t + i)); c.scale = (1, 1, 1)
            if t > 21.2: hide(c, True)
    land = sm((t - 20.6) / 0.9)
    hide(BIG, t < 20.6); hide(RAIN, t < 20.6)
    bounce = 0.18 * math.sin((t - 21.5) * 7) * math.exp(-(t - 21.5) * 1.6) if t > 21.5 else 0
    BIG.location = (0, 2.7, -0.6 - 2.4 * (1 - land) + bounce * 0.5)
    RAIN.location = (0, 2.95, 0.4 - 2 * (1 - land))
    for i, s in enumerate(SPARK):
        on = 21.5 < t < 25.2
        s.hide_render = not on
        if on:
            a = i * 2.4 + t * 1.5
            s.location = (-2.6 + (i * 0.43) % 5.2, 2.4, 1.2 + (i * 0.37 + t * 0.8) % 3.6)
            k = 0.08 + 0.07 * (0.5 + 0.5 * math.sin(t * 8 + i)); s.scale = (k, k, k)
    # ---- yeux de Sunny ----
    blink = 1.0 if (t % 3.7) > 0.15 else 0.2
    look = (-0.1 if t < 3 else (0.0 if t < 12 else 0.12 * math.sin(t * 2)))
    wide = 1.0 + (0.25 if 15 < t < 21 or 24.5 < t < 26 else 0)
    for s, (e, p, lid) in SUN.items():
        e.scale = (wide, 1, wide * blink if blink < 1 else wide)
        p.location = (look + (0.05 if s == "L" else -0.05), -0.14, 0)
        lid.hide_render = True
    # ---- personnages ----
    tilt = {"mimi": 0, "bobo": 0, "bobby": 0}
    for name, c in CH.items():
        tt, hh, ee, mmin, mw = emo_at(name, t)
        sgn = 1 if name != "mimi" else -1
        for b, s in zip(c["brows"], (-1, 1)):
            b.rotation_euler = (0, math.radians(tt * s * -1), 0); b.location.z = 0.34 + hh
        blk = ((t + {"mimi": 0.7, "bobo": 1.9, "bobby": 2.8}[name]) % 3.3) < 0.13
        for (w_, ir, lid) in c["eyes"]:
            sc_ = 0.15 if blk else ee
            for o in (w_, ir): o.scale.z = o.scale.z if False else o.scale.z
            lid.hide_render = True
        # ouverture des yeux : échelle verticale de la tête des yeux via le parent (simple : scale des blancs)
        for (w_, ir, lid) in c["eyes"]:
            base = 0.17 * 1.15
            w_.scale = (0.17, 0.17 * 0.55, base * (0.12 if blk else ee))
            ir.scale = (0.17 * 0.72, 0.17 * 0.4, 0.17 * 0.85 * (0.12 if blk else min(ee, 1.2)))
        m = max(mmin * 0.6, mouth_amt(name, t))
        c["mouth"].scale = (0.12 * mw * (1 + 0.15 * m), 0.04, 0.03 + 0.16 * m)
        c["mouth"].location = (0, c["mz"][1], c["mz"][2] - 0.05 * m)
        c["root"].location.z = 0.35 + 0.025 * math.sin(t * 2.2 + len(name))
        c["head"].rotation_euler = (0, 0, 0)
        c["L"].rotation_euler = (0, 0, math.radians(8)); c["R"].rotation_euler = (0, 0, math.radians(-8))
        c["root"].rotation_euler = (0, 0, 0)
        c["root"].location.y = 0.0
    bobo, mimi, bobby = CH["bobo"], CH["mimi"], CH["bobby"]
    # S2 : Bobo se penche vers le bouton
    lean = K(t, [(3.0, 0), (4.2, 1), (6.0, 1), (7, 0.3), (9, 0.8), (12.2, 1.0), (12.8, 0.2), (14.5, 0)])
    bobo["root"].location.y = -0.3 * lean
    bobo["head"].rotation_euler = (math.radians(-18 * lean), 0, math.radians(7 * math.sin(t * 1.5)))
    # S3 : Mimi lève la patte
    up = K(t, [(5.6, 0), (6.4, 1), (8.2, 1), (9, 0.2), (12, 0.2), (12.4, 1), (13.5, 0.6)])
    mimi["R"].rotation_euler = (math.radians(-80 * up), 0, math.radians(-8 - 40 * up))
    mimi["head"].rotation_euler = (0, 0, math.radians(-8 * up))
    mimi["root"].location.y = -0.15 * up
    # S4-5 : le doigt de Bobo vers le bouton ; appui
    reach = K(t, [(9.6, 0), (11.6, 0.9), (12.2, 1.0), (12.7, 0.9), (13.4, 0.0)])
    bobo["R"].rotation_euler = (math.radians(-62 * reach), 0, math.radians(-14 + 12 * reach))
    bobo["R"].location.z = 0.1
    # S6 : vol, tous secoués
    if 15 <= t < 21.2:
        w_ = min(1, (t - 15) / 0.5)
        for nm, ph in (("bobo", 0), ("mimi", 1.1), ("bobby", 2.2)):
            c = CH[nm]
            c["root"].location.z = 0.35 + 0.12 * w_ * abs(math.sin(t * 6 + ph))
            c["root"].rotation_euler = (0, math.radians(7 * w_ * math.sin(t * 5 + ph)), math.radians(5 * w_ * math.sin(t * 4 + ph)))
        bobby["L"].rotation_euler = (0, 0, math.radians(100 + 20 * math.sin(t * 9))); bobby["R"].rotation_euler = (0, 0, math.radians(-100 - 20 * math.sin(t * 9)))
        mimi["L"].rotation_euler = (math.radians(-70), 0, math.radians(20)); mimi["R"].rotation_euler = (math.radians(-70), 0, math.radians(-20))
        bobo["L"].rotation_euler = (0, 0, math.radians(120 + 15 * math.sin(t * 8))); bobo["R"].rotation_euler = (0, 0, math.radians(-120 - 15 * math.sin(t * 8)))
    # S7 : « WOW » bras en l'air
    if 21.2 <= t < 24.6:
        j = sm((t - 21.2) / 0.3)
        for nm in ("bobo", "mimi", "bobby"):
            c = CH[nm]
            c["L"].rotation_euler = (0, 0, math.radians(150 * j)); c["R"].rotation_euler = (0, 0, math.radians(-150 * j))
            c["root"].location.z = 0.35 + 0.18 * abs(math.sin((t - 21.2) * 5)) * math.exp(-(t - 21.2) * 0.5)
    # S8 : Bobo découvre le 2e bouton, Mimi proteste
    pt = K(t, [(24.6, 0), (25.2, 1), (27.5, 1), (28.0, 0)])
    if t >= 24.6:
        bobo["L"].rotation_euler = (math.radians(-25 * pt), 0, math.radians(8 + 80 * pt))
        bobo["head"].rotation_euler = (0, 0, math.radians(12 * pt))
        mimi["R"].rotation_euler = (math.radians(-40 * pt), 0, math.radians(-12 - 55 * pt))
        mimi["root"].location.y = -0.1 * pt
    # S9 : regard caméra, doigt vers le bouton
    if t >= 27.6:
        a = sm((t - 27.6) / 1.0)
        bobo["head"].rotation_euler = (math.radians(-10 * a), 0, 0)
        bobo["R"].rotation_euler = (math.radians(-60 * a), 0, math.radians(-14 + 8 * a))
        bobo["L"].rotation_euler = (0, 0, math.radians(8))
        bobo["root"].location.y = -0.3 * a


def render_frame(n, path):
    t = n / RFPS
    pose(t)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


if STILL:
    pose(STILL[0]); sc.render.filepath = STILL[1]; bpy.ops.render.render(write_still=True)
else:
    a, b = int(args[2]), int(args[3])
    os.makedirs(OUTDIR, exist_ok=True)
    for n in range(a, b + 1):
        p = os.path.join(OUTDIR, "f_%04d.png" % n)
        if os.path.exists(p): continue
        render_frame(n, p)
