"""Concept v2 renders (Louis 2026-11-13: "too chunky, colours not good, mono natural metallic, modern, not tons of buttons, smooth").
1 Blender unit = 1 cm.  Run:  blender -b -P render_v2.py -- <view: hero|back|side|front> <abs out.png>
48 x 94 x 12 mm natural bead-blasted aluminium unibody (sides + back), soft fully rounded edges, one black glass front
with a 1.8" AMOLED in the upper half and ONE round Talk button below it. Left: volume rocker. Right: one small key.
Back: camera only. Bottom end: USB-C, speaker slots, mic. Antennas sit under the glass top/bottom bands."""
import bpy, bmesh, math, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VIEW, OUT = (argv + ["hero", os.path.join(HERE, "render.png")][len(argv):])[:2]
UI = os.path.join(HERE, "..", "..", "voice-device", "enclosure", "ui_listening.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
W, H, T, RAD = 4.8, 9.4, 1.2, 0.95

def mat(name, base, metal=0.0, rough=0.4, coat=0.0, emit_img=None, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1); p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough; p.inputs["Coat Weight"].default_value = coat
    if emit_img:
        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(emit_img)
        nt.links.new(tex.outputs["Color"], p.inputs["Emission Color"])
        nt.links.new(tex.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Emission Strength"].default_value = emit
    return m

alu = mat("alu_blasted", (0.80, 0.80, 0.81), metal=1.0, rough=0.34)
alu_pol = mat("alu_polished", (0.93, 0.93, 0.94), metal=1.0, rough=0.06)
glass = mat("glass", (0.003, 0.003, 0.004), rough=0.015, coat=1.0)
screen = mat("screen", (0, 0, 0), rough=0.05, emit_img=UI, emit=3.0)
hole = mat("hole", (0.0, 0.0, 0.0), rough=0.9)
lens = mat("lens", (0.01, 0.012, 0.03), metal=0.3, rough=0.03, coat=1.0)

def rrect(w, h, r, n=28):
    pts = []
    for cx, cy, a0 in [(w/2-r, h/2-r, 0), (-w/2+r, h/2-r, 90), (-w/2+r, -h/2+r, 180), (w/2-r, -h/2+r, 270)]:
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def slab(name, w, h, r, depth, z0, material, bevel=0.0, seg=1, x=0, y=0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((px, py, z0)) for px, py in rrect(w, h, r)]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]: v.co.z += depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); ob.location = (x, y, 0)
    for p in me.polygons: p.use_smooth = True
    if bevel:
        bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = bevel; bv.segments = seg
        bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(40); bv.profile = 0.5
    ob.modifiers.new("wn", "WEIGHTED_NORMAL")
    ob.data.materials.append(material); return ob

def pill(name, sx, sy, sz, loc, material, rnd=0.48, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); ob = bpy.context.object; ob.name = name
    ob.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True)
    bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = min(sx, sy, sz) * rnd; bv.segments = 10
    bpy.ops.object.shade_smooth(); ob.data.materials.append(material)
    if rot: ob.rotation_euler = rot
    return ob

def disc(name, r, depth, loc, material, verts=128, rot=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc)
    ob = bpy.context.object; ob.name = name; bpy.ops.object.shade_smooth(); ob.data.materials.append(material)
    if rot: ob.rotation_euler = rot
    return ob

dev = []
# body: soft, fully rounded sides (big round bevel on both long edges loops)
dev.append(slab("body", W, H, RAD, T - 0.07, 0, alu, bevel=0.42, seg=16))
# polished hairline ring where the glass meets the metal
dev.append(slab("ring", W - 0.80, H - 0.80, RAD - 0.40, 0.02, T - 0.085, alu_pol, bevel=0.008, seg=2))
# one glass front, 2.5D edge
dev.append(slab("glass", W - 0.84, H - 0.84, RAD - 0.42, 0.075, T - 0.08, glass, bevel=0.05, seg=8))
sy = H / 2 - 1.0 - 2.06
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, sy, T + 0.0006)); scr = bpy.context.object
scr.scale = (2.87, 3.49, 1); scr.data.materials.append(screen); dev.append(scr)
dev.append(pill("earpiece", 0.9, 0.06, 0.01, (0, H / 2 - 0.62, T - 0.003), hole, rnd=0.49))
# the one front button: Talk (machined aluminium, polished ring, sits flush)
by = -H / 2 + 2.25
dev.append(disc("talk_ring", 0.66, 0.02, (0, by, T - 0.002), alu_pol))
dev.append(disc("talk", 0.6, 0.03, (0, by, T + 0.0), alu))
# sides: left volume rocker, right one small key
zc = T * 0.5
dev.append(pill("rocker", 0.09, 1.7, 0.34, (-W / 2 + 0.005, 1.6, zc), alu))
dev.append(pill("side_key", 0.09, 0.75, 0.34, (W / 2 - 0.005, 1.9, zc), alu))
# bottom end: USB-C, speaker slots, mic
rx = (math.radians(90), 0, 0)
dev.append(pill("usbc", 0.88, 0.1, 0.3, (0, -H / 2 + 0.035, zc), hole))
for i in range(5):
    for sgn in (-1, 1):
        dev.append(disc(f"spk{sgn}{i}", 0.032, 0.1, (sgn * (0.9 + i * 0.16), -H / 2 + 0.03, zc), hole, 24, rx))
