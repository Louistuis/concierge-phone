"""Writes phone.pretty/SIM_Nano_SHOUHAN_7P_H1.37.kicad_mod (SHOU HAN "NANO SIM 7P H1.37" push-push nano-SIM holder with
card-detect switch, 1.37 mm tall, LCSC/JLC C7529384).
Geometry: SHOU HAN drawing "NANO SIM 7P H1.37" rev A0 (datasheets/LCSC_C7529384_SHOUHAN_NANO_SIM_7P_H1.37.pdf p.1,
"RECOMMENDED PCB LAYOUT", tolerance +-0.05), read from the PDF vector paths (pdftocairo -svg; scale fixed by the 13.00 mm
tab pitch). Origin and orientation = the LCSC/EasyEDA footprint C7529384 (SIM-SMD_NANO-SIM-7P-H1.37, v6 units 10 mil =
0.254 mm), so JLC's CPL offsets line up: x = 0 midway between the shell tabs, contacts row at the top (-y), card enters
from the +y edge. Datum: housing insertion edge Yb = +7.4904.
  7 contact pads 0.80 x 1.14 mm at y = -6.7404 (1.48 mm above the upper tab centres), left->right C3 C7 C2 C6 C1 C5 at
  1.27 mm pitch (C3 at x = -4.83) then CD 0.95 mm right of C5.
  4 shell tabs 0.70 x 2.10 mm at x = +-6.50 (13.00 apart), y = Yb-12.75 and Yb-0.75 (12.00 apart).
  2 NPTH locating holes d 0.75 ("2-d0.75 通孔") at x = -5.00 / +3.50 (8.50 apart), y = Yb-2.00.
  Copper restricted areas on the TOP layer ("touch area of contact tips, no first-layer circuits"): 3 x (1.30 x 2.75) at
  x -3.71/-1.17/+1.37 (2.54 pitch), y = Yb-7.67 and 3 x (1.85 x 3.50) at x -3.71/-1.21/+1.29 (2.50 pitch), y = Yb-1.94.
  Written as F.Cu keep-out zones + Cmts.User outlines.
Body: housing 12.29 wide x 13.72 long (contact tips reach 14.50), 1.37 mm tall; card 12.30 x 8.80 nano-SIM; card edge
stands 4.20 +-0.30 mm out of the insertion edge when ejected (drawn on Cmts.User; keep the case opening clear).
Pin names: drawing table "PIN/NO ASSIGNMENT": C1 VCC, C2 RST, C3 CLK, C5 GND, C6 VPP, C7 I/O, CD detect switch; tabs GND
(shell). Pad numbers are the maker's/LCSC symbol numbers (C1..C7, CD, 8-11 for the shell tabs).
Card detect: the drawing's switch diagram says "NORMAL......SHORT / INSERTING CARD......OPEN" between CD and GND, i.e.
normally CLOSED to GND with no card, OPEN with a card. With Quectel's 51k pull-up to VDD_EXT on USIM_DET the line reads
LOW = empty, HIGH = card present (set the module's SIM-detect insert level to high, AT+QSIMDET=1,1).
EasyEDA vs drawing: C5 and CD pads are 0.70 wide in EasyEDA (gap 0.25) but the drawing says "7-0.80" (gap 0.15 mm,
followed here); shell tabs 2.40 long in EasyEDA vs 2.10 in the drawing (followed here); holes d 0.80 vs d 0.75 (0.75
here). All centres agree within 0.01 mm. EasyEDA has no keep-out areas.
MUST-verify: print 1:1 and lay a real holder on it (C5-CD gap is only 0.15 mm; JLC's own footprint narrows those two
pads) and confirm CD reads open with a card on a meter before ordering."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "SIM_Nano_SHOUHAN_7P_H1.37"

PINS = {"C1": "VCC", "C2": "RST", "C3": "CLK", "C5": "GND", "C6": "VPP", "C7": "I/O", "CD": "CD_SW",
        "8": "SHELL_GND", "9": "SHELL_GND", "10": "SHELL_GND", "11": "SHELL_GND"}
CD_SWITCH = "normally closed to GND (shell) without card, open with card inserted"

YB = 7.4904                                   # housing insertion edge (datum of the drawing's vertical dims)


def pads():
    """(num, kind, x, y, w, h) in mm, top view, y down. kind smd/npth."""
    y = -6.7404
    P = [(n, "smd", round(-4.83 + 1.27 * i, 4), y, 0.80, 1.14) for i, n in enumerate(["C3", "C7", "C2", "C6", "C1", "C5"])]
    P.append(("CD", "smd", round(-4.83 + 1.27 * 5 + 0.95, 4), y, 0.80, 1.14))
    yt, yb = round(YB - 12.75, 4), round(YB - 0.75, 4)
    P += [("8", "smd", 6.5, yt, 0.70, 2.10), ("9", "smd", -6.5, yt, 0.70, 2.10),
          ("10", "smd", -6.5, yb, 0.70, 2.10), ("11", "smd", 6.5, yb, 0.70, 2.10)]
    yh = round(YB - 2.0, 4)
    P += [("", "npth", -5.0, yh, 0.75, 0.75), ("", "npth", 3.5, yh, 0.75, 0.75)]
    return P


KEEPOUT = ([(x, round(YB - 7.67, 4), 1.30, 2.75) for x in (-3.71, -1.17, 1.37)] +
           [(x, round(YB - 1.94, 4), 1.85, 3.50) for x in (-3.71, -1.21, 1.29)])


def line(x1, y1, x2, y2, layer, w):
    return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'


def rect(x1, y1, x2, y2, layer, w):
    return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)


def text(t, x, y, layer, size=0.4):
    return (f'  (fp_text user "{t}" (at {x} {y}) (layer "{layer}") '
            f'(effects (font (size {size} {size}) (thickness {round(size * 0.15, 3)}))))\n')


def r4(v):
    return round(v, 4)


def build():
    BW, YT = 12.29 / 2, r4(YB - 13.72)              # housing half width, housing top edge
    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += ('  (descr "SHOU HAN NANO SIM 7P H1.37 push-push nano-SIM holder with card detect (NC, opens with card), '
          '1.37mm. SHOU HAN drawing rev A0 recommended PCB layout; origin as LCSC/EasyEDA C7529384.")\n')
    s += '  (tags "nano SIM push-push card detect C7529384")\n'
    s += '  (attr smd)\n'
    s += f'  (property "Reference" "J**" (at 0 {r4(YB + 0.9)}) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
    s += '  (property "Value" "NANO SIM 7P H1.37" (at 0 2.5) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
    # F.Fab: housing, contact tips line, insertion arrow
    s += rect(-BW, YT, BW, YB, "F.Fab", 0.1)
    s += line(-5.3, r4(YB - 14.50), 3.0, r4(YB - 14.50), "F.Fab", 0.1)
    s += line(0, r4(YB - 0.1), 0, r4(YB - 1.0), "F.Fab", 0.1) + line(-0.4, r4(YB - 0.6), 0, r4(YB - 1.0), "F.Fab", 0.1) + line(0.4, r4(YB - 0.6), 0, r4(YB - 1.0), "F.Fab", 0.1)
    s += text("card in", 1.3, r4(YB - 0.5), "F.Fab", 0.5)
    s += text("C1", 0.25, -5.6, "F.Fab", 0.4)
    # F.CrtYd: pads/body + 0.25
    s += rect(-7.1, -7.6, 7.1, r4(YB - 0.75 + 1.05 + 0.25), "F.CrtYd", 0.05)
    # F.SilkS: housing outline, kept >= 0.2 mm off copper
    so = BW + 0.06                                   # 0.06 outside the housing edge
    s += line(-so, -3.95, -so, 5.43, "F.SilkS", 0.12) + line(so, -3.95, so, 5.43, "F.SilkS", 0.12)
    s += line(-5.9, r4(YB + 0.1), 5.9, r4(YB + 0.1), "F.SilkS", 0.12)
    s += line(-5.9, r4(YT - 0.06), -5.55, r4(YT - 0.06), "F.SilkS", 0.12) + line(3.2, r4(YT - 0.06), 5.9, r4(YT - 0.06), "F.SilkS", 0.12)
    s += '  (fp_circle (center 0.25 -7.75) (end 0.4 -7.75) (stroke (width 0.3) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    # Cmts.User: copper-restricted areas, eject position
    for x, y, w, h in KEEPOUT:
        s += rect(r4(x - w / 2), r4(y - h / 2), r4(x + w / 2), r4(y + h / 2), "Cmts.User", 0.05)
    s += text("no F.Cu: contact tips", -1.2, -2.0, "Cmts.User", 0.4)
    s += line(-BW, r4(YB + 4.2), BW, r4(YB + 4.2), "Cmts.User", 0.05)
    s += text("card edge when ejected (+4.2 +-0.3)", 0, r4(YB + 3.8), "Cmts.User", 0.4)
    # F.Cu keep-out zones (maker: no first-layer circuits under contact tips)
    for i, (x, y, w, h) in enumerate(KEEPOUT):
        x1, y1, x2, y2 = r4(x - w / 2), r4(y - h / 2), r4(x + w / 2), r4(y + h / 2)
        s += (f'  (zone (net 0) (net_name "") (layers "F.Cu") (name "SIM_tip_keepout_{i + 1}") (hatch edge 0.5)\n'
              '    (connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no)\n'
              '    (keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints allowed))\n'
              '    (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))\n'
              f'    (polygon (pts (xy {x1} {y1}) (xy {x2} {y1}) (xy {x2} {y2}) (xy {x1} {y2}))))\n')
    for n, kind, x, y, w, h in pads():
        if kind == "npth":
            s += (f'  (pad "" np_thru_hole circle (at {x} {y}) (size {w} {h}) (drill {w}) (layers "*.Cu" "*.Mask"))\n')
        else:
            s += (f'  (pad "{n}" smd rect (at {x} {y}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask")'
                  f' (pinfunction "{PINS[n]}"))\n')
    s += ')\n'
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    return len(pads())


if __name__ == "__main__":
    print("wrote", build(), "pads (incl. 2 NPTH)")
    try:
        from gen_eg915u import check
        check(OUT, NAME)
    except ImportError as e:
        print("check skipped:", e)
