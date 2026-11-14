"""Concierge phone main board: merges sch_core/power/rf/sense/ui PARTS, places every part, assigns nets, writes phone.kicad_pcb.
Run: KPY make_board.py   (KPY = KiCad's python). Routing: route.py. Coordinates below are front-view mm with the origin at
the board centre and y UP (top end of the phone = +y); add() converts to KiCad (y down, centre at 100,100).

Body 54 x 108 x 15.5 mm (Louis, 2026-11-14 night: 15.5 mm + LiPol LP665056 2400 mAh, board top 6.2 mm under the glass = Waveshare's own stack). PCB 50 x 102 x 1.0, corner radius 4, 6 layers:
  F.Cu parts + routing | In1 solid GND | In2, In3 routing | In4 GND + rail pours | B.Cu parts + routing.
Back side: battery 50 x 58 x 6.9 mm max (LiPol LP665056, 2400 mAh) covers x -25..25, y -41..+17; only flat test pads may sit under it.
Positions set by the 3D fit check (fit_check.py, 2026-11-14): screen glass 33.6 x 41.2 centred (0, 23.4), its FPC folds
behind the panel into J1 at (0, 35.4); NFC antenna centre (0, -9.4); LRA bonded under the cover glass at (20, -34.5); Talk ring (0, -30.65); speaker box bottom-right.

Placement = fixed anchors for every part whose position is set by the case (antennas, keys, connectors, Talk ring,
module, modem, camera), then a cluster packer: every other IC is placed near its 'near' part (or its group's region), and
each passive next to the pad of its 'near' part that shares a net with it, searching outward on a 0.25 mm grid with 4
rotations for the first spot whose courtyard overlaps nothing, stays 0.3 mm inside the edge and outside every keep-out.
A small part that finds no room on its side within reach tries the other side at the same spot."""
import os, re, sys, math, glob, importlib.util, collections, pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I, EDA_ANGLE, DEGREES_T
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib_check import load_fp

W, H, RC = 50.0, 102.0, 4.0
CX, CY = 100.0, 100.0
OUT = os.path.join(HERE, "phone.kicad_pcb")
hw, hh = W / 2, H / 2
TALK = (0.0, -30.65)                       # fingerprint Talk button centre (front plate hole Ø19.6)
BATT = (-25.0, -41.0, 25.0, 17.0)         # back, x0 y0 x1 y1 (LP665056: 50 x 56 cell + PCM = 58)

# ------------------------------------------------------------------ parts
PARTS = []
for f in ("sch_core.py", "sch_power.py", "sch_rf.py", "sch_sense.py", "sch_ui.py"):
    spec = importlib.util.spec_from_file_location(f[:-3], os.path.join(HERE, f))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    for p in m.PARTS: p["_file"] = f; PARTS.append(p)
BY = {p["ref"]: p for p in PARTS}
assert len(BY) == len(PARTS), "duplicate refs"

