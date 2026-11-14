"""Writes phone.pretty/TI_DNP0006A_USON-6-1EP_2x2mm_P0.65mm_EP0.65x1.35mm.kicad_mod (TI OPT3004DNPR ambient light sensor).
The stock 2x2 P0.65 SON footprints have a 1.0 x 1.6 thermal pad; the DNP0006A pad is 0.65 x 1.35, so a stock part would
crowd the pins. Source: TI SBOS929A (https://www.ti.com/lit/ds/symlink/opt3004.pdf): pin table p.3 (Fig. 6-1 top view,
Table 6-1), package outline 4221434/C p.47 (body 2.0 +-0.1, exposed thermal pad 0.65 x 1.35, pitch 0.65),
EXAMPLE BOARD LAYOUT p.48: six 0.5 x 0.25 rounded lands at x = +/-0.95 (1.9 centre to centre), y = -0.65 / 0 / +0.65,
thermal land 0.65 x 1.35 (two optional 0.2 mm vias), NSMD preferred, mask 0.07 max.
Top view: 1 VDD, 2 ADDR, 3 GND down the left (pin 1 top-left), 4 SCL, 5 INT, 6 SDA up the right. Pad 7 = thermal pad
(p.47 note 3 / p.48 note 5: must be soldered; layout guide p.34 recommends connecting it to GND). Clear optical mold:
keep the top of the part under the window, no silk over it."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "TI_DNP0006A_USON-6-1EP_2x2mm_P0.65mm_EP0.65x1.35mm"
PINS = {1: "VDD", 2: "ADDR", 3: "GND", 4: "SCL", 5: "INT", 6: "SDA", 7: "EP"}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pads = []
    for i, y in enumerate((-0.65, 0.0, 0.65)):
        pads.append((1 + i, -0.95, y))       # 1..3 left, top -> bottom
        pads.append((6 - i, 0.95, y))        # 6..4 right, top -> bottom
    assert sorted(p[0] for p in pads) == list(range(1, 7))

    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(x1, y1, x2, y2, layer, w):
        return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)

    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "TI DNP0006A USON-6 2x2mm P0.65, thermal pad 0.65x1.35 (OPT3004, SBOS929A p.47-48)")\n'
    s += '  (tags "OPT3004 OPT3001 DNP USON")\n  (attr smd)\n'
    s += '  (property "Reference" "U**" (at 0 -1.55) (layer "F.SilkS") (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
    s += f'  (property "Value" "{NAME}" (at 0 1.55) (layer "F.Fab") (effects (font (size 0.25 0.25) (thickness 0.04))))\n'
    s += rect(-1.0, -1.0, 1.0, 1.0, "F.Fab", 0.08)
    s += line(-1.0, -0.6, -0.6, -1.0, "F.Fab", 0.08)
    s += rect(-1.45, -1.25, 1.45, 1.25, "F.CrtYd", 0.05)
    s += line(-0.5, -1.1, 0.5, -1.1, "F.SilkS", 0.1) + line(-0.5, 1.1, 0.5, 1.1, "F.SilkS", 0.1)
    s += '  (fp_circle (center -1.35 -1.0) (end -1.27 -1.0) (stroke (width 0.16) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    for n, x, y in pads:
        s += (f'  (pad "{n}" smd roundrect (at {x} {y}) (size 0.5 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.5)'
              f' (solder_mask_margin 0.05) (pinfunction "{PINS[n]}"))\n')
    s += '  (pad "7" smd rect (at 0 0) (size 0.65 1.35) (layers "F.Cu" "F.Mask") (solder_mask_margin 0.05) (pinfunction "EP"))\n'
    s += '  (pad "" smd rect (at 0 0) (size 0.58 1.2) (layers "F.Paste"))\n'      # ~80 % paste on the thermal pad
    s += ')\n'
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    print("wrote", NAME)
