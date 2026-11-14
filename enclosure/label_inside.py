"""Adds leader-line labels to inside_v2.png using the 2D anchors written by render_inside.py, then crops."""
import json, sys
from PIL import Image, ImageDraw, ImageFont
src = sys.argv[1]; out = sys.argv[2]
im = Image.open(src).convert("RGB"); W, H = im.size
L = json.load(open(src + ".labels.json"))
f = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 30)
d = ImageDraw.Draw(im)
skip = {"band", "body", "pcb"}
items = sorted([(v["y"], k, v) for k, v in L.items() if k not in skip])
left = [i for i in items if i[2]["x"] < W * 0.5]; right = [i for i in items if i[2]["x"] >= W * 0.5]
def place(group, side):
    ys = []; y_last = -999
    for y, k, v in group:
        ty = max(y, y_last + 52); ys.append((ty, v)); y_last = ty
    for ty, v in ys:
        tx = 60 if side == "L" else W - 60
        tw = d.textlength(v["text"], font=f)
        ex = tx + tw + 14 if side == "L" else tx - tw - 14
        d.line([(v["x"], v["y"]), (ex, ty + 16)], fill=(40, 40, 45), width=2)
        d.ellipse([v["x"] - 6, v["y"] - 6, v["x"] + 6, v["y"] + 6], fill=(255, 140, 40))
        d.text((tx if side == "L" else tx - tw, ty), v["text"], font=f, fill=(25, 25, 30))
place(left, "L"); place(right, "R")
d.text((60, 430), "Concierge Phone v2: inside (exploded, real size)", font=ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 40), fill=(20, 20, 25))
im.crop((0, 400, W, 1620)).save(out); print("wrote", out)
