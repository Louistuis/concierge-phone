"""3D fit check of the whole phone: board parts + off-board parts + case, in one stack.  python3 fit_check.py [board.json]
Reads shots/board.json (export_view.py) for every footprint's courtyard and side, and the part heights ('h') from sch_*.py.
Everything else (case, screen, battery, antennas, fingerprint, camera, speaker) is in STACK / OBJ below, each number with
its source. Coordinates: front view, mm, origin = board centre = body centre, y up; z = height above the BACK face.

Checks:
  1 every front part's top clears whatever sits above it (screen, front plate, NFC antenna, flex antennas, speaker...)
  2 every back part clears whatever sits below it (battery, camera, back wall)
  3 off-board parts don't hit each other and stay inside the case cavity
  4 the stack adds up to the body thickness
Prints every clearance below MIN_GAP and the slack (wasted air) per zone, exits 1 on any clash."""
import json, os, sys, glob, importlib.util, math
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "shots", "board.json")
MIN_GAP = 0.15        # mm between a part and anything rigid above/below it (tolerance + adhesive squeeze)

# ---------------------------------------------------------------- case + stack (z from the back face up)
# Decided 2026-11-14 night (Louis: 15.5 mm body + LiPol 2400 mAh). Board top 6.2 mm under the glass top = the Waveshare
# ESP32-S3-Touch-AMOLED-1.8 stack the screen FPC was made for (its STEP: glass top 0, board top -6.2).
STACK = {
    "body_w": 54.0, "body_h": 108.0, "body_t": 15.5,
    "side_wall": 1.5, "back_wall": 0.9,                  # aluminium unibody
    "cover_t": 1.1,                                      # front cover glass (Gorilla-class), flush with the screen glass
    "screen_t": 2.6,                                     # 1.8" AMOLED glass + panel, glass top to panel back (donor STEP)
    "batt_gap": 0.2,                                     # back wall -> battery (stretch-release strips)
    "batt_t": 6.9, "batt_w": 50.0, "batt_h": 58.0,       # LiPol LP665056 2400 mAh: 6.6 +-0.3 x 50 x 56, PCM end -> 58
    "foam": 0.3,                                         # battery -> PCB back (PORON)
    "pcb_t": 1.0,                                        # JLC 6-layer 1.0 mm (phone practice)
}
def z():
    s = STACK; d = {}
    d["batt0"] = s["back_wall"] + s["batt_gap"]; d["batt1"] = d["batt0"] + s["batt_t"]
    d["pcb0"] = d["batt1"] + s["foam"]; d["pcb1"] = d["pcb0"] + s["pcb_t"]
    d["cover0"] = s["body_t"] - s["cover_t"]                       # underside of the cover glass
    d["screen0"] = s["body_t"] - s["screen_t"]                     # underside of the screen panel
    return d

# ---------------------------------------------------------------- off-board objects: (name, side, shape, geometry, z0, z1)
# shape "rect": (cx, cy, w, h); "circ": (cx, cy, r); "plate": everywhere. side F = above the board, B = below it.
def objects():
    Z = z(); s = STACK; t = s["body_t"]; p1 = Z["pcb1"]; c0 = Z["cover0"]
    return [
        ("screen", "F", "rect", (0.0, 23.4, 33.6, 41.2), Z["screen0"], t),
        # below the panel back (donor STEP sliced every 0.1 mm, 2026-11-14 night; our y = STEP y + 23.4):
        ("screen bump (driver)", "F", "rect", (7.185, 24.64, 9.77, 12.72), t - 3.6, Z["screen0"]),
        ("screen flex parts", "F", "rect", (10.0, 9.475, 6.72, 11.75), t - 3.4, Z["screen0"]),
        ("screen FPC loop", "F", "rect", (0.0, 35.35, 9.4, 7.0), t - 4.45, Z["screen0"]),        # U-turn, lower leg at -4.3..-4.45
        # plug end: stiffener + A4S header ride on J1 (0.8 mated). Donor: glass top to board top 6.2, so the plug sits at
        # t - 6.2 + 0.8; J1 TOUCH below checks OUR board top is at that same 6.2 (the FPC loop was cut for it).
        ("screen FPC plug (on J1)", "F", "rect", (0.0, 34.6, 9.4, 5.5), t - 6.2 + 0.8, t - 4.45),
        ("cover glass", "F", "plate", None, c0, t),
        ("NFC antenna (Molex 146236)", "F", "rect", (0.0, -9.4, 27.0, 23.0), c0 - 0.27, c0),
        ("LTE flex (Taoglas FXP40)", "F", "rect", (0.0, -46.45, 42.6, 12.1), c0 - 0.24, c0),
        ("Wi-Fi flex (Taoglas FXP74)", "F", "rect", (-1.0, 47.6, 14.0, 7.0), c0 - 0.10, c0),
        ("fingerprint rim", "F", "circ", (0.0, -30.65, 9.6), t - 2.0, t),
        ("fingerprint body", "F", "circ", (0.0, -30.65, 8.25), t - 4.0, t - 2.0),      # 1.2 board + ~0.8 back parts
        ("speaker (Same Sky CMS-16093)", "F", "rect", (17.05, -46.1, 16.0, 9.0), p1 + 0.0, p1 + 3.15),   # working height 3.0 +0.15/-0 (drawing p.2)
        ("LRA (VG0832009L)", "F", "circ", (20.0, -34.5, 4.05), c0 - 3.25, c0),     # bonded under the cover glass
        # its flex tail (4.75 wide, to 8.55 from the centre, pads facing down, level with the motor bottom) points +y;
        # M70 spring (working height 2.0) presses the pads ~7 mm from the centre
        ("LRA tail", "F", "rect", (20.0, -30.225, 4.75, 8.55), c0 - 3.25, c0 - 3.0),
        ("battery 2400 mAh", "B", "rect", (0.0, -41.0 + s["batt_h"] / 2, s["batt_w"], s["batt_h"]), Z["batt0"], Z["batt1"]),
        ("camera head (Arducam OV5647 spy)", "B", "rect", (14.0, 36.0, 8.5, 8.5), s["back_wall"] - 0.5, s["back_wall"] + 5.0),
        ("back wall", "B", "plate", None, 0.0, s["back_wall"]),
        # Talk key: the fingerprint module floats 0.25 mm in its steel rim; a PET nub (NUB long) bonded on its back presses
        # the snap dome (phone practice). MEASURE the real module back before ordering (body bottom = t - 4.0 is an estimate).
        ("Talk plunger (fingerprint back)", "F", "circ", (0.0, -30.65, 1.0), t - 4.0 - NUB, t - 4.0),
        # 0.2 mm stainless bracket strapped over the USB-C shell, screwed down by H2 + H3 (plug forces go into the case)
        ("USB-C bracket", "F", "rect", (0.0, -49.5, 12.6, 3.0), p1 + 3.26, p1 + 3.46),
    ] + [(f"boss {ref}", "B", "circ", (x, y, 1.5), s["back_wall"], Z["pcb0"]) for ref, x, y in MOUNTS]
