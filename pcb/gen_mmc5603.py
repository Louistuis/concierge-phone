"""Writes phone.pretty/MEMSIC_WLP-4_0.8x0.8mm_P0.4mm.kicad_mod (MEMSIC MMC5603NJ 3-axis magnetometer, wafer-level package).
No stock KiCad footprint has a 2x2 bump array at 0.40 mm pitch (stock WLCSP-4 parts are P0.35 / P0.5).
Source: MEMSIC MMC5603NJ datasheet Rev.B (https://www.lcsc.com/datasheet/lcsc_datasheet_1912111437_MEMSIC-MMC5603NJ_C404328.pdf):
package drawing p.17 (body 0.82 +-0.03 square, 0.40 +-0.03 thick, bump pitch 0.40, bump 0.22), RECOMMENDED LAND PATTERN p.18
(4 x round land 0.23 mm, 0.40 x 0.40 pitch), pin table p.4 (A1 VSA, A2 SCL, B1 VDD, B2 SDA).
Top view (p.17 "TOP VIEW"): row A on top, column 1 on the left, pin-1 dot at A1 = top-left. The bottom view on the same page
mirrors the columns (A2 left, A1 right), which confirms the top-view placement used here. Pads are named by ball (A1..B2).
Lands are NSMD (mask 0.035 mm per side leaves a 0.1 mm web at 0.4 pitch); paste = land."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "MEMSIC_WLP-4_0.8x0.8mm_P0.4mm"
PINS = {"A1": "VSA", "A2": "SCL", "B1": "VDD", "B2": "SDA"}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    P, D = 0.2, 0.23                         # half pitch, land diameter
    pads = [("A1", -P, -P), ("A2", P, -P), ("B1", -P, P), ("B2", P, P)]

    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(x1, y1, x2, y2, layer, w):
        return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)

    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "MEMSIC MMC5603NJ WLP-4 0.82x0.82mm, 2x2 bumps P0.40, round lands 0.23 (datasheet Rev.B p.17-18)")\n'
    s += '  (tags "MMC5603 WLP WLCSP magnetometer")\n  (attr smd)\n'
    s += '  (property "Reference" "U**" (at 0 -0.95) (layer "F.SilkS") (effects (font (size 0.4 0.4) (thickness 0.07))))\n'
    s += f'  (property "Value" "{NAME}" (at 0 0.95) (layer "F.Fab") (effects (font (size 0.2 0.2) (thickness 0.03))))\n'
    s += rect(-0.41, -0.41, 0.41, 0.41, "F.Fab", 0.05)
    s += line(-0.41, -0.21, -0.21, -0.41, "F.Fab", 0.05)
    s += rect(-0.66, -0.66, 0.66, 0.66, "F.CrtYd", 0.05)
    s += '  (fp_circle (center -0.6 -0.6) (end -0.55 -0.6) (stroke (width 0.1) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    for n, x, y in pads:
        s += (f'  (pad "{n}" smd circle (at {x} {y}) (size {D} {D}) (layers "F.Cu" "F.Paste" "F.Mask")'
              f' (solder_mask_margin 0.035) (pinfunction "{PINS[n]}"))\n')
    s += ')\n'
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    print("wrote", NAME)
