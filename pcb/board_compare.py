"""Before/after picture of the 2026-11-14 fit pass:  python3 board_compare.py <before board.json> [after board.json] [out.png]
Four boards in a row (side A before/after, side B before/after). Every deliberate change has a numbered badge at the same
spot on both its 'before' and 'after' board (orange = old, cyan = new); the list under the boards says what changed and
why. Small parts that the placer simply reshuffled are left unmarked (Quilter places those again anyway)."""
import json, os, sys, math
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
BEFORE = sys.argv[1]
AFTER = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "shots", "board.json")
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "shots", "board_compare.png")
S = 2; MM = 11 * S
BW, BH = 50 * MM, 102 * MM
GAP, PAD, TOP = 70 * S, 60 * S, 200 * S
LIST_H = 520 * S
W = PAD * 2 + 4 * BW + 3 * GAP + 40 * S
H = TOP + BH + 70 * S + LIST_H

def font(sz, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", sz, index=1 if bold else 0)
    except OSError: return ImageFont.load_default()
F, FB, FT, FS, FBADGE = font(20 * S), font(20 * S, True), font(34 * S, True), font(16 * S), font(15 * S, True)
OLD, NEW = (255, 150, 60), (60, 210, 230)
BG, BOARD, EDGE = (20, 22, 26), (22, 64, 42), (120, 170, 130)

before = {f["ref"]: f for f in json.load(open(BEFORE))}
after = {f["ref"]: f for f in json.load(open(AFTER))}

# (number, side shown, refs, short title, detail). 'side' None = follow each part's own side.
CHANGES = [
    (1, "F", ["J1"], "Screen plug moved under the screen",
     "The real screen's ribbon folds behind the panel and ends ~12 mm above its centre, so the plug moved from the middle of the board up to (0, 35.8)."),
    (2, "F", ["D700", "D701", "D702", "D703"], "Talk ring 1.35 mm higher, LEDs re-spaced",
     "Makes room for the LTE antenna under the bottom glass; the 4 ring LEDs moved to 30/150/210/330 degrees to clear the modem."),
    (3, "F", ["SW70"], "Talk key: click switch to 0.35 mm snap dome",
     "The 1.6 mm switch didn't fit under the fingerprint sensor. A metal dome is what phones use: thinner and a crisper click."),
    (4, "F", ["U36"], "IR receiver: 4.0 mm to 0.8 mm Vishay",
     "The old one hit the front glass. Vishay TSOP57338: flat, 40 m range, reads Sony/NEC/RC5 remotes."),
    (5, "F", ["LS70"], "Speaker: Same Sky driver, bigger spot",
     "No 1511 box speaker exists at this size, so a Same Sky CMS-16093 (16 x 9 x 3 mm) on spring pads, with its sound chamber built into the case."),
    (6, "F", ["M70"], "Vibration motor moved, glued under the glass",
     "Its old spot was full of tall parts. Now at the right of the Talk ring, so you feel it right under your thumb."),
    (7, "F", ["J30", "J31"], "NFC contacts 0.6 mm up",
     "Follows the NFC antenna, which moved up so it clears the fingerprint ring."),
    (8, None, ["U11"], "Faster charging, charger moved to side B",
     "Two resistor values changed: ~1 A charging, full in ~3 h instead of ~5.5 h. The placer put the charger chip on side B."),
    (9, "B", [], "Battery 43 x 62 x 6 to 50 x 60 x 7.3 mm",
     "The old space only held ~1700 mAh. The new one holds a real 2500 mAh cell, using the full inside width."),
    (10, "B", ["J3", "J10"], "Camera plug + battery plug nudged",
     "Room for the wider battery and the microSD slot."),
    (11, None, ["U74"], "Vibration driver moved to side A",
     "The placer moved it next to the motor's new spot."),
]
BATT_OLD, BATT_NEW = (-21.5, -41.0, 21.5, 21.0), (-25.0, -41.0, 25.0, 19.0)
TALK_OLD, TALK_NEW = (0.0, -32.0), (0.0, -30.65)

LABELS = []   # (cx, cy, text, font, colour), drawn last on dark pills so parts never cover them

def panel_origin(i): return PAD + i * (BW + GAP), TOP

def draw_board(d, ox, oy, data, side, state):
    mir = -1 if side == "B" else 1
    P = lambda x, y: (ox + (mir * x + 25) * MM, oy + (51 - y) * MM)
    d.rounded_rectangle([ox, oy, ox + BW, oy + BH], radius=4 * MM, fill=BOARD, outline=EDGE, width=2 * S)
    col = OLD if state == "before" else NEW
    marked = {r for _, s, refs, _, _ in CHANGES for r in refs}
    # screen outline (both states, side A) and battery (side B)
    if side == "F":
        a, b = P(-16.8, 44.0), P(16.8, 2.8)
        dashed_rect(d, a, b, (200, 200, 200), "screen sits here (glass side)", oy)
        t = TALK_OLD if state == "before" else TALK_NEW
        cx, cy = P(*t); r = 10 * MM
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(235, 235, 235), width=2 * S)
    else:
        x0, y0, x1, y1 = BATT_OLD if state == "before" else BATT_NEW
        a, b = P(x0, y1), P(x1, y0)
        d.rectangle([min(a[0], b[0]), a[1], max(a[0], b[0]), b[1]], fill=(28, 74, 50) if state == "before" else (24, 70, 78))
        dashed_rect(d, a, b, col, None, oy)
        lab = "battery ~1700 mAh" if state == "before" else "battery 2500 mAh"
        LABELS.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, lab, FB, col))
    for ref, f in data.items():
        if f["side"] != side: continue
        pts = [P(x, y) for x, y in f["court"]]
        if ref in marked: d.polygon(pts, fill=col + (200,), outline=col + (255,))
        else: d.polygon(pts, outline=(60, 105, 75), width=S)
        for p in f["pads"]:
            if p["npth"]: continue
            cx, cy = P(p["x"], p["y"]); w, h = p["w"] * MM / 2, p["h"] * MM / 2
            if int(round(p["a"])) % 180 == 90: w, h = h, w
            d.rectangle([cx - w, cy - h, cx + w, cy + h], fill=(214, 178, 72) if ref in marked else (150, 128, 60))
    if side == "F" and state == "after":     # off-board parts that moved in with the fit pass
        sx, sy = P(7.6, -41.6); ex, ey = P(23.6, -50.6)
        dashed_rect(d, (sx, sy), (ex, ey), NEW, None, oy)
        cx, cy = P(20.0, -34.5); r = 4 * MM
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=NEW, width=2 * S)
    return P

