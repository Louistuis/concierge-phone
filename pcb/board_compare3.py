"""Board 1.0 vs 1.1 vs 1.2 in one picture:  python3 board_compare3.py [out.png]
Reads shots/board_v1.0.json, board_v1.1.json, board_v1.2.json (export_view.py of each version). Six boards in a row: side A
1.0 / 1.1 / 1.2, then side B 1.0 / 1.1 / 1.2. Changes 1-11 (fit pass, 1.0 to 1.1) are orange on 1.0 and cyan on 1.1;
changes 12-19 (review fixes, 1.1 to 1.2) are outlined grey where they were on 1.1 and green on 1.2. The numbered list
under the boards says what changed and why."""
import json, os, sys, math
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "shots", "board_compare_1.0_1.1_1.2.png")
V = {v: {f["ref"]: f for f in json.load(open(os.path.join(HERE, "shots", f"board_v{v}.json")))} for v in ("1.0", "1.1", "1.2")}
S = 2; MM = 9 * S
BW, BH = 50 * MM, 102 * MM
GAP, SIDEGAP, PAD, TOP = 55 * S, 110 * S, 60 * S, 215 * S
COLS, ROW_H = 4, 112 * S
W = PAD * 2 + 6 * BW + 4 * GAP + SIDEGAP
H = TOP + BH + 90 * S + 2 * 60 * S + 3 * ROW_H + 2 * ROW_H + 40 * S

