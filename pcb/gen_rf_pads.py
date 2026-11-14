"""Writes the RF/tools footprints that have no stock KiCad equivalent into phone.pretty (used by sch_rf.py):

NFC_ANT_PADS  - landing pads for the Molex 1462360111 NFC antenna (23 x 27.3 mm, ferrite backed, C17350773). The antenna
                is NOT placed by JLC: it sticks under the front plate and touches two gold SMD spring contacts soldered on
                these pads. Molex drawing 146236 rev H (LCSC datasheet for C17350773): the antenna tab carries two solder
                pads 2.00 x 3.00 mm with a 0.50 mm gap, i.e. 2.50 mm pitch. Our pads: 1.5 x 2.0 mm on the same 2.50 mm
                pitch so each spring contact lands in the middle of one antenna pad. Pad 1 = NFC_ANT1, pad 2 = NFC_ANT2
                (the coil is symmetric, the order does not matter).
LF_COIL_PADS  - two 1.2 x 1.6 mm pads, 2.54 mm pitch, for the hand-wound 125 kHz coil wires (~50 turns 0.1 mm CuL around
                the NFC antenna ferrite). Not placed by JLC.
Everlight_IR12-21C - IR12-21C/TR8 940 nm chip LED with right-angle lens (C53672), body 3.0 x 1.0 x 2.0 mm.
                Everlight datasheet DIR-0000971 rev 8 p.2 "For reflow soldering (propose)": two 0.8 mm wide lands at the
                body ends, inner gap 0.65 + 0.9 + 0.65 = 2.2 mm -> pad centres +-1.5 mm. The pad depth is not given:
                1.2 mm used (body depth 1.0 + 0.1 each side). Pad 1 = anode, pad 2 = cathode (datasheet polarity drawing:
                1 right, 2 left, top view). The lens emits parallel to the board (right-angle lens): place the part on the
                top board edge with the lens facing out. MUST-verify the emission side against a real part.
Johanson_0868AT43A0020 - 868 MHz ceramic chip antenna 7.0 x 2.0 x 0.8 mm (C3284550). Johanson spec 0868AT43A0020 v1.8
                p.1 "Mounting Considerations I": two 1.0 x 1.8 mm lands, 6.0 mm apart inside an 8.0 mm span -> centres
                +-3.5 mm. Pad 1 = feeding point, pad 2 = NC electrically but it carries the 0.5 mm wide tuning stub
                (down 5.1, left 7.1, up 3.0, right 5.1 mm, drawn here as copper-only segments of pad 2). The stub
                geometry is read off the drawing (not every corner is dimensioned): treat its length as a tuning element.
                p.3: the antenna wants a corner of the board with an ~11 x 10 mm area free of copper on ALL layers; a
                keep-out (no pour, no vias; the feed track is allowed) is drawn around antenna + stub.
Run with KiCad's python or any python3."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")
os.makedirs(OUT, exist_ok=True)


def line(x1, y1, x2, y2, layer, w):
    return f'  (fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'


def rect(x1, y1, x2, y2, layer, w):
    return (line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) +
            line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w))


def head(name, descr, ref_y, val_y):
    return (f'(footprint "{name}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
            f'  (descr "{descr}")\n  (attr smd)\n'
            f'  (property "Reference" "REF**" (at 0 {ref_y}) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
            f'  (property "Value" "{name}" (at 0 {val_y}) (layer "F.Fab") (effects (font (size 0.6 0.6) (thickness 0.1))))\n')


def pad(num, x, y, w, h, fn="", layers='"F.Cu" "F.Paste" "F.Mask"'):
    f = f' (pinfunction "{fn}")' if fn else ""
    return f'  (pad "{num}" smd rect (at {x:.3f} {y:.3f}) (size {w:.3f} {h:.3f}) (layers {layers}){f})\n'


def write(name, body):
    open(os.path.join(OUT, name + ".kicad_mod"), "w").write(body + ")\n")
    print("wrote", name)


# --- NFC antenna landing pads -------------------------------------------------------------------------------------
s = head("NFC_ANT_PADS", "Landing pads for spring contacts to the Molex 1462360111 NFC antenna tab (2.5 mm pitch). Not placed by JLC.", -2.0, 2.0)
s += pad("1", -1.25, 0, 1.5, 2.0, "NFC_ANT1") + pad("2", 1.25, 0, 1.5, 2.0, "NFC_ANT2")
s += rect(-2.25, -1.25, 2.25, 1.25, "F.Fab", 0.1) + rect(-2.5, -1.5, 2.5, 1.5, "F.CrtYd", 0.05)
write("NFC_ANT_PADS", s)

# --- NFC antenna pogo pin (2026-11-14 fit review: bare pads + a 2.5 mm placeholder never reached the antenna) ----------
# KERUI KTR47003UT01-R (LCSC C55342463), drawing on the LCSC datasheet: base flange D2.00 +-0.05, barrel D1.50, plunger
# D1.00, free height 4.70 +-0.15, normal working 4.00, max working 4.20, max compression 3.65. Board top to the Molex
# 146236 antenna tab = 3.83 mm (fit_check.py), inside 3.65..4.20. One pin per footprint (one LCSC part per designator).
s = head("Pogo_KTR47003_D2.0", "SMD pogo pin KERUI KTR47003UT01-R (C55342463), flange D2.0, land D2.2, 4.0 mm working height", -1.6, 1.6)
s += '  (pad "1" smd circle (at 0 0) (size 2.2 2.2) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
s += '  (fp_circle (center 0 0) (end 1.0 0) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))\n'
s += '  (fp_circle (center 0 0) (end 1.2 0) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))\n'
write("Pogo_KTR47003_D2.0", s)

# --- 125 kHz coil wire pads -----------------------------------------------------------------------------------------
s = head("LF_COIL_PADS", "Solder pads for the hand-wound 125 kHz coil wires, 2.54 mm pitch. Not placed by JLC.", -1.7, 1.7)
s += pad("1", -1.27, 0, 1.2, 1.6, "LF_COIL1") + pad("2", 1.27, 0, 1.2, 1.6, "LF_COIL2")
s += rect(-2.12, -1.05, 2.12, 1.05, "F.CrtYd", 0.05)
write("LF_COIL_PADS", s)

# --- Coilcraft 4308RV 125 kHz ferrite-rod coil (2026-11-14 night: replaces the hand-wound coil) -------------------------
# Coilcraft Document 324-2 (rev 12/02/21) "Recommended Land Pattern": pads 1.78 x 2.79, inner gap 8.46, outer 12.01
# -> centres +-5.115. Body 11.43 max x 3.15 max x 2.74 max. MSL1, three 260 C reflows. Keep copper off the rod ends.
s = head("Coilcraft_4308RV", "Coilcraft 4308RV RFID coil 11.43x3.15x2.74 mm, land pattern Doc 324-2", -2.6, 2.6)
s += pad("1", -5.115, 0, 1.78, 2.79, "1") + pad("2", 5.115, 0, 1.78, 2.79, "2")
s += rect(-5.715, -1.575, 5.715, 1.575, "F.Fab", 0.1)
s += rect(-6.26, -1.85, 6.26, 1.85, "F.CrtYd", 0.05)
write("Coilcraft_4308RV", s)

# --- Everlight IR12-21C right-angle IR LED --------------------------------------------------------------------------
s = head("Everlight_IR12-21C", "Everlight IR12-21C/TR8 940nm chip IR LED, right-angle lens, 3.0x1.0x2.0mm. Lands from datasheet DIR-0000971 p.2.", -1.4, 1.4)
s += pad("1", 1.5, 0, 0.8, 1.2, "A") + pad("2", -1.5, 0, 0.8, 1.2, "K")
s += rect(-1.5, -0.5, 1.5, 0.5, "F.Fab", 0.1)
s += line(-0.3, -0.5, -0.3, -1.0, "F.Fab", 0.1) + line(0.3, -0.5, 0.3, -1.0, "F.Fab", 0.1)  # lens side (verify)
s += line(-1.0, -0.75, 1.0, -0.75, "F.SilkS", 0.12)
s += line(-2.2, 0.75, -2.2, -0.75, "F.SilkS", 0.12)  # cathode side mark
s += rect(-2.15, -1.25, 2.15, 0.85, "F.CrtYd", 0.05)
write("Everlight_IR12-21C", s)

# --- Johanson 0868AT43A0020 chip antenna ----------------------------------------------------------------------------
s = head("Johanson_0868AT43A0020", "Johanson 0868AT43A0020 868MHz chip antenna 7x2mm, lands + tuning stub per spec v1.8 p.1, ground-free corner per p.3.", -2.0, 7.2)
s += pad("1", -3.5, 0, 1.0, 1.8, "FEED") + pad("2", 3.5, 0, 1.0, 1.8, "NC")
cu = '"F.Cu"'
# stub (pad 2 copper only): right leg down from the pad, bottom run left, left leg up, top run right
s += pad("2", 3.75, 3.45, 0.5, 5.1, "NC", cu)       # x 3.5..4.0, y 0.9..6.0
s += pad("2", 0.45, 5.75, 7.1, 0.5, "NC", cu)       # x -3.1..4.0, y 5.5..6.0
s += pad("2", -2.85, 4.5, 0.5, 3.0, "NC", cu)       # x -3.1..-2.6, y 3.0..6.0
s += pad("2", -0.55, 3.25, 5.1, 0.5, "NC", cu)      # x -3.1..2.0, y 3.0..3.5
s += rect(-3.5, -1.0, 3.5, 1.0, "F.Fab", 0.1)
s += line(-2.6, -1.3, 2.6, -1.3, "F.SilkS", 0.12)
s += rect(-5.0, -2.0, 5.5, 7.0, "F.CrtYd", 0.05)
s += ('  (zone (net 0) (net_name "") (layers "F.Cu" "In1.Cu" "In2.Cu" "B.Cu") (hatch edge 0.5)\n'
      '    (connect_pads (clearance 0))\n    (min_thickness 0.25)\n'
      '    (keepout (tracks allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))\n'
      '    (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))\n'
      '    (polygon (pts (xy -4.5 -1.6) (xy 5.5 -1.6) (xy 5.5 7.0) (xy -4.5 7.0))))\n')
s += '  (fp_text user "no GND/pour on any layer in this corner (Johanson p.3)" (at 0.5 7.6) (layer "Cmts.User") (effects (font (size 0.4 0.4) (thickness 0.06))))\n'
write("Johanson_0868AT43A0020", s)
