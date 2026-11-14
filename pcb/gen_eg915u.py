"""Writes phone.pretty/Quectel_EG915U.kicad_mod (Quectel EG915U-EU LTE Cat-1bis, LGA-126, 23.6 x 19.9 x 2.4 mm,
JLC C7471302, ordering code EG915UEUAC-N05-SNNSA).
Pad geometry: "Quectel_EG915U_Series_QuecOpen_Hardware_Design_V1.0" (datasheets/), Fig 40 Recommended Footprint (top view)
+ Fig 39 Bottom Dimensions, read from the PDF vector paths (pdftocairo -svg, 126 filled pads, scale fixed by the
18.25 mm column pitch): 62 edge pads 1.05 x 0.70 mm (long axis normal to the edge), centres 0.825 mm in from the
module edge (columns x = +-9.125, rows y = +-10.975, i.e. 21.95 mm apart as Fig 39 says; Fig 40 prints a rounded "22"),
edge pitch 1.1 mm with a 1.7 mm gap at the middle of each column and a 2.5 mm gap in each row; 64 inner pads 1.0 x 1.0 mm
on a 1.7 mm grid (x -5.95..5.95, y -7.65..7.65) plus a 2 x 4 centre block at x +-0.85, y +-0.85/+-2.55.
Body 19.9 x 23.6 (Fig 38), 1.0 mm chamfer ("C1") at the pin-1 corner. Paste 1:1 (Quectel: stencil 0.13-0.15 mm).
Pin numbers: the footprint drawing numbers only pin 1, so numbering comes from Fig 2 "Pin Assignment (Top View)" (page 17):
pin 1 top-left, 1-18 down the left column (gap after 10), 19-31 left->right along the bottom (gap after 24),
32-49 up the right column (gap after 39), 50-62 right->left along the top (gap after 56); inner rows read off Fig 2
row by row (pdftotext -bbox positions). Cross-checked against LCSC/EasyEDA footprint C7471302
("LGA-SMD_L23.6-W19.9-P1.10_EG915U-EC"): all 126 pad numbers land on the same pads; inner pads agree to 0.001 mm.
EasyEDA differs: edge pads 1.80 mm long (0.375 mm longer each way, overhanging the body edge by 0.075 mm), side columns
shifted -0.06 mm in y, top/bottom rows at +-11.00 (22.0 apart). We follow the Quectel drawing.
Pin names: standard (AT firmware) names from "BG95xA&EG915U&EG91xQ Series Compatible Design V1.0" (2025-06-09) Table 7,
EG915U column; QuecOpen names (only matter for QuecOpen firmware) are in QUECOPEN_ALT. All logic I/O is 1.8 V
(VDD_EXT domain); PWRKEY/RESET_N sit in the VBAT domain (pull low only, open drain); USIM pins follow USIM_VDD (1.8/3.0 V).
Boot cautions (Quectel): never pull USB_BOOT (75) high before the module is up unless emergency download is wanted;
pins 18, 19, 30, 38, 39 output 3.0 V for 2 s then 0 V for 1.2 s after power-on before software owns them (do not use as
inputs to anything that minds 3 V, do not drive them hard during that window); PWRKEY low >= 2 s to turn on (wait >= 30 ms
after VBAT is stable), do not tie PWRKEY to GND with a resistor.
RF layout (Quectel 5.1.4, the guide gives NO copper keep-out under the module): ANT_MAIN (60) and ANT_BT/WIFI_SCAN (56)
are 50 ohm; GND pins next to RF pins must not use thermal relief (pads 55, 59, 61 are set to solid zone connection here);
RF trace short, 135-degree bends, CPWG with ground vias >= 2 x W from the trace; clearance under the antenna connector
signal pin; pi-match (0R + 2 x NM) + ESD close to the antenna. Keep >= 3 mm between the module and other parts
(rework); drawn on Cmts.User.
MUST-verify: compare a printed 1:1 of this footprint against a real module's bottom (pin 1 chamfer, pad 60 ANT_MAIN at
top row x = -5.25) and re-check the pin table against the full "EG915U Series Hardware Design" (V1.3/1.4, Quectel login)
before ordering."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
NAME = "Quectel_EG915U"

# number -> name (standard EG915U firmware). "*" names in Quectel docs = under development; kept without the star.
PINS = {1: "PSM_IND", 2: "ADC1", 3: "GND", 4: "PCM_CLK", 5: "PCM_SYNC", 6: "PCM_DIN", 7: "PCM_DOUT",
        8: "USB_VBUS", 9: "USB_DP", 10: "USB_DM", 11: "RESERVED", 12: "RESERVED", 13: "RESERVED", 14: "RESERVED",
        15: "PWRKEY", 16: "RESERVED", 17: "RESET_N", 18: "W_DISABLE#", 19: "AP_READY", 20: "STATUS",
        21: "NET_STATUS", 22: "DBG_RXD", 23: "DBG_TXD", 24: "ADC0", 25: "SPI_CS", 26: "SPI_CLK", 27: "AUX_TXD",
        28: "AUX_RXD", 29: "VDD_EXT", 30: "MAIN_DTR", 31: "GND", 32: "VBAT_BB", 33: "VBAT_BB", 34: "MAIN_RXD",
        35: "MAIN_TXD", 36: "MAIN_CTS", 37: "MAIN_RTS", 38: "MAIN_DCD", 39: "MAIN_RI", 40: "I2C_SCL",
        41: "I2C_SDA", 42: "USIM1_DET", 43: "USIM1_VDD", 44: "USIM1_RST", 45: "USIM1_DATA", 46: "USIM1_CLK",
        47: "USIM1_GND", 48: "GND", 49: "RESERVED", 50: "GND", 51: "RESERVED", 52: "VBAT_RF", 53: "VBAT_RF",
        54: "GND", 55: "GND", 56: "ANT_BT/WIFI_SCAN", 57: "RESERVED", 58: "GND", 59: "GND", 60: "ANT_MAIN",
        61: "GND", 62: "GND", 63: "RESERVED", 64: "SPI_DOUT", 65: "RESERVED", 66: "RESERVED"}
PINS.update({n: "GND" for n in range(67, 75)})
PINS.update({75: "USB_BOOT", 76: "GRFC1", 77: "GRFC2", 78: "RESERVED"})
PINS.update({n: "GND" for n in range(79, 83)})
PINS.update({83: "USIM2_DET", 84: "USIM2_CLK", 85: "USIM2_RST", 86: "USIM2_DATA", 87: "USIM2_VDD", 88: "SPI_DIN",
             89: "GND", 90: "GND", 91: "GND", 92: "RESERVED", 93: "RESERVED", 94: "RESERVED", 95: "RESERVED",
             96: "PSM_EINT", 97: "RESERVED", 98: "RESERVED", 99: "RESERVED", 100: "GND", 101: "GND", 102: "GND"})
PINS.update({n: "RESERVED" for n in range(103, 119)})
PINS.update({119: "MIC_N", 120: "MICBIAS", 121: "SPK_P", 122: "SPK_N", 123: "HP_L", 124: "HP_R", 125: "HP_DET",
             126: "MIC_P"})
assert sorted(PINS) == list(range(1, 127))

# number -> (I/O type, domain/notes). Types per Quectel: AI/AO/AIO analog, DI/DO/DIO digital, OD, PI/PO power.
IO = {1: ("DO", "1.8 V; under development in std FW"), 2: ("AI", "0..VBAT"), 4: ("DI", "1.8 V, PCM slave only"),
      5: ("DI", "1.8 V"), 6: ("DI", "1.8 V"), 7: ("DO", "1.8 V"), 8: ("AI", "3.5..5.25 V, USB detect, test point"),
      9: ("AIO", "USB2.0 90R diff, test point"), 10: ("AIO", "USB2.0 90R diff, test point"),
      15: ("DI", "VBAT domain, active low, >=2 s on"), 17: ("DI", "VBAT domain, active low"),
      18: ("DI", "1.8 V; 3 V/0 V glitch at power-on"), 19: ("DI", "1.8 V; 3 V/0 V glitch at power-on"),
      20: ("DO", "1.8 V"), 21: ("DO", "1.8 V"), 22: ("DI", "1.8 V, debug UART 921600, test point"),
      23: ("DO", "1.8 V, debug UART, test point"), 24: ("AI", "0..VBAT"), 25: ("DO", "1.8 V; under development"),
      26: ("DO", "1.8 V; under development"), 27: ("DO", "1.8 V"), 28: ("DI", "1.8 V"),
      29: ("PO", "1.8 V, 50 mA max"), 30: ("DI", "1.8 V; 3 V/0 V glitch at power-on"),
      32: ("PI", "3.3..4.3 V, >=1 A"), 33: ("PI", "3.3..4.3 V, >=1 A"), 34: ("DI", "1.8 V"), 35: ("DO", "1.8 V"),
      36: ("DO", "1.8 V"), 37: ("DI", "1.8 V"), 38: ("DO", "1.8 V; 3 V/0 V glitch at power-on"),
      39: ("DO", "1.8 V; 3 V/0 V glitch at power-on"), 40: ("OD", "1.8 V, external pull-up"),
      41: ("OD", "1.8 V, external pull-up"), 42: ("DI", "1.8 V"), 43: ("PO", "1.8/3.0 V auto, 50 mA"),
      44: ("DO", "USIM_VDD"), 45: ("DIO", "USIM_VDD"), 46: ("DO", "USIM_VDD"), 47: ("-", "SIM ground"),
      52: ("PI", "3.3..4.3 V, >=2.5 A"), 53: ("PI", "3.3..4.3 V, >=2.5 A"), 56: ("AIO", "50 ohm, Rx only for Wi-Fi scan"),
      60: ("AIO", "50 ohm"), 64: ("DO", "1.8 V; under development"),
      75: ("DI", "1.8 V, active high; do NOT pull up before boot"), 76: ("DO", "1.8 V"), 77: ("DO", "1.8 V"),
      83: ("DI", "1.8 V"), 84: ("DO", "USIM2_VDD"), 85: ("DO", "USIM2_VDD"), 86: ("DIO", "USIM2_VDD"),
      87: ("PO", "1.8/3.0 V"), 88: ("DI", "1.8 V; under development"), 96: ("DI", "1.8 V, wake from PSM (high)"),
      119: ("AI", "analog"), 120: ("PO", "2.2..3.0 V"), 121: ("AO", "analog"), 122: ("AO", "analog"),
      123: ("AO", "analog"), 124: ("AO", "analog"), 125: ("DI", "headphone detect"), 126: ("AI", "analog")}

QUECOPEN_ALT = {16: "LCD_CS", 18: "W_DISABLE# (GPIO)", 19: "AP_READY (GPIO)", 30: "MAIN_DTR (GPIO)",
                38: "MAIN_DCD (GPIO)", 39: "MAIN_RI (GPIO)", 78: "CAM_SPI_CLK", 92: "LCD_TE", 93: "CAM_VDDIO",
                94: "CAM_VDD", 95: "CAM_MCLK", 97: "CAM_SPI_DATA0", 98: "CAM_SPI_DATA1", 103: "CAM_I2C_SCL",
                104: "GPIO5", 105: "LCD_SPI_CLK", 106: "LCD_SPI_RS", 107: "LCD_RST", 108: "LCD_SEL",
                109: "LCD_ISINK", 110: "SD_CLK", 111: "CAM_RST", 114: "CAM_I2C_SDA", 115: "CAM_PWDN",
                116: "LCD_SPI_DOUT"}

SOLID_GND = (55, 59, 61)          # GND pads next to RF pins: no thermal relief (Quectel 5.1.4)


def pads():
    """(num, x, y, w, h) in mm, top view, origin = module centre, y down."""
    P = []
    C, R = 9.125, 10.975
    P += [(n, -C, -9.7 + 1.1 * (n - 1), 1.05, 0.7) for n in range(1, 11)]     # left, top -> bottom
    P += [(n, -C, 1.9 + 1.1 * (n - 11), 1.05, 0.7) for n in range(11, 19)]
    P += [(n, -7.45 + 1.1 * (n - 19), R, 0.7, 1.05) for n in range(19, 25)]   # bottom, left -> right
    P += [(n, 0.55 + 1.1 * (n - 25), R, 0.7, 1.05) for n in range(25, 32)]
    P += [(n, C, 9.6 - 1.1 * (n - 32), 1.05, 0.7) for n in range(32, 40)]     # right, bottom -> top
    P += [(n, C, 0.2 - 1.1 * (n - 40), 1.05, 0.7) for n in range(40, 50)]
    P += [(n, 7.15 - 1.1 * (n - 50), -R, 0.7, 1.05) for n in range(50, 57)]   # top, right -> left
    P += [(n, -1.95 - 1.1 * (n - 57), -R, 0.7, 1.05) for n in range(57, 63)]
    grid = [[103, 114, 82, 81, 80, 79, 113, 112],                              # Fig 2, top view, row by row
            [104, 115, 102, 101, 100, 99, 118, 111],
            [63, 83, None, None, None, None, 98, 78],
            [64, 84, None, 119, 126, None, 97, 77],
            [65, 85, None, 120, 125, None, 96, 76],
            [66, 86, None, 121, 124, None, 95, 75],
            [67, 87, None, 122, 123, None, 94, 74],
            [68, 88, None, None, None, None, 93, 73],
            [105, 116, 89, 90, 91, 92, 117, 110],
            [106, 107, 69, 70, 71, 72, 108, 109]]
    for r, row in enumerate(grid):
        for c, n in enumerate(row):
            if n is not None:
                P.append((n, -5.95 + 1.7 * c, -7.65 + 1.7 * r, 1.0, 1.0))
    P = [(n, round(x, 4), round(y, 4), w, h) for n, x, y, w, h in P]
    assert sorted(p[0] for p in P) == list(range(1, 127))
    return P


def line(x1, y1, x2, y2, layer, w):
    return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'


def poly(pts, layer, w):
    return "".join(line(*pts[i], *pts[(i + 1) % len(pts)], layer, w) for i in range(len(pts)))


def text(t, x, y, layer, size=0.5):
    return (f'  (fp_text user "{t}" (at {x} {y}) (layer "{layer}") '
            f'(effects (font (size {size} {size}) (thickness {round(size * 0.15, 3)})) (justify left)))\n')


def build():
    BX, BY, CH = 9.95, 11.8, 1.0
    s = f'(footprint "{NAME}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += ('  (descr "Quectel EG915U-EU LTE Cat-1bis module, LGA-126, 19.9x23.6x2.4mm. Quectel EG915U QuecOpen HD V1.0 '
          'Fig 39/40 + Fig 2 pin assignment; pin names per BG95xA/EG915U/EG91xQ Compatible Design V1.0. JLC C7471302.")\n')
    s += '  (tags "Quectel EG915U LTE Cat1bis LGA126")\n'
    s += '  (attr smd)\n'
    s += '  (property "Reference" "U**" (at 0 -12.9) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
    s += '  (property "Value" "EG915U-EU" (at 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))\n'
    # F.Fab body with the C1.0 chamfer at the pin-1 corner (top-left, top view)
    s += poly([(-BX + CH, -BY), (BX, -BY), (BX, BY), (-BX, BY), (-BX, -BY + CH)], "F.Fab", 0.1)
    # F.CrtYd: body + 0.25
    c = 0.25
    s += poly([(-BX - c, -BY - c), (BX + c, -BY - c), (BX + c, BY + c), (-BX - c, BY + c)], "F.CrtYd", 0.05)
    # F.SilkS: corner brackets 0.15 outside the body, clear of the edge pads; pin-1 corner chamfered + dot
    o, L = BX + 0.15, 1.2
    t = BY + 0.15
    s += line(o, -t, o, -t + L, "F.SilkS", 0.12) + line(o, -t, o - L, -t, "F.SilkS", 0.12)
    s += line(o, t, o, t - L, "F.SilkS", 0.12) + line(o, t, o - L, t, "F.SilkS", 0.12)
    s += line(-o, t, -o, t - L, "F.SilkS", 0.12) + line(-o, t, -o + L, t, "F.SilkS", 0.12)
    s += line(-o, -t + CH + 0.06, -o + CH + 0.06, -t, "F.SilkS", 0.12)       # chamfer stroke at pin-1 corner
    s += line(-o + CH + 0.06, -t, -o + CH + 1.0, -t, "F.SilkS", 0.12)
    s += line(-o, -t + CH + 0.06, -o, -t + CH + 1.0, "F.SilkS", 0.12)
    s += '  (fp_circle (center -10.65 -9.7) (end -10.5 -9.7) (stroke (width 0.3) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    # Cmts.User: Quectel 3 mm clearance to other components, RF notes
    k = 3.0
    s += poly([(-BX - k, -BY - k), (BX + k, -BY - k), (BX + k, BY + k), (-BX - k, BY + k)], "Cmts.User", 0.05)
    s += text("3 mm to other parts (Quectel, rework)", -BX - k + 0.2, BY + k - 0.5, "Cmts.User", 0.5)
    s += poly([(-6.0, -11.7), (1.3, -11.7), (1.3, -10.25), (-6.0, -10.25)], "Cmts.User", 0.05)
    s += text("RF: 56 ANT_BT/WIFI_SCAN, 60 ANT_MAIN 50R CPWG, short, 135deg bends", -BX - k + 0.2, -BY - k + 0.6, "Cmts.User", 0.5)
    s += text("GND 55/59/61 solid (no thermal relief); vias >= 2W from RF trace", -BX - k + 0.2, -BY - k + 1.3, "Cmts.User", 0.5)
    s += text("pi-match 0R+2xNM + ESD at antenna; no copper under antenna-connector signal pin", -BX - k + 0.2, -BY - k + 2.0, "Cmts.User", 0.5)
    for n, x, y, w, h in pads():
        zc = " (zone_connect 2)" if n in SOLID_GND else ""
        s += (f'  (pad "{n}" smd rect (at {x} {y}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask")'
              f'{zc} (pinfunction "{PINS[n]}"))\n')
    s += ')\n'
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, NAME + ".kicad_mod"), "w").write(s)
    return len(pads())


def check(lib, name):
    """Load with pcbnew and print pad count, bbox and min gap between pads of different numbers (axis-aligned pads)."""
    import pcbnew
    fp = pcbnew.FootprintLoad(lib, name)
    P = []
    for p in fp.Pads():
        pos, sz = p.GetPosition(), p.GetSize()
        P.append((p.GetNumber(), pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y), pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y),
                  p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE, p.GetOrientationDegrees()))
    assert all(o % 180 == 0 for *_, o in P), "rotated pads not handled"
    bb = fp.GetBoundingBox(False)
    best = (1e9, None, None)
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            a, b = P[i], P[j]
            if a[0] == b[0] and a[0] != "":
                continue
            if a[5] and b[5]:
                g = ((a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** .5 - a[3] / 2 - b[3] / 2
            elif a[5] or b[5]:
                cc, r = (a, b) if a[5] else (b, a)
                dx = max(abs(cc[1] - r[1]) - r[3] / 2, 0); dy = max(abs(cc[2] - r[2]) - r[4] / 2, 0)
                g = (dx * dx + dy * dy) ** .5 - cc[3] / 2
            else:
                dx = max(abs(a[1] - b[1]) - (a[3] + b[3]) / 2, 0); dy = max(abs(a[2] - b[2]) - (a[4] + b[4]) / 2, 0)
                g = (dx * dx + dy * dy) ** .5
            if g < best[0]:
                best = (g, a[0] or "NPTH", b[0] or "NPTH")
    print(f"{name}: {len(P)} pads, bbox {pcbnew.ToMM(bb.GetWidth()):.3f} x {pcbnew.ToMM(bb.GetHeight()):.3f} mm "
          f"(x {pcbnew.ToMM(bb.GetLeft()):.3f}..{pcbnew.ToMM(bb.GetRight()):.3f}, "
          f"y {pcbnew.ToMM(bb.GetTop()):.3f}..{pcbnew.ToMM(bb.GetBottom()):.3f}), "
          f"min gap between different pads {best[0]:.3f} mm ({best[1]} - {best[2]})")


if __name__ == "__main__":
    print("wrote", build(), "pads")
    try:
        check(OUT, NAME)
    except ImportError:
        print("pcbnew not available: run with KiCad's python3 to check")
