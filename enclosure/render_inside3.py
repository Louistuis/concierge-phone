"""Exploded 'inside' view of Concierge Phone v2 (packaging study 1). All sizes in mm (converted to cm = Blender units).
Run:  blender -b -P render_inside.py -- <abs out.png>   (also writes <out>.labels.json with 2D label anchors)
Stack, back -> front (z from the back face of the body):
  aluminium body (sides + back, 1.0 back wall, 1.5 side walls) with a pale non-metal bottom band (LTE window)
  battery 42 x 60 x 6 (z 1.2-7.2), camera head on the back of the PCB top-left
  PCB 44 x 80 x 1.0 (z 7.4-8.4), front side: P4 module under the display, LTE module + Talk switch + SIM below
  display (panel 30.6 x 38 x 1.0 + glass 33.6 x 41.2 x 1.5), black front plate 1.5 mm with the panel glass flush."""
import bpy, bmesh, math, sys, os, json
from bpy_extras.object_utils import world_to_camera_view
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.join(HERE, "inside.png")
UI = os.path.join(HERE, "..", "..", "voice-device", "enclosure", "ui_listening.png")
mm = 0.1
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
W, H, T, RAD = 48, 100, 13.5, 9.5
EXP = {"body": 0, "battery": 14, "pcb": 30, "ant": 40, "display": 46, "front": 56}   # exploded lift, mm

