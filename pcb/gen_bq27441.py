"""Writes phone.pretty/TI_DRZ0012A_VSON-12_2.5x4mm.kicad_mod (TI BQ27441-G1 fuel gauge, VSON-12 4.0 x 2.5 mm, 0.4 mm pitch).
No stock KiCad footprint has this land. Source: TI SLUSBH1C (https://www.ti.com/lit/ds/symlink/bq27441-g1.pdf), drawing 4218895/B:
outline p.25 (body 3.85-4.15 x 2.35-2.65, 1.0 mm max), EXAMPLE BOARD LAYOUT p.26, stencil p.27.
Land: 12 pads 0.6 x 0.2 at x = +/-1.9 (3.8 centre-to-centre), 0.4 pitch, pins 1-6 down the left (pin 1 top-left), 7-12 up the
right (12 opposite 1); thermal pad 13 = 2.45 x 1.95 body plus four 0.2-wide tie-bar fingers at x = +/-1.125 reaching y = +/-1.45
(2.9 overall); R0.05, NSMD, mask 0.05 max. Stencil: EP as two 1.08 x 1.75 apertures at x = +/-0.64 (79 %).
(The stencil page labels 7/12 swapped; the outline and land pages both put 12 opposite 1, which is the CCW order used here.)
Pin names: Pin Functions table p.4."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "TI_DRZ0012A_VSON-12_2.5x4mm"
PINS = {1: "SDA", 2: "SCL", 3: "VSS", 4: "NC", 5: "VDD", 6: "BAT", 7: "SRN", 8: "SRP", 9: "NC", 10: "BIN", 11: "NC",
        12: "GPOUT", 13: "EP"}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pads = []
    for i in range(6):
        y = round(-1.0 + 0.4 * i, 3)
        pads.append((1 + i, -1.9, y, 0.6, 0.2))           # 1..6 left, top -> bottom
        pads.append((12 - i, 1.9, y, 0.6, 0.2))           # 12..7 right, top -> bottom
    assert sorted(p[0] for p in pads) == list(range(1, 13))

    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(x1, y1, x2, y2, layer, w):
        return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)

    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "TI DRZ0012A VSON-12 4x2.5mm P0.4mm, thermal pad with tie bars (BQ27441-G1). Land from SLUSBH1C p.26, stencil p.27")\n'
    s += '  (tags "BQ27441 DRZ0012A VSON")\n  (attr smd)\n'
    s += '  (property "Reference" "U**" (at 0 -1.9) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))\n'
    s += f'  (property "Value" "{NAME}" (at 0 1.9) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))\n'
    s += rect(-2.0, -1.25, 2.0, 1.25, "F.Fab", 0.1)
    s += line(-2.0, -0.85, -1.6, -1.25, "F.Fab", 0.1)
    s += rect(-2.45, -1.7, 2.45, 1.7, "F.CrtYd", 0.05)
    s += line(-0.8, -1.55, 0.8, -1.55, "F.SilkS", 0.1) + line(-0.8, 1.55, 0.8, 1.55, "F.SilkS", 0.1)
    s += '  (fp_circle (center -2.35 -1.35) (end -2.27 -1.35) (stroke (width 0.16) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    for n, x, y, w, h in pads:
        s += (f'  (pad "{n}" smd roundrect (at {x} {y}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25)'
              f' (solder_mask_margin 0.05) (pinfunction "{PINS[n]}"))\n')
    # thermal pad 13: main body + four tie-bar fingers (same pad number, copper + mask only)
    s += '  (pad "13" smd rect (at 0 0) (size 2.45 1.95) (layers "F.Cu" "F.Mask") (solder_mask_margin 0.05) (pinfunction "EP"))\n'
    for sx in (-1, 1):
        for sy in (-1, 1):
            s += (f'  (pad "13" smd rect (at {sx * 1.125} {sy * 1.2125}) (size 0.2 0.475) (layers "F.Cu" "F.Mask")'
                  f' (solder_mask_margin 0.05) (pinfunction "EP"))\n')
    for x in (-0.64, 0.64):
        s += f'  (pad "" smd roundrect (at {x} 0) (size 1.08 1.75) (layers "F.Paste") (roundrect_rratio 0.05))\n'
    s += ')\n'
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    print("wrote", NAME)
