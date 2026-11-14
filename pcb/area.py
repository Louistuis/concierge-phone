"""Board-area budget: sums courtyard bounding boxes of every part in the sch_*.py files (+ core big parts), per side.
Run: KPY area.py"""
import os, sys, glob, importlib.util, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib_check import load_fp
def bbox_area(f):
    xs, ys = [], []
    for it in f.GraphicalItems():
        if it.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            bb = it.GetBoundingBox(); xs += [bb.GetLeft(), bb.GetRight()]; ys += [bb.GetTop(), bb.GetBottom()]
    if not xs:
        bb = f.GetBoundingBox(False, False); xs = [bb.GetLeft(), bb.GetRight()]; ys = [bb.GetTop(), bb.GetBottom()]
    return pcbnew.ToMM(max(xs) - min(xs)) * pcbnew.ToMM(max(ys) - min(ys))
tot = {}
for path in sorted(glob.glob(os.path.join(HERE, "sch_*.py"))):
    spec = importlib.util.spec_from_file_location("m", path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    for p in m.PARTS:
        if p.get("dnp_area") is False: continue
        f = load_fp(p["fp"]); a = bbox_area(f) if f else 0
        key = (os.path.basename(path), p.get("side", "F")); tot[key] = tot.get(key, 0) + a
CORE = {"P4 module": (27.2, 27.2, "F"), "EG915U": (21.5, 25.2, "F"), "A4S socket": (10, 3.5, "F"), "nano-SIM": (14.5, 16.4, "F"),
        "USB-C": (9.5, 8, "F"), "camera FPC": (19, 6, "B"), "2x SN74AXC4T774 + USB switch + passives": (14, 10, "F"),
        "U.FL x2 + I2C pull-ups + test pads": (12, 6, "F"), "camera + torch + ToF windows": (14, 12, "B")}
for k, (w, h, s) in CORE.items(): tot[("core", s)] = tot.get(("core", s), 0) + w * h
for k, v in sorted(tot.items()): print(f"{k[0]:<14} {k[1]}  {v:7.0f} mm2")
F = sum(v for k, v in tot.items() if k[1] == "F"); B = sum(v for k, v in tot.items() if k[1] == "B")
print(f"front total {F:.0f} mm2, back total {B:.0f} mm2 (courtyards only, no routing space)")
board = 44 * 88 - 4 * (7 * 7 - 3.14159 * 49 / 4)
print(f"board per side {board:.0f} mm2; back free beside the 42x62 battery ~{board - 42 * 62 - 60:.0f} mm2")