# anchors: ref -> (x, y_up, rotation deg, side). Rotation = KiCad orientation (CCW on screen).
ANCHOR = {
    # front, top end: antennas + IR + reference mic
    "AE30": (-20.4, 46.0, 0, "F"), "D303": (-12.9, 49.6, 180, "F"), "D304": (-8.0, 49.6, 180, "F"),
    "U36": (12.8, 48.7, 180, "F"),   # IR receiver clear of the Wi-Fi flex (x -8..6), review 2026-11-14
    "U72": (5.5, 49.0, 0, "F"),
    "AE31": (19.5, 48.2, 0, "F"), "U33": (13.0, 39.6, 0, "F"),
    # brain, display socket, side keys
    # 15.5 mm body (2026-11-14 night): the screen is 2.6 mm deep behind the glass with a 1 mm driver bump (x 2.3..12.1,
    # y 18.3..31.0) and its FPC loop (x +-4.7, y 31.9..38.9); module STEP: 25 x 25 x 0.8 board + 22.2 x 22.2 shield to 3.3.
    # So the shield sits left of the bump (x -20.1..2.1), rotated 180 so the Wi-Fi pad 2 faces east into free space.
    "U1": (-9.0, 19.2, 180, "F"), "J1": (0.0, 35.45, 0, "F"),   # J1 = donor header centre, panel centre 23.4 + 12.05
    # all three side keys on the right edge (the module now covers the left edge): volume up, volume down, power
    "SW72": (hw - 2.85, 36.4, -90, "F"), "SW73": (hw - 2.85, 28.0, -90, "F"), "SW71": (hw - 2.85, 19.5, -90, "F"),
    # modem + SIM (card enters through the right side wall)
    "U2": (-14.4, -11.0, 0, "F"),   # 2 left + 1 down (2026-11-14 night) for the LTE U.FL strip under the module "J2": (hw - 8.45, -10.0, 90, "F"),
    # NFC / 125 kHz antenna contacts (antenna sits over the modem, centred x 0, y -10)
    "J30": (4.75, -0.9, 0, "F"), "J35": (7.25, -0.9, 0, "F"),   # NFC pogo pins, 2.5 mm pitch
    "J31": (-16.7, -33.0, 90, "F"),   # Coilcraft 4308RV 125 kHz rod coil, lower left under the cover glass, axis along y
    "M70": (20.0, -27.5, 180, "F"),   # spring (housing toward +y, clear of the motor) under the VG0832009L tail pads (motor at (20, -34.5), tail pointing +y)
    # Talk key + light ring + privacy switch
    "SW70": (TALK[0], TALK[1], 0, "F"), "SW74": (-hw + 2.6, -30.0, 90, "F"),
    # bottom end
    "J4": (0.0, -hh + 2.37, 0, "F"),   # 1.2 mm further out: mouth ~1.2 mm behind the outer face (was 2.7), legs 0.5 from the edge
    "U71": (-11.0, -48.8, 0, "F"),   # mic left of screw H2
    "LS70": (9.5, -46.0, 90, "F"),   # Same Sky CMS-16093 springs: 7.55 from the box centre (17.05), drawing p.2; box right of H3
    # back, above the battery: camera FPC, torch, ToF, microSD (slot in the left wall), battery plug
    "J3": (0.05, 25.55, 180, "B"), "D102": (7.0, 40.0, 0, "B"), "U61": (7.0, 34.5, 0, "B"),
    "J71": (-hw + 6.6, 37.8, 270, "B"), "J10": (17.8, 26.5, 180, "B"),
}
# antenna feeds (hybrid routing, Louis 2026-11-13): U.FL right at the RF pin, pi match in a straight line, the antenna's own
# cable makes the long run.
ANCHOR.update({   # U1 pad 2 now at (3.5, 9.7) facing east; EG915U pin 60 at (-19.65, -0.03): row east at y 2.08
    "C5": (5.1, 9.22, 270, "F"), "R5": (6.4, 9.7, 0, "F"), "C6": (7.4, 9.22, 270, "F"), "J6": (10.1, 9.7, 0, "F"),
    # LTE: pin 60 up to a straight row at y 2.08 = the U.FL signal pad height, which runs under the U.FL's west GND pad
    "C9": (-20.13, 2.08, 180, "F"), "R6": (-18.6, 2.08, 0, "F"), "C10": (-17.4, 2.56, 90, "F"), "J5": (-14.9, 3.6, 90, "F"),
})
for i, ref in enumerate(("D700", "D701", "D702", "D703")):   # ring LEDs at 30/150/210/330 deg, r 10.5 (clear of the modem)
    a = math.radians((30, 150, 210, 330)[i])
    ANCHOR[ref] = (TALK[0] + 10.5 * math.cos(a), TALK[1] + 10.5 * math.sin(a), -(30, 150, 210, 330)[i], "F")

