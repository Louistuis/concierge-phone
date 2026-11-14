"""Writes phone.pretty/TI_YKB0008_DSBGA-8_0.8x1.5mm_P0.35mm.kicad_mod (TI LM36011YKBR torch/flash driver, DSBGA 2 x 4 balls).
The stock Texas_DSBGA-8_0.705x1.468mm_Layout2x4_P0.4mm is 0.4 mm pitch (YBJ, INA234) and does NOT fit: YKB is 0.35 mm.
Source: TI package drawing YKB0008 4223222/A (https://www.ti.com/lit/pdf/MXBG377): outline p.1 (ball pitch 0.35 TYP both ways,
4 rows A-D x 2 columns 1-2, 0.5 mm max height), EXAMPLE BOARD LAYOUT p.2 (8X 0.2 mm round NSMD pads, mask opening
0.2 + 0.0325 max per side), stencil p.3 (8X 0.21 square, R0.05). Body 1.512 x 0.800 nom (LM36011 SNVSAN5A p.1).
Top view: A1 top-left, rows A..D top -> bottom, columns 1..2 left -> right (datasheet Figure 5, p.3)."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "TI_YKB0008_DSBGA-8_0.8x1.5mm_P0.35mm"

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(x1, y1, x2, y2, layer, w):
        return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)
    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "TI YKB0008 DSBGA-8, 2x4 balls, 0.35mm pitch, 0.2mm NSMD pads (LM36011). From TI 4223222/A (MXBG377)")\n'
    s += '  (tags "LM36011 YKB0008 DSBGA WCSP")\n  (attr smd)\n'
    s += '  (property "Reference" "U**" (at 0 -1.2) (layer "F.SilkS") (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
    s += f'  (property "Value" "{NAME}" (at 0 1.2) (layer "F.Fab") (effects (font (size 0.3 0.3) (thickness 0.05))))\n'
    s += rect(-0.4, -0.756, 0.4, 0.756, "F.Fab", 0.05)
    s += line(-0.4, -0.556, -0.2, -0.756, "F.Fab", 0.05)
    s += rect(-0.65, -1.0, 0.65, 1.0, "F.CrtYd", 0.05)
    s += line(-0.52, -0.88, -0.2, -0.88, "F.SilkS", 0.08) + line(-0.52, -0.88, -0.52, -0.56, "F.SilkS", 0.08)
    n = 0
    for r, row in enumerate("ABCD"):
        for c in (1, 2):
            x, y = (-0.175 if c == 1 else 0.175), round(-0.525 + 0.35 * r, 3)
            s += (f'  (pad "{row}{c}" smd circle (at {x} {y}) (size 0.2 0.2) (layers "F.Cu" "F.Mask")'
                  f' (solder_mask_margin 0.0325))\n')
            s += f'  (pad "" smd roundrect (at {x} {y}) (size 0.21 0.21) (layers "F.Paste") (roundrect_rratio 0.24))\n'
            n += 1
    s += ')\n'
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    print("wrote", NAME, n, "balls")