NUB = 1.75            # Talk plunger nub length, mm (0.75 at 14.9 mm; the top rose 0.6 and the board sank 0.4)
MOUNTS = []          # (ref, x, y) of the board screws, filled from board.json (H refs): their bosses rise from the back wall

# parts that must REACH the object above/below them (springs, plugs, plungers). Since 2026-11-14 these are no longer
# skipped: the gap must be within +-TOUCH_TOL (h = working height for springs, mated height for plugs). A gap larger than
# that is NO CONTACT (the part never touches what it should), smaller is a clash. This is what hid J1 and J30 before.
TOUCH = {
    "J30": "NFC antenna (Molex 146236)",       # pogo pin 1 presses on the antenna tab
    "J35": "NFC antenna (Molex 146236)",       # pogo pin 2
    "LS70": "speaker (Same Sky CMS-16093)",    # speaker springs land on these pads
    "SW70": "Talk plunger (fingerprint back)", # the plunger on the floating fingerprint module presses the dome
    "J1": "screen FPC plug (on J1)",           # the screen FPC plugs into J1
    "J4": "USB-C bracket",                     # the bracket sits on the USB-C shell
    "M70": "LRA tail",                         # spring contact presses the LRA flex tail pads
}
TOUCH_TOL = 0.2
BOARD_ONLY_H = {"H": (0.9, "M1.4 screw head")}    # board-only footprints (no PARTS entry): height above the board
PLATE_HOLES = ("screen", "fingerprint rim")
# parts whose real shape is not their courtyard: square (side, height) boxes centred on the part (module STEP
# esp32-p4-module_20250730.stp: 25 x 25 board 0.8 thick, shield 22.2 x 22.2 up to 3.3)
SHAPES = {"U1": [(25.0, 0.8), (22.2, 3.3)]}

def overlap(bb, o):
    x0, y0, x1, y1 = bb; shape, g = o[2], o[3]
    if shape == "plate": return True
    if shape == "rect":
        cx, cy, w, h = g; return x0 < cx + w / 2 and x1 > cx - w / 2 and y0 < cy + h / 2 and y1 > cy - h / 2
    cx, cy, r = g
    nx, ny = min(max(cx, x0), x1), min(max(cy, y0), y1)
    return math.hypot(nx - cx, ny - cy) < r

def plate_hole(bb, o):
    """the front plate has holes where the screen glass and the fingerprint sit"""
    if o[0] != "cover glass": return False
    for other in objects():
        if other[0] in PLATE_HOLES and overlap(bb, other):
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            if other[2] == "rect":
                ox, oy, w, h = other[3]
                if abs(cx - ox) < w / 2 and abs(cy - oy) < h / 2: return True
            else:
                ox, oy, r = other[3]
                if math.hypot(cx - ox, cy - oy) < r: return True
    return False

