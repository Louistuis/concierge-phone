"""Writes phone.pretty/TI_DLA_VSON-HR-10_2x3mm.kicad_mod (TI TPS63802DLAR, VSON-HR 10 pins, 2.0 x 3.0 mm, no exposed pad).
Land pattern: TI SLVSEU9D (https://www.ti.com/lit/ds/symlink/tps63802.pdf) drawing 4223750/D, p.36 "EXAMPLE BOARD LAYOUT":
pads 1-5 0.60 x 0.25 at x = -0.90; pads 6, 7, 9, 10 0.90 x 0.25 at x = +0.75; pad 8 (GND) 1.30 x 0.25 spanning x -0.10..+1.20;
0.5 mm pitch, pad 1 / pad 10 at y = -1.0 (pin 1 top-left, top view), R0.05 corners, NSMD, mask 0.07 max all round.
Stencil p.37 (0.1 mm): signal pads 1:1, pad 8 as two 0.55 x 0.25 apertures (centres x = 0.175 and 0.925, 0.2 gap, ~85 %).
Pin names: Table 7-1 p.4. Outline p.35: body 1.9-2.1 x 2.9-3.1, 1.0 mm max height."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "TI_DLA_VSON-HR-10_2x3mm"
PINS = {1: "EN", 2: "MODE", 3: "AGND", 4: "FB", 5: "PG", 6: "VOUT", 7: "L2", 8: "GND", 9: "L1", 10: "VIN"}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pads = []                                              # (num, x, y, w, h)
    for i in range(5):
        pads.append((1 + i, -0.90, -1.0 + 0.5 * i, 0.60, 0.25))   # 1..5 down the left
    for n, y in ((10, -1.0), (9, -0.5), (7, 0.5), (6, 1.0)):
        pads.append((n, 0.75, y, 0.90, 0.25))
    pads.append((8, 0.55, 0.0, 1.30, 0.25))
    assert sorted(p[0] for p in pads) == list(range(1, 11))

    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(x1, y1, x2, y2, layer, w):
        return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)

    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "TI DLA0010A VSON-HR-10 2x3mm P0.5mm, no exposed pad (TPS63802). Land from SLVSEU9D p.36, stencil p.37")\n'
    s += '  (tags "TPS63802 DLA0010A VSON-HR")\n  (attr smd)\n'
    s += '  (property "Reference" "U**" (at 0 -2.2) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))\n'
    s += f'  (property "Value" "{NAME}" (at 0 2.2) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))\n'
    s += rect(-1.0, -1.5, 1.0, 1.5, "F.Fab", 0.1)
    s += line(-1.0, -1.1, -0.6, -1.5, "F.Fab", 0.1)                       # pin-1 chamfer
    s += rect(-1.45, -1.75, 1.45, 1.75, "F.CrtYd", 0.05)
    s += line(-0.5, -1.62, 0.5, -1.62, "F.SilkS", 0.1) + line(-0.5, 1.62, 0.5, 1.62, "F.SilkS", 0.1)
    s += '  (fp_circle (center -1.4 -1.45) (end -1.32 -1.45) (stroke (width 0.16) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    for n, x, y, w, h in pads:
        layers = '"F.Cu" "F.Mask"' if n == 8 else '"F.Cu" "F.Paste" "F.Mask"'
        s += (f'  (pad "{n}" smd roundrect (at {x} {y}) (size {w} {h}) (layers {layers}) (roundrect_rratio 0.2)'
              f' (solder_mask_margin 0.05) (pinfunction "{PINS[n]}"))\n')
    for x in (0.175, 0.925):                                              # pad 8 paste apertures (no number = paste only)
        s += f'  (pad "" smd roundrect (at {x} 0) (size 0.55 0.25) (layers "F.Paste") (roundrect_rratio 0.2))\n'
    s += ')\n'
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    print("wrote", NAME, len(pads), "pads")