def font(sz, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", sz, index=1 if bold else 0)
    except OSError: return ImageFont.load_default()
F, FB, FT, FS, FBADGE, FH = font(20 * S), font(20 * S, True), font(36 * S, True), font(16 * S), font(15 * S, True), font(24 * S, True)
COL = {"1.0": (255, 150, 60), "1.1": (60, 210, 230), "1.2": (140, 230, 110)}
GREY = (170, 175, 185)
BG, BOARD, EDGE = (20, 22, 26), (22, 64, 42), (120, 170, 130)

# (n, group, refs, title, detail, flags)   group "A" = 1.0 to 1.1, "B" = 1.1 to 1.2
CHANGES = [
    (1, "A", ["J1"], "Screen plug moved under the screen", "The screen's ribbon folds behind the panel and ends ~12 mm above its centre, so the plug moved up to (0, 35.8).", ""),
    (2, "A", ["D700", "D701", "D702", "D703"], "Talk ring 1.35 mm higher, LEDs re-spaced", "Room for the LTE antenna under the bottom glass; ring LEDs at 30/150/210/330 degrees to clear the modem.", "ring"),
    (3, "A", ["SW70"], "Talk key: click switch to 0.35 mm snap dome", "The 1.6 mm switch didn't fit under the fingerprint sensor. A metal dome is what phones use.", ""),
    (4, "A", ["U36"], "IR receiver: 4.0 mm to 0.8 mm Vishay", "The old one hit the front glass. Vishay TSOP57338: flat, 40 m range, Sony/NEC/RC5.", ""),
    (5, "A", ["LS70"], "Speaker: Same Sky driver, bigger spot", "Same Sky CMS-16093 (16 x 9 x 3 mm) on spring pads, sound chamber built into the case.", ""),
    (6, "A", ["M70"], "Vibration motor moved, glued under the glass", "Old spot was full of tall parts; now right of the Talk ring, under your thumb.", ""),
    (7, "A", ["J30", "J31"], "NFC contacts 0.6 mm up", "Follows the NFC antenna, which moved up to clear the fingerprint ring.", ""),
    (8, "A", ["U11"], "Faster charging, charger to side B", "~1 A charging, full in ~3 h instead of ~5.5 h.", ""),
    (9, "A", [], "Battery 43 x 62 x 6 to 50 x 60 x 7.3 mm", "The old space held ~1700 mAh; the new one a real 2500 mAh cell, full inside width.", "battery"),
    (10, "A", ["J3", "J10"], "Camera plug + battery plug nudged", "Room for the wider battery and the microSD slot.", ""),
    (11, "A", ["U74"], "Vibration driver to side A", "Placed next to the motor's new spot.", ""),
    (12, "B", ["H1", "H2", "H3", "H4", "H5"], "5 board screws + USB-C bracket", "1.1 had no holes at all. M1.4 screws into posts in the case; the posts set the board height, so a swelling battery can't push it into the screen. H2 + H3 hold a steel bracket over the USB-C.", "each"),
    (13, "B", ["J30", "J35"], "NFC: 2 pogo pins that reach the antenna", "The old contacts stopped 1.33 mm short. KERUI KTR47003UT01-R pins (works 3.65-4.20 mm, gap is 3.83), placed by JLC.", ""),
    (14, "B", ["LS70"], "Speaker pads on the real contact spot", "Same Sky's drawing puts the springs 7.55 mm from the centre, not 7.0. Box 0.45 mm right of screw H3.", ""),
    (15, "B", ["J4"], "USB-C 1.2 mm further out", "The mouth sat 2.7 mm behind the case surface, too deep for many plugs to click in. Now ~1.2 mm.", ""),
    (16, "B", ["U36"], "IR receiver out from under the Wi-Fi antenna", "The Wi-Fi flex covered its window. Now top right, clear of both antennas.", ""),
    (17, "B", ["U20", "Q100"], "Safe charging on any USB port", "New TI TUSB320LA reads what the charger offers: 1.4 A only from 1.5 A / 3 A USB-C chargers, 0.5 A from laptops and USB-A. No firmware.", ""),
    (18, "B", ["U71"], "Bottom mic moved for screw H2", "1.5 mm left; its sound hole channel in the case moves with it.", ""),
    (19, "B", ["R118", "F100", "R19"], "Radio power, fuse and SIM fixes", "Radio rail limit 352 to 564 mA (NFC needs ~250), 2 A fuse for the faster charging, SIM data pull-up from Quectel's reference.", "each"),
]
BATT = {"1.0": (-21.5, -41.0, 21.5, 21.0), "1.1": (-25.0, -41.0, 25.0, 19.0), "1.2": (-25.0, -41.0, 25.0, 19.0)}
MAH = {"1.0": "battery ~1700 mAh", "1.1": "battery 2500 mAh", "1.2": "battery 2500 mAh"}
TALK = {"1.0": (0.0, -32.0), "1.1": (0.0, -30.65), "1.2": (0.0, -30.65)}
SPK = {"1.1": 15.6, "1.2": 17.05}
PANELS = [("F", "1.0"), ("F", "1.1"), ("F", "1.2"), ("B", "1.0"), ("B", "1.1"), ("B", "1.2")]
LABELS = []

def origin(i): return PAD + i * (BW + GAP) + (SIDEGAP - GAP if i >= 3 else 0), TOP

def dashed(d, a, b, col, w=2):
    x0, x1 = sorted((a[0], b[0])); y0, y1 = sorted((a[1], b[1]))
    for p, q in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        L = math.hypot(q[0] - p[0], q[1] - p[1]); n = max(1, int(L / (9 * S)))
        for i in range(0, n, 2):
            t0, t1 = i / n, min(1, (i + 1) / n)
            d.line([p[0] + (q[0] - p[0]) * t0, p[1] + (q[1] - p[1]) * t0, p[0] + (q[0] - p[0]) * t1, p[1] + (q[1] - p[1]) * t1], fill=col, width=w * S)

def role(ref, v):
    """how a part is drawn on board v: 'new' (fill), 'was' (outline), or None"""
    for n, g, refs, *_ in CHANGES:
        if ref not in refs: continue
        if g == "A" and v in ("1.0", "1.1"): return "new" if v == "1.1" else "old"
        if g == "B" and v == "1.2": return "new"
        if g == "B" and v == "1.1": return "was"
    return None

def draw_board(d, ox, oy, side, v):
    mir = -1 if side == "B" else 1
    P = lambda x, y: (ox + (mir * x + 25) * MM, oy + (51 - y) * MM)
    d.rounded_rectangle([ox, oy, ox + BW, oy + BH], radius=4 * MM, fill=BOARD, outline=EDGE, width=2 * S)
    c = COL[v]
    if side == "F":
        dashed(d, P(-16.8, 44.0), P(16.8, 2.8), (200, 200, 200))
        a = P(0, 44.0); LABELS.append((a[0], a[1] + 18 * S, "screen sits here", FS, (210, 210, 210)))
        cx, cy = P(*TALK[v]); r = 10 * MM
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(235, 235, 235), width=2 * S)
    else:
        x0, y0, x1, y1 = BATT[v]; a, b = P(x0, y1), P(x1, y0)
        d.rectangle([min(a[0], b[0]), a[1], max(a[0], b[0]), b[1]], fill=(28, 74, 50) if v == "1.0" else (24, 70, 78))
        dashed(d, a, b, COL["1.0"] if v == "1.0" else COL["1.1"])
        LABELS.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, MAH[v], FB, COL["1.0"] if v == "1.0" else COL["1.1"]))
    for ref, f in V[v].items():
        if f["side"] != side: continue
        pts = [P(x, y) for x, y in f["court"]]; ro = role(ref, v)
        if ro in ("new", "old"): d.polygon(pts, fill=c + (205,), outline=c + (255,))
        elif ro == "was": d.polygon(pts, outline=GREY + (255,), width=2 * S)
        else: d.polygon(pts, outline=(60, 105, 75), width=S)
        for p in f["pads"]:
            if p["npth"]:
                if ref.startswith("H"):
                    cx, cy = P(p["x"], p["y"]); r = 0.8 * MM; d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(10, 10, 12))
                continue
            cx, cy = P(p["x"], p["y"]); w, h = p["w"] * MM / 2, p["h"] * MM / 2
            if int(round(p["a"])) % 180 == 90: w, h = h, w
            d.rectangle([cx - w, cy - h, cx + w, cy + h], fill=(214, 178, 72) if ro else (150, 128, 60))
    if side == "F" and v in SPK:     # off-board parts that sit above the board: speaker box, LRA, USB-C bracket
        sc = SPK[v]; dashed(d, P(sc - 8, -41.6), P(sc + 8, -50.6), c)
        cx, cy = P(20.0, -34.5); r = 4 * MM; d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=2 * S)
        if v == "1.2": dashed(d, P(-6.3, -48.0), P(6.3, -51.0), c)
    if v == "1.2":                   # screw heads (front) / bosses (back)
        for ref in ("H1", "H2", "H3", "H4", "H5"):
            f = V[v][ref]; cx, cy = P(f["x"], f["y"]); r = (1.3 if side == "F" else 1.5) * MM
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=2 * S)
    return P