dev.append(disc("mic_top", 0.032, 0.1, (0.9, H / 2 - 0.03, zc), hole, 24, rx))
# back: camera only, top-left
cx, cy = -W / 2 + 0.95, H / 2 - 0.95
dev.append(disc("cam_ring", 0.4, 0.05, (cx, cy, 0.0), alu_pol))
dev.append(disc("cam_glass", 0.34, 0.06, (cx, cy, -0.004), glass))
dev.append(disc("cam_lens", 0.16, 0.062, (cx, cy, -0.006), lens))

root = bpy.data.objects.new("device", None); sc.collection.objects.link(root)
for o in dev: o.parent = root

# studio: soft light-grey sweep + white reflector cards for the metal
bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, -0.1)); fl = bpy.context.object
fl.data.materials.append(mat("floor", (0.60, 0.60, 0.61), rough=0.5))
sc.world = bpy.data.worlds.new("w"); sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.66, 0.66, 0.67, 1)
sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
for loc, rot in (((-34, 4, 14), (0, 70, 10)), ((34, 10, 14), (0, -70, -10)), ((0, 45, 18), (-70, 0, 0))):
    bpy.ops.mesh.primitive_plane_add(size=40, location=loc, rotation=[math.radians(a) for a in rot])
    card = bpy.context.object; card.data.materials.append(mat("card", (1, 1, 1)))
def area(loc, rot, size, energy, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=[math.radians(a) for a in rot])
    l = bpy.context.object; l.data.size = size; l.data.energy = energy; l.data.color = color
area((-9, -7, 16), (35, 0, -50), 14, 2200)
area((12, 10, 7), (70, 0, 130), 7, 1000, (0.92, 0.95, 1.0))
area((7, -12, 3), (80, 0, 30), 6, 400)
area((0, 14, 12), (-45, 0, 180), 8, 500)

cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam)
sc.camera = cam; cam_d.lens = 85
def look(cam, target):
    import mathutils
    d = mathutils.Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
if VIEW == "back":
    root.rotation_euler = (0, math.radians(180), math.radians(-30)); root.location = (0, 0, T + 0.1)
    cam.location = (8, -28, 21); look(cam, (0, 0.5, 0.6))
elif VIEW == "side":
    root.rotation_euler = (math.radians(90), 0, math.radians(-35)); root.location = (0, 0, H / 2)
    cam.location = (9, -36, 6.5); look(cam, (0, 0, H / 2))
elif VIEW == "front":
    root.rotation_euler = (math.radians(90), 0, 0); root.location = (0, 0, H / 2)
    cam.location = (0, -36, 5.6); look(cam, (0, 0, H / 2))
else:
    root.rotation_euler = (0, 0, math.radians(-32)); cam.location = (8, -29, 21); look(cam, (0.2, 0.3, 0.5))

sc.render.engine = "CYCLES"; sc.cycles.samples = 192; sc.cycles.use_denoising = True
try:
    pr = bpy.context.preferences.addons["cycles"].preferences; pr.compute_device_type = "METAL"; pr.get_devices()
    for dv in pr.devices: dv.use = True
    sc.cycles.device = "GPU"
except Exception as e:
    print("GPU not available:", e)
sc.render.resolution_x, sc.render.resolution_y = (1300, 1700) if VIEW in ("side", "front") else (1800, 1300)
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("wrote", OUT)
