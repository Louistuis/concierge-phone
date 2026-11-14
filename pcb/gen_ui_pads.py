"""Writes two plain landing footprints for sch_ui.py into phone.pretty:

SPK_SPRING_PADS_2P_P4.0mm  speaker landing (LS70). The speaker is NOT on the board: it sits in its enclosure pocket and its
  two gold spring contacts press onto these pads (box speaker ~15 x 11 mm, AAC/Ruiside 1511 class, or a wired FUET
  FS16MS0810 soldered here). Pads 2.0 x 2.6 mm on 4.0 mm centres: big on purpose so a spring contact lands anywhere in
  +-0.5 mm of the nominal spot. No paste (bare ENIG, nothing to reflow). Pad 1 = SPK + (silk "+").
  Re-check the pitch against the chosen speaker's contact drawing before ordering (no speaker drawing was read).
LRA_WIRE_PADS_2P_P2.0mm  wire landing for the LEADER LD0832AA-0099F coin LRA (M70): leads are AWG32 UL3302 wires
  (LEADER spec p.12), soldered by hand after assembly. Pads 1.0 x 1.5 mm on 2.0 mm centres, no paste.
  Pad 1 = OUT+ side (polarity does not matter for an LRA)."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone.pretty")

def line(x1, y1, x2, y2, layer, w):
    return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
def rect(x1, y1, x2, y2, layer, w):
    return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)

def two_pad(name, descr, pitch, pw, ph, ref, plus=True):
    s = f'(footprint "{name}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += f'  (descr "{descr}")\n  (attr smd)\n'
    s += f'  (property "Reference" "{ref}" (at 0 {-(ph / 2 + 0.8)}) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))\n'
    s += f'  (property "Value" "{name}" (at 0 {ph / 2 + 0.8}) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))\n'
    x = pitch / 2
    s += rect(-(x + pw / 2 + 0.25), -(ph / 2 + 0.25), x + pw / 2 + 0.25, ph / 2 + 0.25, "F.CrtYd", 0.05)
    if plus:
        px = -(x + pw / 2 + 0.55)
        s += line(px - 0.25, 0, px + 0.25, 0, "F.SilkS", 0.12) + line(px, -0.25, px, 0.25, "F.SilkS", 0.12)
    s += f'  (pad "1" smd rect (at {-x} 0) (size {pw} {ph}) (layers "F.Cu" "F.Mask") (pinfunction "+"))\n'
    s += f'  (pad "2" smd rect (at {x} 0) (size {pw} {ph}) (layers "F.Cu" "F.Mask") (pinfunction "-"))\n'
    s += ')\n'
    open(os.path.join(OUT, name + ".kicad_mod"), "w").write(s)
    print("wrote", name)

def dome(name="SnapDome_4mm"):
    """4 mm four-leg metal snap dome (phone-style key under the fingerprint Talk button). Centre pad = contact under the
    dome's apex, outer ring = where the legs rest (GND). Dome is applied by hand with its carrier tape after assembly."""
    s = f'(footprint "{name}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "4 mm metal snap dome landing: centre pad 1.6 mm (pad 1, signal), ring 3.2-4.6 mm (pad 2, GND), no paste")\n  (attr smd)\n'
    s += '  (property "Reference" "SW**" (at 0 -3.2) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))\n'
    s += f'  (property "Value" "{name}" (at 0 3.2) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))\n'
    s += '  (fp_circle (center 0 0) (end 2.55 0) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))\n'
    s += '  (pad "1" smd circle (at 0 0) (size 1.6 1.6) (layers "F.Cu" "F.Mask"))\n'
    # ring as a custom pad: annulus 3.2..4.6 mm drawn as a thick circle primitive
    s += ('  (pad "2" smd custom (at 0 2.0) (size 0.6 0.6) (layers "F.Cu" "F.Mask") (options (clearance outline) (anchor circle))\n'
          '    (primitives (gr_circle (center 0 -2.0) (end 1.95 -2.0) (width 0.7) (fill no))))\n')
    s += ')\n'
    open(os.path.join(OUT, name + ".kicad_mod"), "w").write(s); print("wrote", name)

def tsop57(name="Vishay_TSOP57xxx_3.95x3.95mm"):
    """Vishay TSOP572/573/574 top-view IR receiver, 3.95 x 3.95 x 0.8 mm (datasheet doc 82434 rev 2.9 p.7, drawing
    6.550-5315.01-4). Proposed pad layout: 4 pads 0.35 x 0.8 on a 3.0 x 2.75 grid. Pinning from top view:
    1 OUT (bottom-left), 5 VS (bottom-right), 6 GND (top-right), 8 GND (top-left); 2/3/4/7 are internal, no pad."""
    s = f'(footprint "{name}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "Vishay TSOP57xxx 3.95x3.95x0.8 top-view IR receiver, proposed pad layout doc 82434 p.7")\n  (attr smd)\n'
    s += '  (property "Reference" "U**" (at 0 -2.8) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))\n'
    s += f'  (property "Value" "{name}" (at 0 2.8) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))\n'
    s += rect(-2.225, -2.225, 2.225, 2.225, "F.CrtYd", 0.05) + rect(-1.975, -1.975, 1.975, 1.975, "F.Fab", 0.1)
    s += line(-2.1, 1.0, -2.1, 2.1, "F.SilkS", 0.12) + line(-2.1, 2.1, -1.0, 2.1, "F.SilkS", 0.12)   # pin-1 corner
    for num, x, y in (("1", -1.5, 1.375), ("5", 1.5, 1.375), ("6", 1.5, -1.375), ("8", -1.5, -1.375)):
        s += f'  (pad "{num}" smd rect (at {x} {y}) (size 0.35 0.8) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
    s += ')\n'
    open(os.path.join(OUT, name + ".kicad_mod"), "w").write(s); print("wrote", name)

