"""Writes phone.pretty/Sensirion_DFN-6-1EP_2.44x2.44mm_P0.8mm_SGP4x.kicad_mod (Sensirion SGP41 VOC/NOx gas sensor).
No stock KiCad footprint (the Sensirion stock parts are DFN-4/DFN-8). Source: Sensirion SGP41 datasheet version 1.0,
December 2021 (https://sensirion.com/media/documents/5FE8673C/61E96F50/Sensirion_Gas_Sensors_Datasheet_SGP41.pdf):
pin table + transparent top view p.7 (Table 6), package outline p.18 (Fig. 17: 2.44 x 2.44 x 0.85, pitch 0.8, pads 0.35 x 0.4,
die pad 1.25 x 1.64 with a 0.3 x 45 deg pin-1 cut), recommended land pattern p.19 (Fig. 18).
Fig. 18 read off a 300 dpi render (2.3 = pad centre to centre, verified against the 0.55 pad length): six 0.55 x 0.40 lands
at x = +/-1.15, y = -0.8 / 0 / +0.8; die-pad land 1.25 x 1.7 with the 0.3 x 45 deg chamfer at the pin-1 corner; stencil
1.05 x 1.5 on the die pad, full aperture on the pins. NSMD pads (p.19). Pin 1 top-left (p.7 top view, pin-1 dot top-left
of the marking p.18); 1-3 down the left, 4-6 up the right. Pad 7 = die pad: electrically GND (p.7 text), solder it for
mechanical stability. Sensor opening is on the TOP face (bottom-right corner, 0.8 mm), it needs outside air."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "Sensirion_DFN-6-1EP_2.44x2.44mm_P0.8mm_SGP4x"
PINS = {1: "VDD", 2: "VSS", 3: "SDA", 4: "NA_GND", 5: "VDDH", 6: "SCL", 7: "DIE_PAD"}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pads = []
    for i, y in enumerate((-0.8, 0.0, 0.8)):
        pads.append((1 + i, -1.15, y))       # 1..3 left, top -> bottom
        pads.append((6 - i, 1.15, y))        # 6..4 right, top -> bottom
    assert sorted(p[0] for p in pads) == list(range(1, 7))

    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(x1, y1, x2, y2, layer, w):
        return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)

    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "Sensirion SGP41 DFN-6 2.44x2.44mm P0.8, die pad 1.25x1.7 (datasheet v1.0 p.18-19)")\n'
    s += '  (tags "SGP41 SGP40 DFN gas sensor")\n  (attr smd)\n'
    s += '  (property "Reference" "U**" (at 0 -1.75) (layer "F.SilkS") (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
    s += f'  (property "Value" "{NAME}" (at 0 1.75) (layer "F.Fab") (effects (font (size 0.25 0.25) (thickness 0.04))))\n'
    s += rect(-1.22, -1.22, 1.22, 1.22, "F.Fab", 0.08)
    s += line(-1.22, -0.82, -0.82, -1.22, "F.Fab", 0.08)
    s += '  (fp_circle (center 0.62 0.62) (end 1.02 0.62) (stroke (width 0.05) (type dash)) (fill none) (layer "F.Fab"))\n'
    s += rect(-1.7, -1.5, 1.7, 1.5, "F.CrtYd", 0.05)
    s += line(-0.55, -1.32, 0.55, -1.32, "F.SilkS", 0.1) + line(-0.55, 1.32, 0.55, 1.32, "F.SilkS", 0.1)
    s += '  (fp_circle (center -1.55 -1.3) (end -1.47 -1.3) (stroke (width 0.16) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    for n, x, y in pads:
        s += (f'  (pad "{n}" smd rect (at {x} {y}) (size 0.55 0.4) (layers "F.Cu" "F.Paste" "F.Mask")'
              f' (solder_mask_margin 0.05) (pinfunction "{PINS[n]}"))\n')
    # die pad: 1.25 x 1.7 with the 0.3 x 45 deg chamfer at the top-left (pin-1) corner, as a custom polygon pad
    w, h, c = 0.625, 0.85, 0.3
    pts = [(-w + c, -h), (w, -h), (w, h), (-w, h), (-w, -h + c)]
    poly = " ".join(f"(xy {x} {y})" for x, y in pts)
    s += ('  (pad "7" smd custom (at 0 0) (size 0.5 0.5) (layers "F.Cu" "F.Mask") (solder_mask_margin 0.05)'
          ' (pinfunction "DIE_PAD")\n    (options (clearance outline) (anchor rect))\n'
          f'    (primitives (gr_poly (pts {poly}) (width 0) (fill yes))))\n')
    s += '  (pad "" smd rect (at 0 0) (size 1.05 1.5) (layers "F.Paste"))\n'
    s += ')\n'
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    print("wrote", NAME)
