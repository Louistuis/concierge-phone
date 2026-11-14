"""Dumps the board geometry for board_map.py (KiCad's python):  export_view.py [board] > shots/board.json
Per footprint: ref, side, centre (front-view mm, y up, origin = board centre), courtyard outline, pads (centre, size,
rotation, round?). Board outline is the 50 x 102 r4 rectangle from make_board.py."""
import sys, json, os, pcbnew
from pcbnew import ToMM
HERE = os.path.dirname(os.path.abspath(__file__))
b = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "phone.kicad_pcb"))
X = lambda v: ToMM(v.x) - 100.0
Y = lambda v: 100.0 - ToMM(v.y)
out = []
for f in b.GetFootprints():
    back = f.IsFlipped()
    f.BuildCourtyardCaches()
    cy = f.GetCourtyard(pcbnew.B_CrtYd if back else pcbnew.F_CrtYd)
    poly = []
    if cy.OutlineCount():
        o = cy.Outline(0)
        poly = [(X(o.CPoint(i)), Y(o.CPoint(i))) for i in range(o.PointCount())]
    if not poly:
        bb = f.GetBoundingBox(False)
        poly = [(ToMM(bb.GetLeft()) - 100, 100 - ToMM(bb.GetTop())), (ToMM(bb.GetRight()) - 100, 100 - ToMM(bb.GetTop())),
                (ToMM(bb.GetRight()) - 100, 100 - ToMM(bb.GetBottom())), (ToMM(bb.GetLeft()) - 100, 100 - ToMM(bb.GetBottom()))]
    pads = []
    for p in f.Pads():
        s = p.GetSize(pcbnew.F_Cu) if hasattr(p, "GetSize") else p.GetSize()
        pads.append({"x": X(p.GetPosition()), "y": Y(p.GetPosition()), "w": ToMM(s.x), "h": ToMM(s.y),
                     "a": p.GetOrientation().AsDegrees(), "round": p.GetShape(pcbnew.F_Cu) == pcbnew.PAD_SHAPE_CIRCLE
                     if hasattr(pcbnew, "PAD_SHAPE_CIRCLE") else False,
                     "npth": p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH})
    out.append({"ref": f.GetReference(), "side": "B" if back else "F", "x": X(f.GetPosition()), "y": Y(f.GetPosition()),
                "court": poly, "pads": pads})
json.dump(out, sys.stdout)
