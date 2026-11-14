"""Labeled 'what is inside' map of the main board, both sides:  python3 board_map.py [shots/board.json] [out.png]
Reads export_view.py's dump. Key parts are filled by job, every label sits in a column beside the board with a leader
line to its part, spaced so no two labels touch. The back is drawn as seen with the board turned over (x mirrored)."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "shots", "board.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "shots", "board_map.png")

S = 2                       # supersample
MM = 13 * S                 # px per mm
FS, LH = 21 * S, 29 * S     # label font size, minimum label pitch
GAP = 70 * S                # column to board gap (room for the leader elbows)
TOP, BOT = 190 * S, 150 * S
BW, BH = 50 * MM, 102 * MM
def colw(items):            # label column width from the longest label
    return int(max(ImageDraw.Draw(Image.new("L", (1, 1))).textlength(t, font=F) for _, t, _ in items)) + 30 * S


def font(sz, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", sz, index=1 if bold else 0)
    except OSError: return ImageFont.load_default()
F, FB, FT, FN = font(FS), font(FS, True), font(34 * S, True), font(18 * S)


CAT = {   # job -> (fill, text)
    "core": ((70, 130, 230), "Brain and logic"),
    "radio": ((150, 95, 220), "Radios and antennas"),
    "power": ((240, 145, 50), "Power and battery"),
    "sense": ((60, 185, 110), "Sensors"),
    "ui": ((230, 90, 150), "Buttons, sound, light"),
    "conn": ((150, 160, 170), "Plugs and slots"),
}
# (refs, label, job). One label per row; a label pointing at several parts gets one leader per part.
FRONT = [
    (["U1"], "Brain: ESP32-P4 + C6 module (CPU, Wi-Fi 6, Bluetooth)", "core"),
    (["U2"], "4G LTE modem", "radio"),
    (["J2"], "nano-SIM tray", "radio"),
    (["J5"], "LTE antenna plug", "radio"),
    (["J6"], "Wi-Fi antenna plug", "radio"),
    (["J1"], "Screen connector", "conn"),
    (["J4"], "USB-C port", "conn"),
    (["U19"], "USB-C protection", "power"),
    (["U5", "U6"], "USB switches (flashing / BadUSB)", "conn"),
    (["SW70"], "Talk key: snap dome under the fingerprint", "ui"),
    (["J70"], "Fingerprint sensor plug", "sense"),
    (["D700", "D701", "D702", "D703"], "Light ring LEDs (4)", "ui"),
    (["U75"], "Light ring driver", "ui"),
    (["AE30"], "Sub-GHz antenna (433 / 868 MHz)", "radio"),
    (["AE31"], "GPS antenna", "radio"),
    (["U33"], "GPS receiver", "radio"),
    (["U36"], "Infrared receiver", "radio"),
    (["D303", "D304"], "Infrared blaster LEDs", "radio"),
    (["U72"], "Top microphone", "ui"),
    (["U71"], "Bottom microphone", "ui"),
    (["LS70"], "Speaker contacts", "ui"),
    (["U73"], "Speaker amplifier", "ui"),
    (["M70"], "Vibration motor pads (motor on the glass)", "ui"),
    (["SW71"], "Side key (power / camera)", "ui"),
    (["SW72", "SW73"], "Volume keys", "ui"),
    (["SW74"], "Privacy switch (camera + mic off)", "ui"),
    (["U10"], "3.3 V power converter", "power"),
    (["U11"], "Battery charger", "power"),
    (["U12"], "LTE power converter", "power"),
    (["U14", "U16", "U76"], "Power switches (screen, radios, ring)", "power"),
    (["U30"], "NFC reader", "radio"),
    (["J30"], "NFC antenna contacts", "radio"),
    (["J31"], "125 kHz RFID coil contacts", "radio"),
    (["U31"], "Sub-GHz radio (CC1101)", "radio"),
    (["U32"], "LoRa radio (SX1262)", "radio"),
    (["U37", "U38", "U40", "U41"], "Antenna switches", "radio"),
    (["U3", "U4"], "Modem signal level shifters", "core"),
    (["U50", "U51"], "Extra I/O chips", "core"),
    (["U60"], "Secure key chip", "core"),
    (["U52"], "Motion sensor", "sense"),
    (["U53"], "Compass", "sense"),
    (["U55"], "Temperature + humidity", "sense"),
    (["U56"], "Light sensor", "sense"),
]
BACK = [
    (["J3"], "Camera connector", "conn"),
    (["J71"], "microSD card slot", "conn"),
    (["J10"], "Battery plug", "power"),
    (["D102"], "Flashlight LED", "ui"),
    (["U18"], "Flashlight driver", "ui"),
    (["U61"], "Distance sensor (laser ToF)", "sense"),
    (["U57"], "Color sensor", "sense"),
    (["U58"], "1.8 V supply for the color sensor", "power"),
    (["U13"], "Battery fuel gauge", "power"),
    (["U15", "U17"], "Power switches (camera, microSD)", "power"),
    (["U54"], "Air pressure sensor", "sense"),
    (["U59"], "Air quality sensor", "sense"),
    (["U74"], "Vibration driver", "ui"),
    (["U35"], "125 kHz RFID detector", "radio"),
    (["U39"], "Sub-GHz band switch", "radio"),
]

parts = {f["ref"]: f for f in json.load(open(SRC))}
ALL = FRONT + BACK
def on_side(side):
    """every label whose parts sit on this side (parts can change sides when the placer runs again)"""
    out = []
    for refs, text, job in ALL:
        r = [x for x in refs if x in parts and parts[x]["side"] == side]
        if r: out.append((r, text, job))
    return out

def panel(img, d, ox, side, items, title, sub):
    mir = -1 if side == "B" else 1
    items = on_side(side)
    COLW = colw(items); PW = 2 * COLW + 2 * GAP + BW
    bx0 = ox + COLW + GAP
    def P(x, y): return (bx0 + (mir * x + 25) * MM, TOP + (51 - y) * MM)
    # board
    d.rounded_rectangle([bx0, TOP, bx0 + BW, TOP + BH], radius=4 * MM, fill=(22, 64, 42), outline=(120, 170, 130), width=2 * S)
    keyed = {r: job for refs, _, job in items for r in refs}
    for ref, f in parts.items():
        if f["side"] != side: continue
        pts = [P(x, y) for x, y in f["court"]]
        if ref in keyed:
            c = CAT[keyed[ref]][0]
            d.polygon(pts, fill=c + (170,), outline=c + (255,))
        else:
            d.polygon(pts, outline=(70, 120, 85), width=S)
        for p in f["pads"]:
            if p["npth"]: continue
            cx, cy = P(p["x"], p["y"]); w, h = p["w"] * MM / 2, p["h"] * MM / 2
            if int(round(p["a"])) % 180 == 90: w, h = h, w
            d.rectangle([cx - w, cy - h, cx + w, cy + h], fill=(214, 178, 72))
    # overlays
    dash = lambda a, b: [d.line([a[0] + (b[0] - a[0]) * t / 40, a[1] + (b[1] - a[1]) * t / 40,
                                 a[0] + (b[0] - a[0]) * (t + .55) / 40, a[1] + (b[1] - a[1]) * (t + .55) / 40],
                                fill=(255, 255, 255, 200), width=2 * S) for t in range(40)]
    if side == "B":
        a, b = P(-25, 19), P(25, -41)
        x0, x1 = sorted((a[0], b[0]))
        for p, q in (((x0, a[1]), (x1, a[1])), ((x1, a[1]), (x1, b[1])), ((x1, b[1]), (x0, b[1])), ((x0, b[1]), (x0, a[1]))): dash(p, q)
        tx = (x0 + x1) / 2; ty = (a[1] + b[1]) / 2
        for i, t in enumerate(("Battery sits here", "2500 mAh, 50 x 60 x 7.3", "(no parts under it)")):
            tw = d.textlength(t, font=FB if i == 0 else F); d.text((tx - tw / 2, ty - 50 * S + i * 34 * S), t, font=FB if i == 0 else F, fill=(235, 235, 235))
    else:
        cx, cy = P(0, -30.65); r = 10 * MM
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 170), width=2 * S)
        t = "Talk ring"; tw = d.textlength(t, font=FN); ty = cy - 6.5 * MM
        d.rounded_rectangle([cx - tw / 2 - 8 * S, ty - 3 * S, cx + tw / 2 + 8 * S, ty + 23 * S], radius=8 * S, fill=(20, 22, 26, 230))
        d.text((cx - tw / 2, ty), t, font=FN, fill=(240, 240, 240))
    # edge words
    for word, y in (("TOP EDGE", 51), ("BOTTOM EDGE", -51)):
        x, yy = P(0, y); tw = d.textlength(word, font=FN)
        d.text((x - tw / 2, yy + (-30 * S if y > 0 else 8 * S)), word, font=FN, fill=(150, 150, 150))
    # labels: one column per side of the board, picked by where the part is in this view
    rows = []
    for refs, text, job in items:
        tg = [P(parts[r]["x"], parts[r]["y"]) for r in refs]
        mx = sum(p[0] for p in tg) / len(tg); my = sum(p[1] for p in tg) / len(tg)
        rows.append({"text": text, "job": job, "tg": tg, "x": mx, "y": my})
    mid = bx0 + BW / 2
    cols = {"L": [r for r in rows if r["x"] < mid], "R": [r for r in rows if r["x"] >= mid]}
    while abs(len(cols["L"]) - len(cols["R"])) > 6:             # keep both columns usable
        a, b = ("L", "R") if len(cols["L"]) > len(cols["R"]) else ("R", "L")
        mv = max(cols[a], key=lambda r: r["x"]) if a == "L" else min(cols[a], key=lambda r: r["x"])
        cols[a].remove(mv); cols[b].append(mv)
    lo, hi = TOP - 20 * S, TOP + BH + 20 * S
    for k, col in cols.items():
        col.sort(key=lambda r: r["y"])
        ys = [r["y"] for r in col]
        for _ in range(200):                                       # relax: no two rows closer than LH, inside [lo, hi]
            for i in range(1, len(ys)):
                if ys[i] - ys[i - 1] < LH: ys[i] = ys[i - 1] + LH
            if ys and ys[-1] > hi: ys[-1] = hi
            for i in range(len(ys) - 2, -1, -1):
                if ys[i + 1] - ys[i] < LH: ys[i] = ys[i + 1] - LH
            if ys and ys[0] < lo: ys[0] = lo
        for r, y in zip(col, ys):
            c = CAT[r["job"]][0]
            tw = d.textlength(r["text"], font=F)
            if k == "L":
                tx = bx0 - GAP - tw; ex = bx0 - GAP + 8 * S; elbow = bx0 - 18 * S
            else:
                tx = bx0 + BW + GAP; ex = tx - 8 * S; elbow = bx0 + BW + 18 * S
            d.text((tx, y - FS * 0.6), r["text"], font=F, fill=(235, 238, 242))
            d.ellipse([ex - 4 * S if k == "R" else ex - 4 * S, y - 4 * S, ex + 4 * S, y + 4 * S], fill=c)
            for t in r["tg"]:
                d.line([ex, y, elbow, y, t[0], t[1]], fill=c + (230,), width=2 * S, joint="curve")
                d.ellipse([t[0] - 5 * S, t[1] - 5 * S, t[0] + 5 * S, t[1] + 5 * S], fill=(255, 255, 255), outline=c, width=2 * S)
    tw = d.textlength(title, font=FT); d.text((ox + PW / 2 - tw / 2, 40 * S), title, font=FT, fill=(245, 245, 245))
    tw = d.textlength(sub, font=F); d.text((ox + PW / 2 - tw / 2, 92 * S), sub, font=F, fill=(165, 170, 178))

PA = 2 * colw(on_side("F")) + 2 * GAP + BW; PB = 2 * colw(on_side("B")) + 2 * GAP + BW
W, H = PA + 80 * S + PB, TOP + BH + BOT
img = Image.new("RGBA", (W, H), (20, 22, 26, 255))
over = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(over)
panel(over, d, 0, "F", FRONT, "Side A (top of the board)", "faces the screen; 50 x 102 x 1.0 mm, 6 layers")
panel(over, d, PA + 80 * S, "B", BACK, "Side B (board turned over)", "faces the back cover and battery")
img = Image.alpha_composite(img, over); d = ImageDraw.Draw(img)
# legend + note
x = 60 * S; y = H - 95 * S
for job, (c, name) in CAT.items():
    d.rounded_rectangle([x, y, x + 26 * S, y + 26 * S], radius=5 * S, fill=c)
    d.text((x + 36 * S, y), name, font=F, fill=(225, 228, 232)); x += 36 * S + d.textlength(name, font=F) + 50 * S
note = ("Gold = solder pads. Unlabeled outlines are small resistors and capacitors. Big parts are fixed by the case; "
        "the small ones may move when Quilter's auto-placement comes back.")
d.text((60 * S, H - 50 * S), note, font=FN, fill=(150, 155, 162))
img.convert("RGB").resize((W // S, H // S), Image.LANCZOS).save(OUT)
print(OUT, W // S, "x", H // S)