def check(f, bb, h, val, Z, clashes, tight, slack, seen):
    for o in objects():
        if o[1] != f["side"] or not overlap(bb, o) or plate_hole(bb, o): continue
        if f["side"] == "F": gap = o[4] - (Z["pcb1"] + h)
        else:                gap = (Z["pcb0"] - h) - o[5]
        row = (round(gap, 2), f["ref"], val, h, o[0])
        if f["ref"] in TOUCH and TOUCH[f["ref"]] == o[0]:
            seen.add(f["ref"])
            if gap > TOUCH_TOL: clashes.append((round(gap, 2), f["ref"], "NO CONTACT: " + val, h, o[0]))
            elif gap < -TOUCH_TOL: clashes.append(row)
            continue
        if gap < 0: clashes.append(row)
        elif gap < MIN_GAP: tight.append(row)
        slack[o[0]] = min(slack.get(o[0], 99), gap)

def run(quiet=False):
    Z = z(); s = STACK
    H = {}
    for f in sorted(glob.glob(os.path.join(HERE, "sch_*.py"))):
        sp = importlib.util.spec_from_file_location("m", f); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        for p in m.PARTS: H[p["ref"]] = (p.get("h", 1.0), p["value"])
    parts = json.load(open(SRC))
    MOUNTS[:] = [(f["ref"], f["x"], f["y"]) for f in parts if f["ref"] not in H and f["ref"].rstrip("0123456789") == "H"]
    for ref, x, y in MOUNTS:      # H2/H3 heads sit on the 0.2 mm bracket tabs
        H[ref] = (BOARD_ONLY_H["H"][0] + (0.2 if abs(y + 49.5) < 2 and abs(x) < 8 else 0), BOARD_ONLY_H["H"][1])
    clashes, tight, slack = [], [], {}
    seen = set()
    for f in parts:
        xs = [p[0] for p in f["court"]]; ys = [p[1] for p in f["court"]]
        boxes = [((min(xs), min(ys), max(xs), max(ys)), H[f["ref"]][0])]
        if f["ref"] in SHAPES: boxes = [((f["x"] - a / 2, f["y"] - a / 2, f["x"] + a / 2, f["y"] + a / 2), hh) for a, hh in SHAPES[f["ref"]]]
        for bb, h in boxes:
            check(f, bb, h, H[f["ref"]][1], Z, clashes, tight, slack, seen)
    for ref, o in TOUCH.items():
        if ref not in seen: clashes.append((0, ref, "NO CONTACT: not under its object at all", 0, o))
    # off-board objects vs each other (same side, overlapping in plan and in z)
    obs = [o for o in objects() if o[2] != "plate"]
    for i, a in enumerate(obs):
        for b in obs[i + 1:]:
            if {a[0], b[0]} in ({"fingerprint rim", "fingerprint body"}, {"LRA (VG0832009L)", "LRA tail"}) or (a[0].startswith("screen") and b[0].startswith("screen")): continue
            ga = (a[3][0] - (a[3][2] / 2 if a[2] == "rect" else a[3][2]), a[3][1] - (a[3][3] / 2 if a[2] == "rect" else a[3][2]),
                  a[3][0] + (a[3][2] / 2 if a[2] == "rect" else a[3][2]), a[3][1] + (a[3][3] / 2 if a[2] == "rect" else a[3][2]))
            if overlap(ga, b) and a[4] < b[5] - 1e-6 and b[4] < a[5] - 1e-6:
                clashes.append((round(-min(a[5] - b[4], b[5] - a[4]), 2), a[0], "", 0, b[0]))
    # cavity: every object inside the inner walls
    iw, ih = s["body_w"] / 2 - s["side_wall"], s["body_h"] / 2 - s["side_wall"]
    for o in obs:
        if o[2] == "rect":
            cx, cy, w, h = o[3]
            if abs(cx) + w / 2 > iw + 1e-6 or abs(cy) + h / 2 > ih + 1e-6:
                clashes.append((0, o[0], "outside the cavity", 0, "side wall"))
    if not quiet:
        print(f"stack (z from the back face): back wall 0-{s['back_wall']}, battery {Z['batt0']:.2f}-{Z['batt1']:.2f}, "
              f"PCB {Z['pcb0']:.2f}-{Z['pcb1']:.2f}, screen from {Z['screen0']:.2f}, cover glass from {Z['cover0']:.2f}, top {s['body_t']}")
        print(f"room above the board: {Z['screen0'] - Z['pcb1']:.2f} mm under the screen panel, {Z['cover0'] - Z['pcb1']:.2f} mm under the cover glass; "
              f"below: {Z['pcb0'] - s['back_wall']:.2f} mm to the back wall")
        for title, rows in (("CLASH", clashes), ("TIGHT (< %.2f mm)" % MIN_GAP, tight)):
            for g, ref, val, h, o in sorted(rows):
                print(f"{title:6} {ref:6} {val[:28]:28} h {h:4.2f}  vs {o:24} gap {g:+.2f} mm")
        print("smallest gap per object (wasted air if large):", ", ".join(f"{k} {v:.2f}" for k, v in sorted(slack.items(), key=lambda x: x[1])))
        print("RESULT:", "FITS" if not clashes else f"{len(clashes)} CLASH(ES)")
    return clashes, tight, slack

if __name__ == "__main__":
    c, _, _ = run(); sys.exit(1 if c else 0)