def badge(d, x, y, n, col, hollow=False):
    r = 13 * S
    d.ellipse([x - r, y - r, x + r, y + r], fill=(15, 15, 18), outline=col, width=(2 if hollow else 3) * S)
    t = str(n); d.text((x, y), t, font=FBADGE, fill=(255, 255, 255) if not hollow else GREY, anchor="mm")

img = Image.new("RGBA", (W, H), BG + (255,))
lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
Pf = {}
for i, (side, v) in enumerate(PANELS):
    ox, oy = origin(i); Pf[(side, v)] = draw_board(d, ox, oy, side, v)
    d.text((ox + BW / 2, oy - 26 * S), f"{'Side A' if side == 'F' else 'Side B'}  {v}", font=FB, fill=COL[v], anchor="mm")
for side, x in (("F", origin(0)[0]), ("B", origin(3)[0])):
    pass
img = Image.alpha_composite(img, lay); d = ImageDraw.Draw(img)
for cx, cy, text, fnt, col in LABELS:
    tw = d.textlength(text, font=fnt); hh = fnt.size * 0.75
    d.rounded_rectangle([cx - tw / 2 - 10 * S, cy - hh, cx + tw / 2 + 10 * S, cy + hh], radius=int(hh), fill=(15, 17, 20))
    d.text((cx, cy), text, font=fnt, fill=col, anchor="mm")