def dashed_rect(d, a, b, col, text, oy):
    x0, x1 = sorted((a[0], b[0])); y0, y1 = sorted((a[1], b[1]))
    for (p, q) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        L = math.hypot(q[0] - p[0], q[1] - p[1]); n = max(1, int(L / (9 * S)))
        for i in range(0, n, 2):
            t0, t1 = i / n, min(1, (i + 1) / n)
            d.line([p[0] + (q[0] - p[0]) * t0, p[1] + (q[1] - p[1]) * t0, p[0] + (q[0] - p[0]) * t1, p[1] + (q[1] - p[1]) * t1], fill=col, width=2 * S)
    if text:
        LABELS.append(((x0 + x1) / 2, y0 + 18 * S, text, FS, (210, 210, 210)))

def badge(d, x, y, n, col):
    r = 13 * S
    d.ellipse([x - r, y - r, x + r, y + r], fill=(15, 15, 18), outline=col, width=3 * S)
    t = str(n); tw = d.textlength(t, font=FBADGE); d.text((x - tw / 2, y - 10 * S), t, font=FBADGE, fill=(255, 255, 255))

img = Image.new("RGBA", (W, H), BG + (255,))
lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
panels = [("F", "before", before, "Side A  before"), ("F", "after", after, "Side A  after"),
          ("B", "before", before, "Side B  before"), ("B", "after", after, "Side B  after")]
