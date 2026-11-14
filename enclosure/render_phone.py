"""First-look renders of the Concierge Phone (1 Blender unit = 1 cm). Concept only, not the CAD.
Run:  blender -b -P render_phone.py -- <view: hero|back|side> <abs out.png>
Outside 50 x 116 x 15 mm candybar. 6061 body, fine bead blast + champagne gold anodize, polished gold chamfer.
Gloss black PMMA end caps (antenna windows) top + bottom, black PC keys. Front: 1.8" 368x448 AMOLED (glass
33.6 x 41.2), 2 soft keys + 5-way pad. Right side: Talk + camera shutter. Left: volume. Back: camera ring."""
import bpy, bmesh, math, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VIEW, OUT = (argv + ["hero", os.path.join(HERE, "render.png")][len(argv):])[:2]
UI = os.path.join(HERE, "..", "..", "voice-device", "enclosure", "ui_listening.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
W, H, T, RAD, CAP = 5.0, 11.6, 1.5, 0.75, 1.3

def mat(name, base, metal=0.0, rough=0.4, coat=0.0, emit_img=None, emit=0.0, aniso=0.0):
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

gold = mat("gold_satin", (0.84, 0.66, 0.40), metal=1.0, rough=0.30)
gold_pol = mat("gold_polished", (0.93, 0.77, 0.52), metal=1.0, rough=0.07)
onyx = mat("onyx_cap", (0.006, 0.006, 0.007), rough=0.04, coat=1.0)
keyb = mat("keys", (0.012, 0.012, 0.014), rough=0.22, coat=0.4)
glass = mat("glass", (0.002, 0.002, 0.003), rough=0.02, coat=1.0)
screen = mat("screen", (0, 0, 0), rough=0.05, emit_img=UI, emit=3.0)
hole = mat("hole", (0.0, 0.0, 0.0), rough=0.9)
lens = mat("lens", (0.01, 0.012, 0.03), metal=0.3, rough=0.03, coat=1.0)

def rrect(w, h, r, n=24):
    pts = []
    for cx, cy, a0 in [(w/2-r, h/2-r, 0), (-w/2+r, h/2-r, 90), (-w/2+r, -h/2+r, 180), (w/2-r, -h/2+r, 270)]:
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def slab(name, w, h, r, depth, z0, mats, bevel=0.0, seg=1, x=0, y=0, bevel_mat=-1):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((px, py, z0)) for px, py in rrect(w, h, r)]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]: v.co.z += depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); ob.location = (x, y, 0)
    for m in mats: ob.data.materials.append(m)
    if bevel:
        bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = bevel; bv.segments = seg
        bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(40)
        if bevel_mat >= 0: bv.material = bevel_mat
    ob.modifiers.new("wn", "WEIGHTED_NORMAL")
    return ob

def apply_all(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)

def cutter(name, y0, y1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, (y0 + y1) / 2, T / 2)); c = bpy.context.object
    c.name = name; c.scale = (W * 2, y1 - y0, T * 3); bpy.ops.object.transform_apply(scale=True); return c

def boolean(ob, other, op):
    m = ob.modifiers.new("b", "BOOLEAN"); m.operation = op; m.object = other; m.solver = "EXACT"
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier="b")

def pill(name, sx, sy, sz, loc, material, rnd=0.48):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); ob = bpy.context.object; ob.name = name
    ob.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True)
    bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = min(sx, sy, sz) * rnd; bv.segments = 10
    bpy.ops.object.shade_smooth(); ob.data.materials.append(material); return ob

def disc(name, r, depth, loc, material, verts=96):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc)
    ob = bpy.context.object; ob.name = name; bpy.ops.object.shade_smooth(); ob.data.materials.append(material)
    return ob

dev = []
# ---- body: one bevelled slab split into gold middle + onyx end caps (0.25 mm seam)
full = slab("full", W, H, RAD, T, 0, [gold, gold_pol], bevel=0.055, seg=1, bevel_mat=1)
apply_all(full)
caps = full.copy(); caps.data = full.data.copy(); sc.collection.objects.link(caps)
mid_lo, mid_hi = -H / 2 + CAP, H / 2 - CAP
c_in = cutter("c_in", mid_lo, mid_hi); c_out = cutter("c_out", mid_lo - 0.025, mid_hi + 0.025)
boolean(full, c_in, "INTERSECT"); boolean(caps, c_out, "DIFFERENCE")
for c in (c_in, c_out): bpy.data.objects.remove(c)
caps.data.materials.clear(); caps.data.materials.append(onyx); caps.name = "caps"
for p in caps.data.polygons: p.use_smooth = False
full.name = "body"; dev += [full, caps]

# ---- front: display glass flush with a hair of lip, screen, earpiece slot
sy = mid_hi - 0.28 - 2.06
dev.append(slab("glass", 3.36, 4.12, 0.42, 0.06, T - 0.055, [glass], bevel=0.04, seg=6, y=sy))
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, sy, T + 0.0052)); scr = bpy.context.object
scr.scale = (2.87, 3.49, 1); scr.data.materials.append(screen); dev.append(scr)
dev.append(pill("earpiece", 1.1, 0.07, 0.02, (0, H / 2 - CAP / 2 + 0.05, T), hole, rnd=0.49))

# ---- keys: 2 soft keys + 5-way pad (black keys, polished gold ring)
ky = -2.25
dev.append(disc("pad_ring", 1.02, 0.03, (0, ky, T + 0.004), gold_pol))
dev.append(disc("pad", 0.97, 0.07, (0, ky, T + 0.02), keyb))
dev.append(disc("ok_ring", 0.43, 0.075, (0, ky, T + 0.03), gold_pol))
dev.append(disc("ok", 0.38, 0.09, (0, ky, T + 0.035), keyb))
for a in range(4):   # tiny direction dots
    ang = math.pi / 2 * a
    dev.append(disc(f"dot{a}", 0.035, 0.08, (0.7 * math.cos(ang), ky + 0.7 * math.sin(ang), T + 0.03), gold_pol, 24))
