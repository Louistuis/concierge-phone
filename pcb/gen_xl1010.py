"""Writes phone.pretty/LED_XINGLIGHT_XL-B1010RGBT_1.0x1.0mm.kicad_mod (XINGLIGHT XL-B1010RGBT-HF RGB LED, LCSC C22464515).
Source: XINGLIGHT datasheet (LCSC C22464515 PDF, "Outline Dimension" p.8): body 1.0 x 1.0 x 0.85 mm, common anode.
Polarity diagram p.8: pin 1 = common anode (+), pin 2 = R cathode, pin 3 = G cathode, pin 4 = B cathode.
Top-view drawing p.8: pin 1 top-right, 2 bottom-right, 3 bottom-left, 4 top-left (the pads below follow it, KiCad y down).
Recommended soldering pattern p.8: four 0.45 x 0.45 mm pads, 0.4 mm gap both ways -> pad centres at +-0.425 mm.
CAUTION (unverified): the datasheet's bottom-view drawing carries the same 1-2-3-4 corner labels as the top view, so one
of the two drawings is mirrored. This file follows the TOP view. Diode-test one reel sample (anode = pin 1) before the
first assembly order; a mirror would swap anode<->B and R<->G."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "LED_XINGLIGHT_XL-B1010RGBT_1.0x1.0mm"
PADS = {"1": (0.425, -0.425, "A"), "2": (0.425, 0.425, "R"), "3": (-0.425, 0.425, "G"), "4": (-0.425, -0.425, "B")}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(x1, y1, x2, y2, layer, w):
        return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)
    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += ('  (descr "XINGLIGHT XL-B1010RGBT-HF 1010 RGB LED, common anode. Pads 1 A, 2 R, 3 G, 4 B. '
          'Datasheet p.8 recommended pattern 0.45 x 0.45, 0.4 gap")\n')
    s += '  (tags "LED RGB 1010 XL-B1010RGBT")\n  (attr smd)\n'
    s += '  (property "Reference" "D**" (at 0 -1.2) (layer "F.SilkS") (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
    s += f'  (property "Value" "{NAME}" (at 0 1.3) (layer "F.Fab") (effects (font (size 0.3 0.3) (thickness 0.05))))\n'
    s += rect(-0.5, -0.5, 0.5, 0.5, "F.Fab", 0.05)
    s += line(0.25, -0.5, 0.5, -0.25, "F.Fab", 0.05)                       # pin-1 (anode) corner chamfer
    s += rect(-0.9, -0.9, 0.9, 0.9, "F.CrtYd", 0.05)
    s += '  (fp_circle (center 0.95 -0.95) (end 1.03 -0.95) (stroke (width 0.12) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    for n, (x, y, fn) in PADS.items():
        s += (f'  (pad "{n}" smd rect (at {x} {y}) (size 0.45 0.45) (layers "F.Cu" "F.Paste" "F.Mask")'
              f' (pinfunction "{fn}"))\n')
    s += ')\n'
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    print("wrote", NAME)