Pf = {}
for i, (side, state, data, title) in enumerate(panels):
    ox, oy = panel_origin(i)
    Pf[(side, state)] = draw_board(d, ox, oy, data, side, state)
    tw = d.textlength(title, font=FB); d.text((ox + BW / 2 - tw / 2, oy - 40 * S), title, font=FB, fill=OLD if state == "before" else NEW)
# badges: at the parts' centre on each board where that part sits
for n, side, refs, short, _ in CHANGES:
    for state, data in (("before", before), ("after", after)):
        if not refs:          # battery
            for s in ("B",):
                P = Pf[(s, state)]; x0, y0, x1, y1 = BATT_OLD if state == "before" else BATT_NEW
                x, y = P(x1 - 3, y0 + 6); badge(d, x, y, n, OLD if state == "before" else NEW)
            continue
        pts = [(data[r]["x"], data[r]["y"], data[r]["side"]) for r in refs if r in data]
        sides = {p[2] for p in pts}
        for s in sides:
            sel = [p for p in pts if p[2] == s]
            mx = sum(p[0] for p in sel) / len(sel); my = sum(p[1] for p in sel) / len(sel)
            if len(sel) > 1 and n == 2: mx, my = (TALK_OLD if state == "before" else TALK_NEW); my += 6.5
            x, y = Pf[(s, state)](mx, my)
            badge(d, x + 15 * S, y - 15 * S, n, OLD if state == "before" else NEW)
img = Image.alpha_composite(img, lay); d = ImageDraw.Draw(img)
for cx, cy, text, fnt, col in LABELS:
    tw = d.textlength(text, font=fnt); hh = fnt.size * 0.75
    d.rounded_rectangle([cx - tw / 2 - 10 * S, cy - hh, cx + tw / 2 + 10 * S, cy + hh], radius=int(hh), fill=(15, 17, 20))
    d.text((cx, cy), text, font=fnt, fill=col, anchor="mm")
d.text((PAD, 40 * S), "What changed in the fit pass", font=FT, fill=(245, 245, 245))
d.text((PAD, 92 * S), "Body 54 x 108 x 13.5 to 14.9 mm   |   board 1.6 to 1.0 mm thick   |   battery ~1700 to 2500 mAh   |   charging ~5.5 h to ~3 h   |   no part downgraded",
       font=F, fill=(200, 205, 212))
d.text((PAD, 128 * S), "Orange = where it was, cyan = where it is now. Dashed cyan on side A: the new speaker box and vibration motor (bought separately, sit above the board). "
       "Unmarked small parts were reshuffled by the placer; Quilter places those again anyway.", font=FS, fill=(150, 155, 162))
# change list in 3 columns
y0 = TOP + BH + 60 * S; colw = (W - 2 * PAD) / 3
def wrap(text, width, fnt):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=fnt) <= width: cur = t
        else: lines.append(cur); cur = w_
    return lines + [cur]
for k, (n, side, refs, short, detail) in enumerate(CHANGES):
    cx = PAD + (k // 4) * colw; cy = y0 + (k % 4) * 122 * S
    badge(d, cx + 14 * S, cy + 12 * S, n, NEW)
    d.text((cx + 38 * S, cy), short, font=FB, fill=(240, 240, 240))
    for j, line in enumerate(wrap(detail, colw - 60 * S, FS)[:4]):
        d.text((cx + 38 * S, cy + 30 * S + j * 21 * S), line, font=FS, fill=(165, 170, 178))
img.convert("RGB").resize((W // S, H // S), Image.LANCZOS).save(OUT)
print(OUT, W // S, "x", H // S)