# badges
def spots(refs, v, each):
    pts = [(V[v][r]["x"], V[v][r]["y"], V[v][r]["side"]) for r in refs if r in V[v]]
    if each: return [(x, y, s) for x, y, s in pts]
    out = []
    for s in {p[2] for p in pts}:
        sel = [p for p in pts if p[2] == s]; out.append((sum(p[0] for p in sel) / len(sel), sum(p[1] for p in sel) / len(sel), s))
    return out
for n, g, refs, title, detail, flag in CHANGES:
    boards = (("1.0", False), ("1.1", False)) if g == "A" else (("1.1", True), ("1.2", False))
    for v, hollow in boards:
        col = GREY if hollow else COL[v]
        if flag == "battery":
            x0, y0, x1, y1 = BATT[v]; x, y = Pf[("B", v)](x1 - 3, y0 + 6); badge(d, x, y, n, col, hollow); continue
        for x, y, s in spots(refs, v, flag == "each"):
            if flag == "ring": x, y = TALK[v][0], TALK[v][1] + 6.5
            px, py = Pf[(s, v)](x, y); badge(d, px + 15 * S, py - 15 * S, n, col, hollow)
# header
d.text((PAD, 38 * S), "Concierge phone board: 1.0 to 1.1 to 1.2", font=FT, fill=(245, 245, 245))
d.text((PAD, 94 * S), "Body 13.5 to 14.9 mm   |   board 1.6 to 1.0 mm   |   battery ~1700 to 2500 mAh   |   5 screws + USB-C bracket   |   "
       "charging ~5.5 h to ~3 h, safe on any USB port   |   no part downgraded", font=F, fill=(200, 205, 212))
lx = PAD
for v, txt in (("1.0", "1.0 original"), ("1.1", "1.1 fit pass (14.9 mm body, 2500 mAh)"), ("1.2", "1.2 review fixes (tonight)")):
    d.rounded_rectangle([lx, 132 * S, lx + 18 * S, 150 * S], radius=4 * S, fill=COL[v]); d.text((lx + 26 * S, 132 * S), txt, font=FS, fill=(200, 205, 212))
    lx += d.textlength(txt, font=FS) + 70 * S
d.text((lx, 132 * S), "Grey outline + grey number = where a 1.2 change sat on 1.1. Unmarked parts were re-packed by the placer.", font=FS, fill=(150, 155, 162))
# lists
def wrap(text, width, fnt):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=fnt) <= width: cur = t
        else: lines.append(cur); cur = w_
    return lines + [cur]
y = TOP + BH + 60 * S; colw = (W - 2 * PAD) / COLS
for g, head in (("A", "1.0 to 1.1: fit pass"), ("B", "1.1 to 1.2: review fixes")):
    d.text((PAD, y), head, font=FH, fill=COL["1.1" if g == "A" else "1.2"]); y += 48 * S
    items = [c for c in CHANGES if c[1] == g]
    for k, (n, _, refs, title, detail, _) in enumerate(items):
        cx = PAD + (k % COLS) * colw; cy = y + (k // COLS) * ROW_H
        badge(d, cx + 14 * S, cy + 12 * S, n, COL["1.1" if g == "A" else "1.2"])
        d.text((cx + 38 * S, cy), title, font=FB, fill=(240, 240, 240))
        for j, line in enumerate(wrap(detail, colw - 60 * S, FS)[:3]):
            d.text((cx + 38 * S, cy + 30 * S + j * 21 * S), line, font=FS, fill=(165, 170, 178))
    y += ((len(items) + COLS - 1) // COLS) * ROW_H + 12 * S
img = img.crop((0, 0, W, min(H, int(y + 20 * S))))
img.convert("RGB").resize((img.width // S, img.height // S), Image.LANCZOS).save(OUT)
print(OUT, img.width // S, "x", img.height // S)