def mat(name, base, metal=0.0, rough=0.4, coat=0.0, emit_img=None, emit=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1); p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough; p.inputs["Coat Weight"].default_value = coat
    if alpha < 1: p.inputs["Alpha"].default_value = alpha
    if emit_img:
        tex = m.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(emit_img)
        m.node_tree.links.new(tex.outputs["Color"], p.inputs["Emission Color"])
        m.node_tree.links.new(tex.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Emission Strength"].default_value = emit
    return m
M = dict(alu=mat("alu", (0.80, 0.80, 0.81), 1, 0.34), band=mat("band", (0.70, 0.71, 0.72), 0, 0.45),
         batt=mat("batt", (0.62, 0.64, 0.68), 0.7, 0.35), pcb=mat("pcb", (0.03, 0.05, 0.09), 0, 0.35, 0.4),
         shield=mat("shield", (0.85, 0.85, 0.86), 1, 0.22), lte=mat("lte", (0.78, 0.79, 0.80), 1, 0.28),
         blk=mat("blk", (0.01, 0.01, 0.012), 0, 0.3), front=mat("front", (0.004, 0.004, 0.005), 0, 0.03, 1.0),
         flex=mat("flex", (0.78, 0.42, 0.08), 0.2, 0.3), gold=mat("gold", (0.95, 0.75, 0.35), 1, 0.2),
         glass=mat("glass", (0.003, 0.003, 0.004), 0, 0.02, 1.0), screen=mat("screen", (0, 0, 0), 0, 0.05, emit_img=UI, emit=2.6),
         spk=mat("spk", (0.15, 0.15, 0.16), 0.5, 0.4), ferrite=mat("ferrite", (0.08, 0.08, 0.09), 0.2, 0.6), led=mat("led", (0.95, 0.95, 0.9), 0, 0.3), frost=mat("frost", (0.9, 0.9, 0.92), 0, 0.6), lens=mat("lens", (0.02, 0.03, 0.08), 0.3, 0.03, 1.0))

def rrect(w, h, r, n=24):
    pts = []
    for cx, cy, a0 in [(w/2-r, h/2-r, 0), (-w/2+r, h/2-r, 90), (-w/2+r, -h/2+r, 180), (w/2-r, -h/2+r, 270)]:
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

objs = {}
def box(name, w, h, d, x, y, z0, material, r=0.3, bevel=0.15, lift="pcb"):
    """w x h footprint (mm) centred at x, y; from z0 up by d (mm, measured from the back face)."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((px * mm, py * mm, 0)) for px, py in rrect(w, h, max(min(r, w / 2 - 0.01, h / 2 - 0.01), 0.01))]
    f = bm.faces.new(vs); ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]: v.co.z += d * mm
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    ob.location = (x * mm, y * mm, (z0 + EXP[lift]) * mm)
    if bevel:
        b = ob.modifiers.new("b", "BEVEL"); b.width = bevel * mm; b.segments = 3; b.limit_method = "ANGLE"
    ob.data.materials.append(material); objs[name] = ob; return ob

def boolean(ob, other, op="DIFFERENCE"):
    m = ob.modifiers.new("x", "BOOLEAN"); m.operation = op; m.object = other; m.solver = "EXACT"
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier="x"); other.hide_render = True

# ---- body tub (open at the front) + non-metal bottom band
tub = box("body", W, H, T - 1.5, 0, 0, 0, M["alu"], r=RAD, bevel=2.5, lift="body")
inner = box("inner", W - 3, H - 3, 20, 0, 0, 1.0, M["alu"], r=RAD - 1.5, bevel=0, lift="body")
boolean(tub, inner)
cut = box("bandcut", W + 4, 9.4, 30, 0, -H / 2 + 4.5, -5, M["alu"], r=0.01, bevel=0, lift="body"); boolean(tub, cut)
band = box("band", W, H, T - 1.5, 0, 0, 0, M["band"], r=RAD, bevel=2.5, lift="body")
boolean(band, box("inner2", W - 3, H - 3, 20, 0, 0, 1.0, M["alu"], r=RAD - 1.5, bevel=0, lift="body"))
boolean(band, box("bandkeep", W + 4, 9.0, 30, 0, -H / 2 + 4.5, -5, M["alu"], r=0.01, bevel=0, lift="body"), "INTERSECT")

# ---- back side of the board: battery + camera, torch, laser distance, microSD
box("battery", 42, 62, 6, 0, -10, 1.2, M["batt"], r=1.5, bevel=0.6, lift="battery")
box("cam_head", 10, 10, 5.4, -14, 34, 1.6, M["blk"], r=0.8, bevel=0.3, lift="battery")
box("cam_lens", 6, 6, 0.6, -14, 34, 1.0, M["lens"], r=3, bevel=0.2, lift="battery")
box("torch", 3, 3, 1.0, -6.5, 36.5, 5.8, M["led"], r=0.3, bevel=0.1, lift="battery")
box("tof", 4.9, 2.5, 1.6, -6.5, 31.5, 5.2, M["blk"], r=0.3, bevel=0.1, lift="battery")
box("microsd", 11.4, 12, 1.4, 12, 33, 5.4, M["shield"], r=0.4, bevel=0.15, lift="battery")

# ---- PCB and its front-side parts
Z = 8.4
box("pcb", 44, 88, 1.0, 0, 1, 7.4, M["pcb"], r=3, bevel=0.2)
box("p4", 25, 25, 2.5, 0, 24, Z, M["shield"], r=0.6, bevel=0.25)                 # ESP32-P4 + C6 module
box("gnss", 9.7, 10.1, 2.4, 16.5, 38, Z, M["shield"], r=0.5, bevel=0.2)            # u-blox MAX-M10S
box("lte", 19.9, 23.6, 2.4, -11, -22, Z, M["lte"], r=0.6, bevel=0.25)             # Quectel EG915U
box("sim", 14.2, 16.1, 1.4, 12, -24, Z, M["shield"], r=0.4, bevel=0.15)           # nano-SIM
box("disp_sock", 9.3, 2.5, 0.8, 0, 7.5, Z, M["blk"], r=0.2, bevel=0.1)
box("usbc", 8.9, 7.3, 3.2, 0, -45, Z - 1.6, M["shield"], r=1.2, bevel=0.3)
box("spk", 16, 8, 3.0, 14, -43, Z, M["spk"], r=1.0, bevel=0.3)
box("talk_sw", 3.0, 2.5, 1.6, 0, -31, Z, M["blk"], r=0.3, bevel=0.1)
chips = [("nfc_ic", -15, 2, 5, 5), ("cc1101", 15, 2, 4, 4), ("lora", 15, 8.5, 4, 4), ("charger", -16, -36, 3, 3),
         ("buckboost", -9, -36, 3, 4), ("lte_pwr", 6, -36, 4, 3), ("expander", -16, 9, 5, 5), ("imu", 17, 14, 3, 2.5),
         ("baro", -18, 40, 2, 2), ("rh", -15, 40, 1.5, 1.5), ("voc", -12, 40, 2.4, 2.4), ("rfid_lf", -9, -8, 3, 3),
         ("amp", 19, -36, 3, 3), ("haptic", -19, -28, 3, 3), ("se", 19, -10, 2, 3), ("fuel", -19, -18, 2.5, 4),
         ("led_drv", 6, -16, 2, 1.6), ("ir_tx", -4, 44.5, 3, 2), ("ir_rx", 4, 44.5, 5, 4)]
for name, x, y, w, h in chips:
    box(name, w, h, 0.9, x, y, Z, M["blk"], r=0.2, bevel=0.08)
box("ufl_lte", 3, 3, 1.2, -19, -41, Z, M["gold"], r=1.4, bevel=0.1)
box("ufl_wifi", 3, 3, 1.2, 19, 44, Z, M["gold"], r=1.4, bevel=0.1)
box("ant_subg", 7, 3, 0.8, -17, 44.5, Z, M["blk"], r=0.2, bevel=0.1)
box("ant_gnss", 3.2, 1.6, 0.8, 11, 44.5, Z, M["blk"], r=0.2, bevel=0.1)
for i in range(4):   # light ring LEDs around the Talk key
    a = math.radians(45 + 90 * i)
    box(f"ring{i}", 1.0, 1.0, 0.6, 10.5 * math.cos(a), -31 + 10.5 * math.sin(a), Z, M["led"], r=0.1, bevel=0.05)

# ---- antennas: LTE flex at the bottom band, Wi-Fi at the top end, NFC + 125 kHz coil under the front plate
box("ant_lte", 42.6, 8.0, 0.2, 0, -44, 11.6, M["flex"], r=0.5, bevel=0, lift="ant")
box("ant_wifi", 34.9, 9.0, 0.2, -2, 43, 11.6, M["flex"], r=0.5, bevel=0, lift="ant")
box("nfc", 27.3, 23, 0.3, 0, -10, 11.4, M["ferrite"], r=1.0, bevel=0, lift="ant")
box("nfc_coil", 25, 21, 0.05, 0, -10, 11.71, M["flex"], r=2.0, bevel=0, lift="ant")

# ---- display + front plate with the fingerprint Talk button + light ring
box("panel", 30.6, 38, 1.0, 0, 23.4, 11.0, M["blk"], r=1.0, bevel=0.2, lift="display")
box("panel_glass", 33.6, 41.2, 1.5, 0, 23.4, 12.0, M["glass"], r=3.5, bevel=0.5, lift="display")
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 23.4 * mm, (13.52 + EXP["display"]) * mm)); s = bpy.context.object
s.scale = (28.7 * mm, 34.94 * mm, 1); s.data.materials.append(M["screen"]); objs["screen"] = s
fp = box("front", W - 3.2, H - 3.2, 1.5, 0, 0, 12.0, M["front"], r=RAD - 1.6, bevel=0.5, lift="front")
boolean(fp, box("win", 33.8, 41.4, 10, 0, 23.4, 8, M["front"], r=3.5, bevel=0, lift="front"))
boolean(fp, box("talkhole", 19.6, 19.6, 10, 0, -31, 8, M["front"], r=9.8, bevel=0, lift="front"))
box("fp_rim", 19.2, 19.2, 2.0, 0, -31, 11.5, M["alu"], r=9.6, bevel=0.5, lift="front")
box("fp_glass", 14.2, 14.2, 0.2, 0, -31, 13.45, M["glass"], r=7.1, bevel=0.05, lift="front")
box("ring_guide", 22.5, 22.5, 0.4, 0, -31, 11.6, M["frost"], r=11.25, bevel=0.1, lift="front")
# ---- studio
bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, -0.05)); fl = bpy.context.object
fl.data.materials.append(mat("floor", (0.62, 0.62, 0.63), 0, 0.5))
sc.world = bpy.data.worlds.new("w"); sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.68, 0.68, 0.69, 1)
sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
for loc, rot in (((-34, 4, 14), (0, 70, 10)), ((34, 10, 14), (0, -70, -10)), ((0, 45, 18), (-70, 0, 0))):
    bpy.ops.mesh.primitive_plane_add(size=40, location=loc, rotation=[math.radians(a) for a in rot])
    bpy.context.object.data.materials.append(mat("card", (1, 1, 1)))
def area(loc, rot, size, energy):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=[math.radians(a) for a in rot])
    l = bpy.context.object; l.data.size = size; l.data.energy = energy
area((-9, -7, 18), (30, 0, -50), 14, 2600); area((12, 10, 9), (65, 0, 130), 7, 900); area((7, -12, 4), (80, 0, 30), 6, 400)

root = bpy.data.objects.new("dev", None); sc.collection.objects.link(root)
for o in objs.values(): o.parent = root
root.rotation_euler = (0, 0, math.radians(-28))
cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam)
sc.camera = cam; cam_d.lens = 70
cam.location = (13, -30, 26)
import mathutils
d = mathutils.Vector((0.2, 0.4, 2.6)) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

sc.render.engine = "CYCLES"; sc.cycles.samples = 160; sc.cycles.use_denoising = True
try:
    pr = bpy.context.preferences.addons["cycles"].preferences; pr.compute_device_type = "METAL"; pr.get_devices()
    for dv in pr.devices: dv.use = True
    sc.cycles.device = "GPU"
except Exception as e:
    print("GPU not available:", e)
sc.render.resolution_x, sc.render.resolution_y = 1700, 2000
bpy.context.view_layer.update()

# 2D anchors for labels (top-centre of each part, in pixels)
LAB = {"front": "Black glass front", "panel_glass": "1.8\" AMOLED + touch", "fp_rim": "Fingerprint Talk button + light ring",
       "nfc": "NFC + 125 kHz coil (ferrite)", "ant_wifi": "Wi-Fi antenna", "ant_lte": "4G antenna (bottom band)",
       "p4": "ESP32-P4 + Wi-Fi 6 module", "gnss": "GPS (u-blox M10)", "lte": "4G modem", "sim": "Nano-SIM",
       "cc1101": "Sub-GHz + LoRa radios", "expander": "Sensors, power, tools (chips)", "spk": "Speaker", "usbc": "USB-C",
       "battery": "Battery ~1,800-2,000 mAh", "cam_head": "Camera + torch + laser distance", "microsd": "microSD",
       "ir_rx": "Infrared TX/RX (top end)"}
anch = {}
for k, text in LAB.items():
    ob = objs[k]; bb = [ob.matrix_world @ mathutils.Vector(c) for c in ob.bound_box]
    c = sum(bb, mathutils.Vector()) / 8; top = max(v.z for v in bb); p = mathutils.Vector((c.x, c.y, top))
    v = world_to_camera_view(sc, cam, p)
    anch[k] = {"text": text, "x": v.x * sc.render.resolution_x, "y": (1 - v.y) * sc.render.resolution_y}
json.dump(anch, open(OUT + ".labels.json", "w"), indent=1)
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("wrote", OUT)
