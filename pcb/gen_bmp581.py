"""Writes phone.pretty/Bosch_BMP581_LGA-10_2x2mm_P0.5mm.kicad_mod (Bosch BMP581 barometer, 10-pin metal-lid LGA 2.0 x 2.0 x 0.8).
No stock KiCad footprint matches (the ST/Rohm 2x2 LGA-10 parts number their pads differently).
Source: Bosch BST-BMP581-DS004-13 rev 1.13 (https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp581-ds004.pdf):
pin table + top/bottom pin-out p.46 (Fig. 23 / Table 28), package outline p.68 (Fig. 29 top, Fig. 30 bottom view),
landing pattern p.69 (Fig. 32).
Package pads: rows of 3 at 0.5 pitch (0.25 x 0.275, long side toward the edge), columns of 2 at 0.5 pitch (0.275 x 0.25),
pad end 0.1 from the body edge, so pad centres at +/-0.7625 (the "1.525" on Fig. 30/32). Land = package pad + 25 um per side
(p.69): 0.30 x 0.325 rows, 0.325 x 0.30 columns, same centres.
Fig. 30 (BOTTOM view, pin-1 corner top-right): top row 8 9 10 left->right, right column 1 2 top->bottom, bottom row 5 4 3,
left column 7 6 top->bottom. Mirrored to TOP view (pin-1 corner top-left, Fig. 29): left column 1 (top) 2, bottom row 3 4 5
left->right, right column 6 (bottom) 7, top row 8 9 10 right->left. Counter-clockwise from pin 1, same as Fig. 23 top view.
p.69: no solder mask under the sensor (20 um mask clearance), no vias or traces under it: a mask opening covers the whole land
field here. Port hole is on the lid (outside air side)."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "Bosch_BMP581_LGA-10_2x2mm_P0.5mm"
PINS = {1: "VDDIO", 2: "SCK", 3: "VSS", 4: "SDI", 5: "SDO", 6: "CSB", 7: "INT", 8: "VSS", 9: "VSS", 10: "VDD"}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    C = 0.7625
    ROW, COL = (0.30, 0.325), (0.325, 0.30)      # (w, h) of row pads and column pads
    pads = [(1, -C, -0.25, COL), (2, -C, 0.25, COL),
            (3, -0.5, C, ROW), (4, 0.0, C, ROW), (5, 0.5, C, ROW),
            (6, C, 0.25, COL), (7, C, -0.25, COL),
            (8, 0.5, -C, ROW), (9, 0.0, -C, ROW), (10, -0.5, -C, ROW)]
    assert sorted(p[0] for p in pads) == list(range(1, 11))

    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(x1, y1, x2, y2, layer, w):
        return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)

    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "Bosch BMP581 LGA-10 2x2mm P0.5, land = pad + 25um (BST-BMP581-DS004-13 p.68-69), no mask under the part")\n'
    s += '  (tags "BMP581 LGA barometer")\n  (attr smd)\n'
    s += '  (property "Reference" "U**" (at 0 -1.45) (layer "F.SilkS") (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
    s += f'  (property "Value" "{NAME}" (at 0 1.45) (layer "F.Fab") (effects (font (size 0.3 0.3) (thickness 0.05))))\n'
    s += rect(-1.0, -1.0, 1.0, 1.0, "F.Fab", 0.08)
    s += line(-1.0, -0.7, -0.7, -1.0, "F.Fab", 0.08)
    s += rect(-1.25, -1.25, 1.25, 1.25, "F.CrtYd", 0.05)
    for sx in (-1, 1):                       # silk corner ticks outside the body
        for sy in (-1, 1):
            s += line(sx * 1.1, sy * 0.75, sx * 1.1, sy * 1.1, "F.SilkS", 0.1) + line(sx * 1.1, sy * 1.1, sx * 0.75, sy * 1.1, "F.SilkS", 0.1)
    s += '  (fp_circle (center -1.25 -1.25) (end -1.17 -1.25) (stroke (width 0.16) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    # one mask opening over the land field (Bosch: no solder mask under the sensor)
    s += '  (fp_rect (start -0.95 -0.95) (end 0.95 0.95) (stroke (width 0) (type solid)) (fill solid) (layer "F.Mask"))\n'
    for n, x, y, (w, h) in pads:
        s += (f'  (pad "{n}" smd rect (at {x} {y}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask")'
              f' (solder_mask_margin 0.02) (pinfunction "{PINS[n]}"))\n')
    s += ')\n'
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    print("wrote", NAME)
