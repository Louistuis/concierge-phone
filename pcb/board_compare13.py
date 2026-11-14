"""Board 1.2 vs 1.3 in one picture:  python3 board_compare13.py [out.png]  (made from board_compare3.py)
Reads shots/board_v1.0.json, board_v1.1.json, board_v1.2.json (export_view.py of each version). Six boards in a row: side A
1.0 / 1.1 / 1.2, then side B 1.0 / 1.1 / 1.2. Changes 1-11 (fit pass, 1.0 to 1.1) are orange on 1.0 and cyan on 1.1;
changes 12-19 (review fixes, 1.1 to 1.2) are outlined grey where they were on 1.1 and green on 1.2. The numbered list
under the boards says what changed and why."""
import json, os, sys, math
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "shots", "board_compare_1.2_1.3.png")
V = {v: {f["ref"]: f for f in json.load(open(os.path.join(HERE, "shots", f"board_v{v}.json")))} for v in ("1.2", "1.3")}
S = 2; MM = 9 * S
BW, BH = 50 * MM, 102 * MM
GAP, SIDEGAP, PAD, TOP = 55 * S, 110 * S, 60 * S, 215 * S
COLS, ROW_H = 4, 112 * S
W = PAD * 2 + 4 * BW + 2 * GAP + SIDEGAP
H = TOP + BH + 90 * S + 2 * 60 * S + 3 * ROW_H + 2 * ROW_H + 40 * S

def font(sz, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", sz, index=1 if bold else 0)
    except OSError: return ImageFont.load_default()
F, FB, FT, FS, FBADGE, FH = font(20 * S), font(20 * S, True), font(36 * S, True), font(16 * S), font(15 * S, True), font(24 * S, True)
COL = {"1.2": (60, 210, 230), "1.3": (255, 196, 70)}
GREY = (170, 175, 185)
BG, BOARD, EDGE = (20, 22, 26), (22, 64, 42), (120, 170, 130)

# (n, group, refs, title, detail, flags)   group "A" = 1.0 to 1.1, "B" = 1.1 to 1.2
CHANGES = [
    (20, "C", ["U1"], "Chip module left and turned around", "The screen is 2.6 mm deep with a 1 mm bump on the right; the module's 3.3 mm shield now sits left of it.", ""),
    (21, "C", ["J1"], "Screen plug on Waveshare's exact spot", "(0, 35.45), 6.2 mm under the glass like Waveshare's own board, so the screen cable fits as made.", ""),
    (22, "C", ["SW71", "SW72", "SW73"], "All three side keys on the right", "Volume up, volume down, power. The module now covers the left edge.", "each"),
    (23, "C", ["U2", "J5"], "LTE modem 2 mm left, 1 mm down", "Room for its antenna plug in a strip under the module, feed in one straight row.", ""),
    (24, "C", ["J6"], "Wi-Fi antenna plug moved east", "Follows the module's antenna pad, now facing right.", ""),
    (25, "C", ["J30", "J35"], "Taller NFC pins (5.5 mm)", "The board sits 0.6 mm lower in the thicker body; BAT Wireless pins reach the antenna, JLC fits them.", ""),
    (26, "C", ["M70"], "Vibration motor: no wires", "Vybronics VG0832009L press-fit motor; JLC solders a spring under its contact tail.", ""),
    (27, "C", ["J31"], "125 kHz coil: ready-made", "Coilcraft 4308RV-404 instead of a hand-wound coil, sent to JLC with the module.", ""),
    (28, "C", ["H4"], "Screw H4 1.8 mm up", "Makes room for the volume-up key on the right edge.", ""),
    (29, "C", ["U71", "U72"], "Both mics back at their sound holes", "Fix: their fixed spots had slipped into a code comment in 1.2 and the placer put them mid-board.", "each"),
    (30, "C", [], "Battery 2400 mAh LiPol, 50 x 58 x 6.6 mm", "The 2500 mAh cell was really up to 8.1 mm thick. This one has the temperature sensor and plug built in.", "battery"),
]
BATT = {"1.2": (-25.0, -41.0, 25.0, 19.0), "1.3": (-25.0, -41.0, 25.0, 17.0)}
MAH = {"1.2": "battery 2500 mAh (really up to 8.1 mm)", "1.3": "battery 2400 mAh LiPol"}
TALK = {"1.2": (0.0, -30.65), "1.3": (0.0, -30.65)}
SPK = {"1.2": 17.05, "1.3": 17.05}
PANELS = [("F", "1.2"), ("F", "1.3"), ("B", "1.2"), ("B", "1.3")]
LABELS = []

def origin(i): return PAD + i * (BW + GAP) + (SIDEGAP - GAP if i >= 2 else 0), TOP

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
        if v == "1.3": return "new"
        if v == "1.2": return "was"
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
        d.rectangle([min(a[0], b[0]), a[1], max(a[0], b[0]), b[1]], fill=(24, 70, 78) if v == "1.2" else (70, 60, 30))
        dashed(d, a, b, COL[v])
        LABELS.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, MAH[v], FB, COL[v]))
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
        dashed(d, P(-6.3, -48.0), P(6.3, -51.0), c)
    if side == "F" and v == "1.3":   # 1.3: what sits under the screen (driver bump, flex parts, cable loop)
        for x0, y0, x1, y1 in ((2.3, 18.28, 12.07, 31.0), (6.64, 3.6, 13.36, 15.35), (-4.7, 31.85, 4.7, 38.85)):
            dashed(d, P(x0, y1), P(x1, y0), (235, 120, 120))
    if True:                         # screw heads (front) / bosses (back)
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
    boards = (("1.2", True), ("1.3", False))
    for v, hollow in boards:
        col = GREY if hollow else COL[v]
        if flag == "battery":
            x0, y0, x1, y1 = BATT[v]; x, y = Pf[("B", v)](x1 - 3, y0 + 6); badge(d, x, y, n, col, hollow); continue
        for x, y, s in spots(refs, v, flag == "each"):
            if flag == "ring": x, y = TALK[v][0], TALK[v][1] + 6.5
            px, py = Pf[(s, v)](x, y); badge(d, px + 15 * S, py - 15 * S, n, col, hollow)
