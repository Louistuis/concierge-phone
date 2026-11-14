"""Writes phone.pretty/LED_XINGLIGHT_XL-3030_3.0x3.0mm.kicad_mod (XINGLIGHT XL-3030UWC-1W-3V white 1 W LED, LCSC C2843891).
Source: XINGLIGHT datasheet (LCSC C2843891 PDF, "Outline Dimension" p.7): body 3.0 x 3.0 (3.2 incl. terminals) x 0.65 mm,
polarity: pad 1 = cathode (-), pad 2 = anode (+), cathode corner chamfer on the pad-1 side.
Recommended soldering pattern: anode pad 2.2 x 2.4, cathode pad 0.9 x 2.4, 0.46 gap (3.56 overall).
The pattern is placed so its 0.46 gap lines up with the package's gap (package pads 2.0 + 0.46 + 0.7 = 3.16 centred).
Absolute max: IF 300 mA continuous, 500 mA pulsed (<= 0.1 ms, 1/10 duty) (p.3)."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "LED_XINGLIGHT_XL-3030_3.0x3.0mm"

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    gap_l, gap_r = -1.58 + 2.0, -1.58 + 2.0 + 0.46          # package gap 0.42 .. 0.88
    a_x = round(gap_l - 1.1, 3)                               # anode pad 2.2 wide, right edge at gap_l
    k_x = round(gap_r + 0.45, 3)                              # cathode pad 0.9 wide, left edge at gap_r
    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(x1, y1, x2, y2, layer, w):
        return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)
    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "XINGLIGHT XL-3030UWC-1W-3V 3030 LED, 2 pads (1 = cathode, 2 = anode, large). Datasheet p.7 recommended pattern")\n'
    s += '  (tags "LED 3030 XL-3030UWC")\n  (attr smd)\n'
    s += '  (property "Reference" "D**" (at 0 -2.3) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))\n'
    s += f'  (property "Value" "{NAME}" (at 0 2.3) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))\n'
    s += rect(-1.5, -1.5, 1.5, 1.5, "F.Fab", 0.1)
    s += line(1.1, 1.5, 1.5, 1.1, "F.Fab", 0.1)                                   # cathode chamfer (pad-1 side)
    s += '  (fp_circle (center 0 0) (end 1.25 0) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))\n'
    s += rect(-2.05, -1.75, 2.05, 1.75, "F.CrtYd", 0.05)
    s += line(-1.6, -1.62, 1.6, -1.62, "F.SilkS", 0.12) + line(-1.6, 1.62, 1.6, 1.62, "F.SilkS", 0.12)
    s += line(1.95, -1.3, 1.95, 1.3, "F.SilkS", 0.15)                              # cathode bar
    s += f'  (pad "1" smd rect (at {k_x} 0) (size 0.9 2.4) (layers "F.Cu" "F.Paste" "F.Mask") (pinfunction "K"))\n'
    s += f'  (pad "2" smd rect (at {a_x} 0) (size 2.2 2.4) (layers "F.Cu" "F.Paste" "F.Mask") (pinfunction "A"))\n'
    s += ')\n'
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    print("wrote", NAME, "anode x", a_x, "cathode x", k_x)