def mount_hole(name="MountingHole_M1.4_NPTH"):
    """Board screw hole (2026-11-14): M1.4 pan-head screw from the front into a tapped aluminium boss that rises from the
    back wall (boss Ø3.0 sets the board height, so a swelling battery can't push the board into the screen). NPTH 1.6,
    keep-out Ø3.0 on BOTH sides (head Ø2.6 on the front, boss Ø3.0 on the back). Board-only: no BOM, no CPL, no schematic."""
    s = f'(footprint "{name}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "M1.4 screw hole, NPTH 1.6 mm, keep-out 3.0 mm both sides (front head, back boss)")\n'
    s += '  (attr board_only exclude_from_pos_files exclude_from_bom)\n'
    s += '  (property "Reference" "H**" (at 0 -2.4) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
    s += f'  (property "Value" "{name}" (at 0 2.4) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))\n'
    for lay in ("F.CrtYd", "B.CrtYd"):
        s += f'  (fp_circle (center 0 0) (end 1.5 0) (stroke (width 0.05) (type solid)) (fill none) (layer "{lay}"))\n'
    s += '  (pad "" np_thru_hole circle (at 0 0) (size 1.6 1.6) (drill 1.6) (layers "*.Cu" "*.Mask"))\n'
    s += ')\n'
    open(os.path.join(OUT, name + ".kicad_mod"), "w").write(s); print("wrote", name)

def gswitch2(name="GSwitch_GT-BTP20002-0170B_2P_P2.0"):
    """G-Switch GT-BTP20002-0170B-020A 2-pin battery spring contact (LCSC C55079717), drawing GT-BTP200XX-0170B-020A
    rev A0 2024-12-12: housing 4.0 x 6.0 x 1.7, contacts 1.35 +-0.2 above it (free 3.05), working height 2.0, pitch 2.0.
    PCB reference diagram: 2 pads 1.70 x 2.20 on 2.00 at one end of the housing (3.95 from the pad edge to the far end).
    The contact apex sits ~1.3-1.65 from the pad end (side view 6.10 - 4.8 ref / 4.45): origin = apex, pads at y -0.4.
    Presses the flex-tail pads of the Vybronics VG0832009L LRA (M70). MUST-verify the apex position on a sample."""
    s = f'(footprint "{name}"\n  (version 20240108)\n  (generator "claude")\n  (layer "F.Cu")\n'
    s += '  (descr "G-Switch GT-BTP20002-0170B-020A 2P 2.0 mm spring contact, working height 2.0")\n  (attr smd)\n'
    s += '  (property "Reference" "M**" (at 0 -2.6) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))\n'
    s += f'  (property "Value" "{name}" (at 0 5.4) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))\n'
    s += rect(-2.0, -1.5, 2.0, 4.5, "F.Fab", 0.1) + rect(-2.25, -1.75, 2.25, 4.75, "F.CrtYd", 0.05)
    for num, x in (("1", -1.0), ("2", 1.0)):
        s += f'  (pad "{num}" smd rect (at {x} -0.4) (size 1.7 2.2) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
    s += ')\n'
    open(os.path.join(OUT, name + ".kicad_mod"), "w").write(s); print("wrote", name)

if __name__ == "__main__":
    dome(); tsop57(); mount_hole(); gswitch2()
    two_pad("SPK_SPRING_PADS_2P_P2.4mm",
            "Same Sky CMS-16093-078S spring contacts: recommended pad layout (drawing p.2) 2 pads on 2.4 mm, 3.7 mm overall, no paste. Pad 1 = SPK+",
            2.4, 1.3, 1.6, "LS**")
    os.makedirs(OUT, exist_ok=True)
    two_pad("SPK_SPRING_PADS_2P_P4.0mm",
            "Speaker spring-contact landing, 2 pads 2.0x2.6 mm on 4.0 mm, no paste. Pad 1 = SPK+ (MAX98357A OUTP)",
            4.0, 2.0, 2.6, "LS**")
    two_pad("LRA_WIRE_PADS_2P_P2.0mm",
            "Hand-solder wire landing for LEADER LD0832AA LRA (AWG32 leads), 2 pads 1.0x1.5 mm on 2.0 mm, no paste",
            2.0, 1.0, 1.5, "M**")