# header
d.text((PAD, 38 * S), "Concierge phone board: 1.2 to 1.3", font=FT, fill=(245, 245, 245))
d.text((PAD, 94 * S), "Body 14.9 to 15.5 mm (screen at Waveshare's own height)   |   JLC 1.0 mm impedance stackup   |   no hand soldering   |   "
       "fit check: 0 clashes", font=F, fill=(200, 205, 212))
lx = PAD
for v, txt in (("1.2", "1.2 (last night)"), ("1.3", "1.3 (this morning)")):
    d.rounded_rectangle([lx, 132 * S, lx + 18 * S, 150 * S], radius=4 * S, fill=COL[v]); d.text((lx + 26 * S, 132 * S), txt, font=FS, fill=(200, 205, 212))
    lx += d.textlength(txt, font=FS) + 70 * S
d.text((lx, 132 * S), "Grey = where it sat on 1.2. Red dashes = screen bump, flex parts, cable loop. Unmarked parts were re-packed by the placer.", font=FS, fill=(150, 155, 162))
# lists
def wrap(text, width, fnt):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=fnt) <= width: cur = t
        else: lines.append(cur); cur = w_
    return lines + [cur]
y = TOP + BH + 60 * S; colw = (W - 2 * PAD) / COLS
for g, head in (("C", "1.2 to 1.3: 15.5 mm body, real screen, click-together parts"),):
    d.text((PAD, y), head, font=FH, fill=COL["1.3"]); y += 48 * S
    items = [c for c in CHANGES if c[1] == g]
    for k, (n, _, refs, title, detail, _) in enumerate(items):
        cx = PAD + (k % COLS) * colw; cy = y + (k // COLS) * ROW_H
        badge(d, cx + 14 * S, cy + 12 * S, n, COL["1.3"])
        d.text((cx + 38 * S, cy), title, font=FB, fill=(240, 240, 240))
        for j, line in enumerate(wrap(detail, colw - 60 * S, FS)[:3]):
            d.text((cx + 38 * S, cy + 30 * S + j * 21 * S), line, font=FS, fill=(165, 170, 178))
    y += ((len(items) + COLS - 1) // COLS) * ROW_H + 12 * S
img = img.crop((0, 0, W, min(H, int(y + 20 * S))))
img.convert("RGB").resize((img.width // S, img.height // S), Image.LANCZOS).save(OUT)
print(OUT, img.width // S, "x", img.height // S)