# keep-outs: (side, x0, y0, x1, y1, rule) rule = "all" (nothing), "low" (only parts h <= 0.6), "flat" (h <= 0.1),
# or a number = the tallest part allowed there (mm). The screen rules come from fit_check.py (donor STEP, 15.5 mm body)
# minus the 0.15 mm MIN_GAP, so the packer never puts a part where the fit check would fail.
KEEP = [
    ("B", *BATT, "flat"),
    ("F", -hw, 44.0, hw, hh, "all"),          # top antenna band: anchored parts only
    ("B", -hw, 44.0, hw, hh, "all"),
    ("B", 9.0, 31.0, 19.0, 41.0, "all"),      # camera head (10 x 10 module on the back cover)
    ("F", 8.75, -hh, hw, -41.2, "flat"),      # Same Sky CMS-16093 speaker 16 x 9 (x 9.05..25.05, y -50.6..-41.6) on its spring pads
    ("B", -6.5, -hh, 6.5, -44.0, "all"),      # USB-C shell legs come through
    ("F", -16.8, 2.8, 16.8, 44.0, 3.45),      # under the screen panel (3.6 mm)
    ("F", 2.3, 18.28, 12.07, 31.0, 2.45),     # screen driver bump (2.6)
    ("F", 6.64, 3.6, 13.36, 15.35, 2.65),     # screen flex parts (2.8)
    ("F", -4.7, 31.85, 4.7, 38.85, 1.6),      # screen FPC loop (1.75)
    ("F", -4.7, 31.85, 4.7, 37.35, 0.65),     # screen FPC plug end (0.8), J1 itself is anchored
]
CIRCLES = [("F", TALK[0], TALK[1], 10.0, "low"),   # fingerprint module body + steel rim above the board
           ("F", 20.0, -34.5, 4.6, "low")]         # LRA LD0832AA (8 x 3.4) bonded under the cover glass: only <= 0.6 mm parts below
# board screws (2026-11-14, Louis: "add mounting"): M1.4 from the front into bosses rising from the back wall. Only where a
# Ø3.2 spot is clear on BOTH sides and outside the battery: no top corners (sub-GHz AE30 / GNSS AE31 antennas), none
# under the battery. H2 + H3 also hold a 0.2 mm steel bracket strapped over the USB-C shell (plug forces go into the case).
MOUNT = {"H1": (-21.0, -47.0),                     # bottom-left corner (arc centre of the r4 corner)
         "H2": (-6.9, -49.0), "H3": (6.9, -49.0),  # either side of the USB-C, USB-C bracket screws
         "H4": (21.5, 41.8),                       # top right, beside the camera head, below the antenna band
         "H5": (-9.0, 42.5)}                       # top left, under the screen, right of the microSD, below the antenna band
MOUNT_R = 1.5                                      # keep-out radius both sides (head Ø2.6 front, boss Ø3.0 back)
for p in PARTS: p.setdefault("h", 1.0)
# 0201 for small passives (JLC places 0201): every 0402 resistor and every 0402 cap up to 100 nF, except parts that are
# hand-tuned with the NanoVNA or DNP (those stay 0402 so they can be swapped with an iron). LCSC numbers of swapped parts
# are re-picked from the JLC 0201 catalogue when the BOM is written (p["lcsc0201"] marks them).
def _cap_ok(v):
    v = v.split()[0]
    return v.endswith("pF") or v.endswith("nF") and float(v[:-2]) <= 100
SWAPPED = 0
for p in PARTS:
    if p.get("dnp") or "NanoVNA" in p.get("note", "") or re.search(r"(^|\s)DNP(\s|$)", p["value"]): continue
    if p.get("keep0402"): continue               # e.g. R104 887 R: no JLC 0201 part (order gate 2026-11-14)
    if p["fp"] == "Resistor_SMD:R_0402_1005Metric" or (p["fp"] == "Capacitor_SMD:C_0402_1005Metric" and _cap_ok(p["value"])):
        p["fp"] = p["fp"].replace("0402_1005Metric", "0201_0603Metric"); p["h"] = 0.35; p["lcsc0201"] = True; SWAPPED += 1
IC_GAP = 0.3     # extra room kept around every non-passive so the router can drop vias next to its pins

# ------------------------------------------------------------------ board
b = pcbnew.NewBoard(OUT)
ds = b.GetDesignSettings(); ds.SetCopperLayerCount(6); ds.SetBoardThickness(FromMM(1.0))   # 1.0 mm 6-layer (fit_check.py stack)
ds.m_MinThroughDrill = FromMM(0.2); ds.m_HoleClearance = FromMM(0.2)
for lay, name, typ in ((pcbnew.In1_Cu, "In1.GND", pcbnew.LT_POWER), (pcbnew.In2_Cu, "In2.Sig", pcbnew.LT_SIGNAL),
                       (pcbnew.In3_Cu, "In3.Sig", pcbnew.LT_SIGNAL), (pcbnew.In4_Cu, "In4.Pwr", pcbnew.LT_MIXED)):
    b.SetLayerName(lay, name); b.SetLayerType(lay, typ)