for sx in (-1, 1):
    for dy, nm in ((1.15, "soft"), (-1.15, "call")):
        dev.append(slab(f"{nm}{sx}", 1.0, 0.44, 0.2, 0.075, T - 0.01, [keyb], bevel=0.03, seg=5, x=sx * 1.62, y=ky + dy))
# small frosted status light in the bottom cap
dev.append(disc("led", 0.05, 0.02, (0, -H / 2 + CAP / 2 + 0.15, T + 0.001), mat("led", (1, 0.85, 0.6), emit=0, rough=0.3), 32))

# ---- sides: right = Talk (long, polished gold) + shutter, left = volume
zc = T * 0.52
dev.append(pill("talk", 0.12, 1.8, 0.5, (W / 2 + 0.03, 0.9, zc), gold_pol))
dev.append(pill("shutter", 0.12, 0.7, 0.5, (W / 2 + 0.03, -2.9, zc), gold_pol))
dev.append(pill("volup", 0.12, 0.8, 0.5, (-W / 2 - 0.03, 2.4, zc), gold_pol))
dev.append(pill("voldn", 0.12, 0.8, 0.5, (-W / 2 - 0.03, 1.45, zc), gold_pol))
# ---- bottom end: USB-C + 2 mic holes in the onyx cap
dev.append(pill("usbc", 0.9, 0.12, 0.32, (0, -H / 2 + 0.04, T / 2), hole))
for mx in (-1.2, 1.2): dev.append(disc(f"mic{mx}", 0.04, 0.1, (mx, -H / 2 + 0.03, T / 2), hole, 24))
for o in dev[-3:]: o.rotation_euler = (math.radians(90), 0, 0) if o.name.startswith("mic") else o.rotation_euler

# ---- back: camera ring + lens near the top, speaker grille near the bottom
cy = mid_hi - 0.95
dev.append(disc("cam_ring", 0.58, 0.06, (0, cy, -0.01), gold_pol))
dev.append(disc("cam_glass", 0.5, 0.07, (0, cy, -0.012), glass))
dev.append(disc("cam_lens", 0.24, 0.072, (0, cy, -0.013), lens))
dev.append(disc("flash", 0.11, 0.065, (0.95, cy, -0.011), mat("flash", (0.9, 0.86, 0.7), rough=0.2, coat=1.0), 48))
for i in range(-6, 7):
    for j in range(-1, 2):
        dev.append(disc(f"g{i}{j}", 0.035, 0.04, (i * 0.18, mid_lo + 0.9 + j * 0.18, -0.005), hole, 16))

root = bpy.data.objects.new("device", None); sc.collection.objects.link(root)
for o in dev: o.parent = root

# ---- studio: dark slate floor, warm key, cool rim
bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, -0.1)); fl = bpy.context.object
fl.data.materials.append(mat("floor", (0.56, 0.53, 0.50), rough=0.5))
sc.world = bpy.data.worlds.new("w"); sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.62, 0.59, 0.55, 1)
sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
# big white reflector cards so the metal has something bright to mirror
for loc, rot in (((-34, 4, 14), (0, 70, 10)), ((34, 10, 14), (0, -70, -10)), ((0, 45, 18), (-70, 0, 0))):
    bpy.ops.mesh.primitive_plane_add(size=40, location=loc, rotation=[math.radians(a) for a in rot])
    card = bpy.context.object; card.data.materials.append(mat("card", (1, 1, 1), emit=0))
    card.visible_camera = False
def area(loc, rot, size, energy, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=[math.radians(a) for a in rot])
    l = bpy.context.object; l.data.size = size; l.data.energy = energy; l.data.color = color
area((-9, -7, 16), (35, 0, -50), 14, 2400, (1.0, 0.95, 0.88))
area((12, 10, 7), (70, 0, 130), 7, 1100, (0.85, 0.9, 1.0))
area((7, -12, 3), (80, 0, 30), 6, 400)
area((0, 14, 12), (-45, 0, 180), 8, 600, (1.0, 0.9, 0.75))

cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam)
sc.camera = cam; cam_d.lens = 85
def look(cam, target):
    import mathutils
    d = mathutils.Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
if VIEW == "back":   # face down, camera end toward the viewer
    root.rotation_euler = (0, math.radians(180), math.radians(-30)); root.location = (0, 0, T + 0.1)
    cam.location = (9, -31, 23); look(cam, (0, 0.6, 0.8))
elif VIEW == "side":  # standing, three-quarter from the right
    root.rotation_euler = (math.radians(90), 0, math.radians(-35)); root.location = (0, 0, H / 2)
    cam.location = (10, -40, 7); look(cam, (0, 0, H / 2))
else:
    root.rotation_euler = (0, 0, math.radians(-32)); cam.location = (9, -33, 24); look(cam, (0.2, 0.3, 0.6))

sc.render.engine = "CYCLES"; sc.cycles.samples = 192; sc.cycles.use_denoising = True
try:
    pr = bpy.context.preferences.addons["cycles"].preferences; pr.compute_device_type = "METAL"; pr.get_devices()
    for dv in pr.devices: dv.use = True
    sc.cycles.device = "GPU"
except Exception as e:
    print("GPU not available:", e)
sc.view_settings.look = "AgX - Medium High Contrast" if "AgX - Medium High Contrast" in [l.name for l in []] else sc.view_settings.look
sc.render.resolution_x, sc.render.resolution_y = (1300, 1700) if VIEW == "side" else (1800, 1300)
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("wrote", OUT)
