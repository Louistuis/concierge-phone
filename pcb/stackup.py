"""Writes JLC's 6-layer 1.0 mm impedance stackup JLC06101H-3313 into a .kicad_pcb (setup > stackup) and sets the board
thickness, so Quilter ('stackup from input file') and KiCad's impedance tools see the real board.   stackup.py board.kicad_pcb
Source: jlcpcb.com/impedance data for 6 layers / 1.0 mm, read 2026-11-14 (scratchpad stackup/web/six_1.0.json):
  F.Cu 1 oz | 3313 prepreg 0.0994 Er 4.1 | In1 0.5 oz | core 0.25 Er 4.23 (calculator) / 4.6 (impedance page) | In2 0.5 oz |
  7628 prepreg 0.2104 (order data; calculator 0.2028) Er 4.4 | In3 0.5 oz | core 0.25 | In4 0.5 oz | 3313 0.0994 | B.Cu 1 oz.
Loss tangent is not published by JLC: 0.02 is KiCad's FR-4 placeholder. Total 1.040 mm (JLC: 1.03 +-10 %)."""
import re, sys
CU_OUT, CU_IN = 0.035, 0.0152
LAYERS = [("F.SilkS", "Top Silk Screen", None), ("F.Paste", "Top Solder Paste", None),
          ("F.Mask", "Top Solder Mask", (0.01, "LPI", 3.8, None)),
          ("F.Cu", "copper", CU_OUT), ("dielectric 1", "prepreg", (0.0994, "3313 RC57%", 4.1, 0.02)),
          ("In1.Cu", "copper", CU_IN), ("dielectric 2", "core", (0.25, "FR4 core", 4.23, 0.02)),
          ("In2.Cu", "copper", CU_IN), ("dielectric 3", "prepreg", (0.2104, "7628 RC49%", 4.4, 0.02)),
          ("In3.Cu", "copper", CU_IN), ("dielectric 4", "core", (0.25, "FR4 core", 4.23, 0.02)),
          ("In4.Cu", "copper", CU_IN), ("dielectric 5", "prepreg", (0.0994, "3313 RC57%", 4.1, 0.02)),
          ("B.Cu", "copper", CU_OUT), ("B.Mask", "Bottom Solder Mask", (0.01, "LPI", 3.8, None)),
          ("B.Paste", "Bottom Solder Paste", None), ("B.SilkS", "Bottom Silk Screen", None)]

def block(t="\t\t"):
    out = [f"{t}(stackup"]
    for name, typ, v in LAYERS:
        s = f'{t}\t(layer "{name}" (type "{typ}")'
        if isinstance(v, float): s += f" (thickness {v})"
        elif v:
            th, mat, er, tan = v
            s += f' (thickness {th}) (material "{mat}") (epsilon_r {er})' + (f" (loss_tangent {tan})" if tan else "")
        out.append(s + ")")
    out += [f'{t}\t(copper_finish "ENIG")', f"{t}\t(dielectric_constraints no)", f"{t})"]
    return "\n".join(out) + "\n"

def total():
    return round(sum(v if isinstance(v, float) else v[0] for _, typ, v in LAYERS if v and "Mask" not in typ), 4)

def patch(path):
    s = open(path).read()
    s = re.sub(r"\n\t\t\(stackup\n.*?\n\t\t\)\n", "\n", s, flags=re.S)          # drop an old stackup block
    s = s.replace("\n\t(setup\n", "\n\t(setup\n" + block(), 1)
    s = re.sub(r"(\(general\s*\n\s*\(thickness )[0-9.]+", lambda m: m.group(1) + str(total()), s, count=1)
    open(path, "w").write(s)
    return total()

if __name__ == "__main__":
    for p in sys.argv[1:]: print(p, "stackup JLC06101H-3313, thickness", patch(p))