K = lambda x, y: VECTOR2I(FromMM(CX + x), FromMM(CY - y))
def seg(a, c):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(a); s.SetEnd(c); s.SetWidth(FromMM(0.1)); b.Add(s)
def arc(c, st):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetCenter(c); s.SetStart(st); s.SetArcAngleAndEnd(EDA_ANGLE(90, DEGREES_T)); s.SetWidth(FromMM(0.1)); b.Add(s)
seg(K(-hw + RC, hh), K(hw - RC, hh)); seg(K(hw, hh - RC), K(hw, -hh + RC))
seg(K(hw - RC, -hh), K(-hw + RC, -hh)); seg(K(-hw, -hh + RC), K(-hw, hh - RC))
for (cx, cy, sx, sy) in [(hw - RC, hh - RC, hw - RC, hh), (hw - RC, -hh + RC, hw, -hh + RC),
                         (-hw + RC, -hh + RC, -hw + RC, -hh), (-hw + RC, hh - RC, -hw, hh - RC)]:
    arc(K(cx, cy), K(sx, sy))   # screen-CCW from the start point (KiCad y down) = clockwise in y-up

nets = {}
def net(n):
    if n not in nets:
        ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
    return nets[n]

# ------------------------------------------------------------------ geometry helpers
_box = {}
def crt_box(fp, rot, side):
    """courtyard bbox (x0, y0, x1, y1) in y-up mm relative to the footprint origin, for this rotation and side"""
    key = (fp, rot, side)
    if key not in _box:
        f = load_fp(fp); f.SetPosition(VECTOR2I(0, 0)); f.SetOrientation(EDA_ANGLE(rot, DEGREES_T))
        mx = -1 if side == "B" else 1          # a flip on B mirrors x about the origin (Flip() needs a board)
        xs, ys = [], []
        for it in f.GraphicalItems():
            if it.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                bb = it.GetBoundingBox(); xs += [bb.GetLeft(), bb.GetRight()]; ys += [bb.GetTop(), bb.GetBottom()]
        if not xs:
            bb = f.GetBoundingBox(False, False); xs = [bb.GetLeft(), bb.GetRight()]; ys = [bb.GetTop(), bb.GetBottom()]
        holes = [(mx * ToMM(p.GetPosition().x), -ToMM(p.GetPosition().y), ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)))
                 for p in f.Pads() if p.HasHole()]
        x0, x1 = sorted((mx * ToMM(min(xs)), mx * ToMM(max(xs))))
        _box[key] = (x0, -ToMM(max(ys)), x1, -ToMM(min(ys)), holes)
    return _box[key]

CELL = 2.0
grid = {"F": collections.defaultdict(list), "B": collections.defaultdict(list)}
placed = {}          # ref -> (x, y, rot, side, rect)
def cells(r):
    for i in range(int(math.floor(r[0] / CELL)), int(math.floor(r[2] / CELL)) + 1):
        for j in range(int(math.floor(r[1] / CELL)), int(math.floor(r[3] / CELL)) + 1):
            yield (i, j)
def free(r, side):
    for c in cells(r):
        for o in grid[side][c]:
            if r[0] < o[2] and o[0] < r[2] and r[1] < o[3] and o[1] < r[3]: return False
    return True
def occupy(r, side):
    for c in cells(r): grid[side][c].append(r)

def inside_board(r, m=0.3):
    x0, y0, x1, y1 = r
    if x0 < -hw + m or x1 > hw - m or y0 < -hh + m or y1 > hh - m: return False
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):          # rounded corners
        cx, cy = sx * (hw - RC), sy * (hh - RC)
        px, py = (x1 if sx > 0 else x0), (y1 if sy > 0 else y0)
        if sx * px > sx * cx and sy * py > sy * cy and math.hypot(px - cx, py - cy) > RC - m: return False
    return True

def allowed(r, side, h, anchored=False):
    for (s, x0, y0, x1, y1, rule) in KEEP:
        if s != side or not (r[0] < x1 and x0 < r[2] and r[1] < y1 and y0 < r[3]): continue
        if anchored and rule != "flat": continue
        if rule == "all" or (rule == "low" and h > 0.6) or (rule == "flat" and h > 0.1): return False
        if isinstance(rule, float) and h > rule: return False
    for (s, cx, cy, rad, rule) in CIRCLES:
        if s != side or anchored: continue
        nx, ny = min(max(cx, r[0]), r[2]), min(max(cy, r[1]), r[3])
        if math.hypot(nx - cx, ny - cy) < rad and h > 0.6: return False
    return True

