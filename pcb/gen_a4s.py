"""Writes phone.pretty/Panasonic_AXE534127_A4S_34P.kicad_mod: Panasonic A4S 0.4 mm board-to-FPC socket, 34 pins
(AXE534127, LCSC C6863072), mates the AXE634124 header on the Waveshare/Makerfabs 1.8" 368x448 AMOLED (CO5300/SH8601).
Land pattern: Panasonic A4S catalog ACCTB7E (Oct 2021) p.8 recommended PCB pattern, read at 1600 dpi:
signal pads 0.23 x 0.50 at 0.40 pitch, X -3.20..+3.20, rows at Y +-1.20 (pads Y 0.95..1.45); 4 hold-downs 0.90 x 0.92 at
X +-4.20, Y +-0.99; insulation area Y +-0.10..+-0.95 under the contacts = no exposed copper, no vias.
Numbering: panel pin list is odd/even (2k-1 faces 2k across the rows). Panasonic defines no pin 1 (part is symmetric).
Here: odd row at Y = -1.20, pin 1 at X = -3.20, so pins 1/2 at the left end and 33/34 at the right end.
MUST-verify: on a real Waveshare board, meter the socket: one row ends in 7 grounds (21..33), pins 3+4 grounded and facing,
pin 34 -> VPP test point. That fixes which panel end goes where; flip this footprint 180 deg if needed."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
os.makedirs(OUT, exist_ok=True)

# 1.8" AMOLED flex pin list (Makerfabs panel table, Waveshare wiring), QSPI mode
PINS = {1: "LCD_RESET", 2: "TE", 3: "GND(DCX)", 4: "GND", 5: "QSPI_D0", 6: "NC", 7: "QSPI_D1", 8: "TP_SCL",
        9: "QSPI_CLK", 10: "TP_SDA", 11: "LCD_CS", 12: "TP_INT", 13: "QSPI_D2", 14: "TP_RESET", 15: "QSPI_D3",
        16: "TP_VCC", 17: "IM1", 18: "VBAT", 19: "IM0", 20: "VBAT", 21: "GND", 22: "PWR_EN", 23: "MIPI_CLKP(GND)",
        24: "VCI", 25: "MIPI_CLKN(GND)", 26: "VDDIO", 27: "GND", 28: "GND", 29: "MIPI_D0P(GND)", 30: "NC",
        31: "MIPI_D0N(GND)", 32: "NC", 33: "GND", 34: "VPP(test)"}

if __name__ == "__main__":
    def line(x1, y1, x2, y2, layer, w):
        return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
    def rect(x1, y1, x2, y2, layer, w):
        return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)
    s = '(footprint "Panasonic_AXE534127_A4S_34P"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "Panasonic A4S 34-pin 0.4mm board-to-FPC socket AXE534127 (C6863072), pattern from catalog ACCTB7E p.8")\n  (attr smd)\n'
    s += '  (property "Reference" "J**" (at 0 -2.4) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))\n'
    s += '  (property "Value" "AXE534127" (at 0 2.4) (layer "F.Fab") (effects (font (size 0.6 0.6) (thickness 0.1))))\n'
    s += rect(-4.65, -1.25, 4.65, 1.25, "F.Fab", 0.1)
    s += rect(-5.0, -1.75, 5.0, 1.75, "F.CrtYd", 0.05)
    s += rect(-3.4, -0.95, 3.4, 0.95, "Cmts.User", 0.05)   # insulation area: mask only, no vias
    s += '  (fp_circle (center -3.2 -1.95) (end -3.1 -1.95) (stroke (width 0.2) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    for k in range(17):
        x = round(-3.2 + 0.4 * k, 3)
        s += f'  (pad "{2*k+1}" smd rect (at {x} -1.2) (size 0.23 0.5) (layers "F.Cu" "F.Paste" "F.Mask") (pinfunction "{PINS[2*k+1]}"))\n'
        s += f'  (pad "{2*k+2}" smd rect (at {x} 1.2) (size 0.23 0.5) (layers "F.Cu" "F.Paste" "F.Mask") (pinfunction "{PINS[2*k+2]}"))\n'
    for x in (-4.2, 4.2):   # hold-downs (each end pair is one metal piece): ground them
        for y in (-0.99, 0.99):
            s += f'  (pad "MP" smd rect (at {x} {y}) (size 0.9 0.92) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
    s += ')\n'
    open(os.path.join(OUT, "Panasonic_AXE534127_A4S_34P.kicad_mod"), "w").write(s)
    print("wrote 34 + 4 MP pads")
