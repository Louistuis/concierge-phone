"""Writes phone.pretty/Waveshare_ESP32-P4-Module.kicad_mod (ESP32-P4NRW32X + ESP32-C6FH8, 25 x 25 mm, 88 castellated pads).
Pad geometry: Waveshare "ESP32-P4-Module-PCB-Land-Pattern.dxf" (files.waveshare.com/wiki/ESP32-P4-Module/), read
exactly by ezdxf: 88 pads 0.70 x 1.50 mm, 1.00 mm pitch, pad centres on the 25.0 mm outline (+-12.5), mask +0.051 per side.
Pin numbers + names: Waveshare ESP32-P4-Module V1.1 schematic symbol U1 (ESP32-P4-Module-datasheet.pdf p.1).
The DXF carries no numbers; its pin-1 dot (top left, first pad of the left column) matches the assembly drawing (p.2)
and the symbol runs counter-clockwise: 1-22 left (top->bottom), 23-44 bottom, 45-66 right (bottom->top), 67-88 top.
MUST-verify: confirm pad 2 (LNA_OUT) and pad 85/86 (3V3) on a real module with a meter before ordering."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
os.makedirs(OUT, exist_ok=True)

PINS = {1: "GND", 2: "LNA_OUT", 3: "GND", 4: "C6_U0RXD", 5: "C6_U0TXD", 6: "C6_IO15", 7: "C6_IO14", 8: "C6_IO13",
        9: "C6_IO9", 10: "C6_IO8", 11: "C6_IO7", 12: "C6_IO6", 13: "C6_IO5", 14: "C6_IO4", 15: "GND"}
PINS.update({16 + i: f"GPIO{1 + i}" for i in range(7)})                       # 16-22 GPIO1-7
PINS.update({23: "GPIO8", 24: "GPIO9", 25: "GPIO10", 26: "GPIO11", 27: "GPIO12", 28: "GPIO13", 29: "GPIO20",
             30: "GPIO21", 31: "GPIO22", 32: "GPIO23", 33: "GND", 34: "DSI_D1P", 35: "DSI_D1N", 36: "DSI_CLKN",
             37: "DSI_CLKP", 38: "DSI_D0P", 39: "DSI_D0N", 40: "GND", 41: "CSI_D0N", 42: "CSI_D0P", 43: "CSI_CLKP",
             44: "CSI_CLKN", 45: "CSI_D1N", 46: "CSI_D1P", 47: "GND", 48: "USB_HS_DM", 49: "USB_HS_DP",
             50: "GPIO24", 51: "GPIO25", 52: "GND"})
PINS.update({53 + i: f"GPIO{26 + i}" for i in range(13)})                     # 53-65 GPIO26-38
PINS.update({66: "VFB_VO4"})
PINS.update({67 + i: f"GPIO{39 + i}" for i in range(16)})                     # 67-82 GPIO39-54
PINS.update({83: "GND", 84: "VBAT", 85: "ESP_3V3", 86: "ESP_3V3", 87: "CHIP_PU", 88: "GPIO0"})
assert sorted(PINS) == list(range(1, 89))

if __name__ == "__main__":
    E, P = 12.5, 10.5                       # pad-centre ring, first/last pad offset
    W, L = 0.70, 1.50
    pads = []
    for i in range(22):
        o = -P + i
        pads.append((1 + i, -E, o, L, W))   # left, top -> bottom
        pads.append((23 + i, o, E, W, L))   # bottom, left -> right
        pads.append((45 + i, E, -o, L, W))  # right, bottom -> top
        pads.append((67 + i, -o, -E, W, L)) # top, right -> left
    assert sorted(p[0] for p in pads) == list(range(1, 89))

    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(a, layer, w):
        return line(-a, -a, a, -a, layer, w) + line(a, -a, a, a, layer, w) + line(a, a, -a, a, layer, w) + line(-a, a, -a, -a, layer, w)

    s = '(footprint "Waveshare_ESP32-P4-Module"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "Waveshare ESP32-P4-Module (ESP32-P4NRW32X + ESP32-C6FH8), 25x25mm, 88 castellated pads 1.0mm pitch. From Waveshare land-pattern DXF + V1.1 schematic.")\n'
    s += '  (attr smd)\n'
    s += '  (property "Reference" "U**" (at 0 -14.6) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
    s += '  (property "Value" "ESP32-P4-Module" (at 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))\n'
    s += rect(12.5, "F.Fab", 0.1)
    s += rect(13.6, "F.CrtYd", 0.05)
    for sx in (-1, 1):                       # silk corner brackets outside the pad ring
        for sy in (-1, 1):
            s += line(sx * 13.45, sy * 11.3, sx * 13.45, sy * 13.45, "F.SilkS", 0.12)
            s += line(sx * 13.45, sy * 13.45, sx * 11.3, sy * 13.45, "F.SilkS", 0.12)
    s += '  (fp_circle (center -14.1 -10.5) (end -13.95 -10.5) (stroke (width 0.3) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    for n, x, y, w, h in pads:
        s += (f'  (pad "{n}" smd rect (at {x} {y}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask")'
              f' (solder_mask_margin 0.051) (pinfunction "{PINS[n]}"))\n')
    s += ')\n'
    open(os.path.join(OUT, "Waveshare_ESP32-P4-Module.kicad_mod"), "w").write(s)
    print("wrote", len(pads), "pads")