def put(p, x, y, rot, side, force=False):
    bx = crt_box(p["fp"], rot, side)
    g = 0.0 if is_passive(p) or p["ref"].startswith("TP") else IC_GAP
    r = (x + bx[0] - g, y + bx[1] - g, x + bx[2] + g, y + bx[3] + g)
    if not force:
        if not inside_board(r) or not free(r, side) or not allowed(r, side, p["h"]): return False
        other = "B" if side == "F" else "F"      # plated holes block both sides
        for (hx, hy, d) in bx[4]:
            hr = (x + hx - d / 2 - 0.3, y + hy - d / 2 - 0.3, x + hx + d / 2 + 0.3, y + hy + d / 2 + 0.3)
            if not free(hr, other): return False
    occupy(r, side)
    for (hx, hy, d) in bx[4]:
        occupy((x + hx - d / 2 - 0.3, y + hy - d / 2 - 0.3, x + hx + d / 2 + 0.3, y + hy + d / 2 + 0.3),
               "B" if side == "F" else "F")
    placed[p["ref"]] = (x, y, rot, side, r)
    return True

# ------------------------------------------------------------------ pad positions of placed parts (for passive targets)
_pads = {}
def pad_xy(ref):
    """{net: [(x, y)]} for a placed part, y-up board mm"""
    if ref in _pads: return _pads[ref]
    p = BY[ref]; x, y, rot, side, _ = placed[ref]
    f = load_fp(p["fp"]); f.SetPosition(VECTOR2I(0, 0)); f.SetOrientation(EDA_ANGLE(rot, DEGREES_T))
    mx = -1 if side == "B" else 1
    out = collections.defaultdict(list)
    for pd in f.Pads():
        n = p.get("pins", {}).get(pd.GetNumber())
        if n: out[n].append((x + mx * ToMM(pd.GetPosition().x), y - ToMM(pd.GetPosition().y)))
    _pads[ref] = out; return out

RAILS = {"GND", "3V3", "VSYS", "VBAT", "VBUS", "1V8_LTE", "3V8_LTE", "RF_3V3", "DISP_3V3", "CAM_3V3", "SD_3V3",
         "MIC_3V3", "FP_3V3"}
def is_passive(p): return p["ref"].rstrip("0123456789") in ("C", "R", "L", "FB")
def target(p):
    """(x, y, side) where this part wants to be"""
    near = p.get("near")
    if near and near in placed:
        nx, ny, _, nside, _ = placed[near]
        mine = set(p.get("pins", {}).values())
        sig = [n for n in mine if n not in RAILS]
        pads = pad_xy(near)
        for group in (sig, [n for n in mine if n in RAILS and n != "GND"]):
            pts = [pt for n in group for pt in pads.get(n, [])]
            if pts:
                return sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts), nside
        return nx, ny, nside
    return REGION.get(p["ref"], REGION.get(p["group"], (0, 0, "F")))

# default regions for unanchored ICs (and their passives when 'near' is missing)
REGION = {"rf": (-15.0, 22.0, "F"), "sense": (-17.0, -2.0, "F"), "ui": (-15.0, -34.0, "F"),
          "power": (17.0, -32.0, "F"), "core": (0.0, 0.0, "F"),
          "U30": (8.0, -5.0, "F"), "U50": (-3.0, 0.0, "F"), "U51": (-3.0, 0.0, "F"), "U53": (-16.0, 36.0, "F"),
          "U55": (-20.0, 4.0, "F"), "U54": (21.5, 38.0, "B"), "U56": (-6.0, 38.0, "F"), "U57": (-2.0, 38.0, "F"), "U73": (13.0, -40.0, "F"), "U74": (-14.0, -38.0, "F"),
          "M70": (20.0, -34.5, "F"), "J70": (0.0, -19.5, "F"), "U12": (3.0, -16.0, "F"), "U11": (16.0, -36.0, "F"),
          "U10": (18.0, -27.0, "F"), "U19": (6.0, -40.0, "F"), "U13": (17.0, 21.0, "B"), "U60": (-3.0, 38.0, "F"),
          "U18": (11.0, 38.0, "B"), "U14": (6.0, 3.0, "F"), "U15": (0.0, 26.0, "B"), "U16": (-15.0, 10.0, "F"),
          "U17": (-15.0, 30.0, "B"), "U76": (0.0, -19.0, "F"), "U75": (-13.0, -27.0, "F")}

