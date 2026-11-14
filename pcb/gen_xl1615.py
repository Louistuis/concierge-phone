"""Writes phone.pretty/LED_XINGLIGHT_XL-1615RGBC_1.6x1.5mm.kicad_mod (XINGLIGHT XL-1615RGBC-RF RGB LED, LCSC C965840,
638,302 at JLC 2026-11-13; replaced the XL-B1010RGBT-HF whose datasheet top and bottom views contradict each other).
Source: XINGLIGHT XL-1615RGBC-RF datasheet (LCSC C965840 PDF) p.8 "Outline Dimension":
  top view (numbered castellations + green triangle between 1 and 2): 1 top-left, 2 bottom-left, 3 top-right, 4 bottom-right;
  circuit: pin 2 = common anode (+), 1 = R, 3 = G, 4 = B cathodes. Body 1.6 x 1.5 x 0.6 mm.
  Recommended soldering pattern: four 0.45 x 0.65 mm pads, 0.8 mm gap across, 0.3 mm gap between rows
  -> pad centres x +-0.625, y +-0.475 (KiCad top view, y down).
p.3: IF 20 mA max per colour, VR 5 V, ESD 2 kV (same class as the part it replaces)."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "LED_XINGLIGHT_XL-1615RGBC_1.6x1.5mm"
PADS = {"1": (-0.625, -0.475, "R"), "2": (-0.625, 0.475, "A"), "3": (0.625, -0.475, "G"), "4": (0.625, 0.475, "B")}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(x1, y1, x2, y2, layer, w):
        return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)
    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += ('  (descr "XINGLIGHT XL-1615RGBC-RF 1615 RGB LED, common anode. Pads 1 R, 2 A, 3 G, 4 B (datasheet p.8 top view). '
          'Pattern 0.45 x 0.65, 0.8 gap across, 0.3 between rows")\n')
    s += '  (tags "LED RGB 1615 XL-1615RGBC")\n  (attr smd)\n'
    s += '  (property "Reference" "D**" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
    s += f'  (property "Value" "{NAME}" (at 0 1.5) (layer "F.Fab") (effects (font (size 0.3 0.3) (thickness 0.05))))\n'
    s += rect(-0.8, -0.75, 0.8, 0.75, "F.Fab", 0.05)
    s += line(-0.8, -0.45, -0.5, -0.75, "F.Fab", 0.05)                    # pin-1 corner chamfer
    s += rect(-1.05, -1.0, 1.05, 1.0, "F.CrtYd", 0.05)
    s += '  (fp_circle (center -1.2 -1.05) (end -1.12 -1.05) (stroke (width 0.12) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    for n, (x, y, fn) in PADS.items():
        s += (f'  (pad "{n}" smd rect (at {x} {y}) (size 0.45 0.65) (layers "F.Cu" "F.Paste" "F.Mask")'
              f' (pinfunction "{fn}"))\n')
    s += ')\n'
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    print("wrote", NAME)