def search(p, tx, ty, side, rmax=24.0, step=0.25):
    rots = (0, 90, 180, 270)
    k = 0
    while k * step <= rmax:
        ring = [(0, 0)] if k == 0 else (
            [(i, -k) for i in range(-k, k + 1)] + [(i, k) for i in range(-k, k + 1)] +
            [(-k, j) for j in range(-k + 1, k)] + [(k, j) for j in range(-k + 1, k)])
        ring.sort(key=lambda d: d[0] * d[0] + d[1] * d[1])
        for (i, j) in ring:
            for rot in rots:
                if put(p, tx + i * step, ty + j * step, rot, side): return True
        k += 1
    return False

# ------------------------------------------------------------------ place
for hx, hy in MOUNT.values():                       # screw keep-outs first, on both sides
    for s in ("F", "B"): occupy((hx - MOUNT_R, hy - MOUNT_R, hx + MOUNT_R, hy + MOUNT_R), s)
for ref, (x, y, rot, side) in ANCHOR.items():
    p = BY[ref]; p["side"] = side
    bx = crt_box(p["fp"], rot, side)
    r = (x + bx[0], y + bx[1], x + bx[2], y + bx[3])
    if not free(r, side):
        hit = [o for o, v in placed.items() if v[3] == side and r[0] < v[4][2] and v[4][0] < r[2] and r[1] < v[4][3] and v[4][1] < r[3]]
        print(f"WARNING anchor {ref} {tuple(round(v, 2) for v in r)} overlaps {[(o, tuple(round(v, 2) for v in placed[o][4])) for o in hit]}")
    if not allowed(r, side, p["h"], anchored=True): print(f"WARNING anchor {ref} sits in a keep-out")
    put(p, x, y, rot, side, force=True)

def order_key(p):
    return (is_passive(p) or p["ref"].startswith("TP"), -(lambda b_: (b_[2] - b_[0]) * (b_[3] - b_[1]))(crt_box(p["fp"], 0, "F")))
todo = sorted([p for p in PARTS if p["ref"] not in placed], key=order_key)
failed, flipped = [], []
for rnd in range(6):
    left = []
    for p in todo:
        near = p.get("near")
        if near and near not in placed and BY.get(near) and rnd < 5: left.append(p); continue
        tx, ty, tside = target(p)
        side = tside if p["ref"] not in REGION else REGION[p["ref"]][2]
        if p["ref"].startswith("TP"): side = "B"
        if search(p, tx, ty, side): p["side"] = side; continue
        other = "B" if side == "F" else "F"
        if p["h"] <= 1.5 and search(p, tx, ty, other, rmax=12.0):
            p["side"] = other; flipped.append(p["ref"]); continue
        if search(p, tx, ty, side, rmax=60.0, step=0.5) or search(p, tx, ty, other, rmax=60.0, step=0.5):
            flipped.append(p["ref"] + "(far)"); continue
        failed.append(p["ref"])
    todo = left
    if not todo: break

# ------------------------------------------------------------------ build footprints
for p in PARTS:
    if p["ref"] not in placed: continue
    x, y, rot, side, _ = placed[p["ref"]]
    f = load_fp(p["fp"]); f.SetReference(p["ref"]); f.SetValue(p["value"])
    f.SetPosition(K(x, y)); f.SetOrientation(EDA_ANGLE(rot, DEGREES_T)); b.Add(f)
    if side == "B": f.Flip(K(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    for pd in f.Pads():
        n = p.get("pins", {}).get(pd.GetNumber())
        if n: pd.SetNet(net(n))
    if p.get("dnp"): f.SetDNP(True); f.SetExcludedFromBOM(True); f.SetExcludedFromPosFiles(True)
    if not p.get("lcsc"): f.SetExcludedFromPosFiles(True)
for ref, (hx, hy) in MOUNT.items():
    f = load_fp("phone:MountingHole_M1.4_NPTH"); f.SetReference(ref); f.SetValue("M1.4 screw")
    f.SetPosition(K(hx, hy)); b.Add(f)
    f.SetBoardOnly(True); f.SetExcludedFromBOM(True); f.SetExcludedFromPosFiles(True)

# antenna keep-outs (no pour, no vias) under the GNSS chip antenna and the whole top 6 mm of the board on every layer
def rule_area(x0, y0, x1, y1, tracks_ok=True):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetDoNotAllowZoneFills(True) if hasattr(z, "SetDoNotAllowZoneFills") else z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowVias(True); z.SetDoNotAllowTracks(not tracks_ok); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); [ls.AddLayer(l) for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu)]
    z.SetLayerSet(ls); ol = z.Outline(); ol.NewOutline()
    for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): ol.Append(K(x, y).x, K(x, y).y)
    b.Add(z)
# 0.5 mm board-edge band: no tracks or vias (Freerouting does not know KiCad's edge clearance); pads may sit in it
def rr(w, h, r, n=8):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts
def edge_rule(pts):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    try: z.SetDoNotAllowZoneFills(False)
    except AttributeError: z.SetDoNotAllowCopperPour(False)
    ls = pcbnew.LSET(); [ls.AddLayer(l) for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu)]
    z.SetLayerSet(ls); ol = z.Outline(); ol.NewOutline()
    for (x, y) in pts: ol.Append(K(x, y).x, K(x, y).y)
    b.Add(z)
E = 0.5; O = 0.2                                   # band width, overhang past the edge
edge_rule([(-hw - O, -hh + RC), (-hw + E, -hh + RC), (-hw + E, hh - RC), (-hw - O, hh - RC)])      # left
edge_rule([(hw - E, -hh + RC), (hw + O, -hh + RC), (hw + O, hh - RC), (hw - E, hh - RC)])          # right
edge_rule([(-hw + RC, hh - E), (hw - RC, hh - E), (hw - RC, hh + O), (-hw + RC, hh + O)])          # top
edge_rule([(-hw + RC, -hh - O), (hw - RC, -hh - O), (hw - RC, -hh + E), (-hw + RC, -hh + E)])      # bottom
for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):                                                # corners
    cx, cy = sx * (hw - RC), sy * (hh - RC)
    arcpts = [(cx + sx * (RC - E) * math.cos(math.radians(a)), cy + sy * (RC - E) * math.sin(math.radians(a))) for a in range(0, 91, 10)]
    edge_rule(arcpts + [(cx, cy + sy * (RC + O)), (cx + sx * (RC + O), cy + sy * (RC + O)), (cx + sx * (RC + O), cy)])
ax, ay = ANCHOR["AE31"][:2]
rule_area(ax - 2.125 - 1.0, ay - 2.0, hw, hh)                     # W3011 4.25 x 4.0 clearance + feed side
# 125 kHz rod coil J31 at (-16.7, -33.0) along y: no copper under the rod between its pads or within 1 mm of its ends
rule_area(-18.5, -37.2, -14.9, -28.8, tracks_ok=False)
rule_area(-19.2, -40.0, -14.2, -39.0, tracks_ok=False); rule_area(-19.2, -27.0, -14.2, -26.0, tracks_ok=False)

b.Save(OUT)
nF = sum(1 for r in placed.values() if r[3] == "F"); nB = len(placed) - nF
area = lambda s: sum((r[4][2] - r[4][0]) * (r[4][3] - r[4][1]) for r in placed.values() if r[3] == s)
board = W * H - 4 * (RC * RC - math.pi * RC * RC / 4)
print(f"placed {len(placed)}/{len(PARTS)} (F {nF}, B {nB}); courtyards F {area('F'):.0f} mm2, B {area('B'):.0f} mm2 "
      f"of {board:.0f} per side (B usable beside battery ~{board - 43 * 62 - 6 * W:.0f})")
print("moved to the other side:", flipped)
print("FAILED:", failed)
print("nets:", len(nets), "| 0201 swaps:", SWAPPED)

# JLC 6-layer 1.0 mm impedance stackup into the saved board (stackup.py, 2026-11-14 night)
import stackup
print("stackup JLC06101H-3313, board", stackup.patch(OUT), "mm")
