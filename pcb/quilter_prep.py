"""Quilter (app.quilter.ai) input files from the placed board. Run with KiCad's python after make_board.py + route.py export:
    quilter_prep.py            -> quilter/A-route-only/  and  quilter/B-place-and-route/
Each folder holds phone.kicad_pro + phone.kicad_sch (gen_sch.py) + phone.kicad_pcb, linked (footprint paths = symbol uuids).

Common to both boards:
  - all vias, fan-out stubs and copper pours removed (Quilter treats leftover vias as intentional and regenerates pours);
    only the four locked 50 ohm antenna feed runs (route.py CHAINS) stay, Quilter keeps pre-routed copper as is.
  - inner layers named for Quilter: In1 'gnd', In4 'pwr' (its plane detection keys on those names), In2/In3 'sig1'/'sig2'.
  - net classes: CSI_* and the USB pairs in 'differentialpair' (Quilter's detection class; USB is 90 ohm, Quilter offers
    85 or 100, pick 85 for USB and 100 for CSI in the job's Differential Pairs table), RF50 + Power unchanged.
A: every part stays where make_board.py put it (Quilter only routes).
B: only the parts the case fixes stay (make_board ANCHOR: antennas, keys, connectors, module, modem, Talk ring, antenna
   feeds) plus whatever already sits in a restricted area (Talk button circle, under the battery, speaker); every other
   part goes off the board, where Quilter places it. The restricted areas become footprint keep-outs (with the pre-placed
   parts cut out), so nothing tall lands under the battery, the fingerprint module or in the antenna band."""
import os, sys, json, math, shutil, subprocess, pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I
HERE = os.path.dirname(os.path.abspath(__file__))
KPY = sys.executable
SRC = os.path.join(HERE, "phone.kicad_pcb")
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
CHAIN_NETS = {"WIFI_RF", "WIFI_ANT", "LTE_RF", "LTE_ANT"}
CX, CY = 100.0, 100.0

# make_board.py's anchors and keep-outs (exec only its top part: parts, anchors, keep-outs; no board is built)
src = open(os.path.join(HERE, "make_board.py")).read().split("# ------------------------------------------------------------------ board")[0]
MB = {"__file__": os.path.join(HERE, "make_board.py"), "__name__": "mb"}
exec(compile(src, "make_board.py", "exec"), MB)
ANCHOR, KEEP, CIRCLES = MB["ANCHOR"], MB["KEEP"], MB["CIRCLES"]

def common(b):
    for lay, name in ((pcbnew.In1_Cu, "gnd"), (pcbnew.In2_Cu, "sig1"), (pcbnew.In3_Cu, "sig2"), (pcbnew.In4_Cu, "pwr")):
        b.SetLayerName(lay, name)
    b.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER); b.SetLayerType(pcbnew.In4_Cu, pcbnew.LT_POWER)

def strip(b):
    """last step before Save: after the first Remove() KiCad 10's SWIG wrappers come back untyped"""
    drop = [z for z in b.Zones() if not z.GetIsRuleArea()]
    drop += [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() not in CHAIN_NETS or t.GetLayer() != pcbnew.F_Cu]
    for x in drop: b.Remove(x)

def link(b, outd):
    """footprint path = symbol uuid, LCSC field as in the schematic, and the schematic's 'unconnected-(...)' nets on nc pads
    (what KiCad's Update PCB from Schematic would do), so schematic parity DRC comes back clean."""
    import re, glob, importlib.util
    ids = json.load(open(os.path.join(outd, "sym_uuids.json")))["symbols"]
    spec = {}
    for fn in sorted(glob.glob(os.path.join(HERE, "sch_*.py"))):
        s = importlib.util.spec_from_file_location("m", fn); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
        for p in m.PARTS: spec[p["ref"]] = p
    net = os.path.join(outd, "phone.net")
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net, os.path.join(outd, "phone.kicad_sch")],
                   check=True, capture_output=True)
    nc = {}
    for m in re.finditer(r'\(name "(unconnected-[^"]*)"\)(.*?)\n\t\t\)', open(net).read(), re.S):
        for r, pn in re.findall(r'\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', m.group(2)): nc[(r, pn)] = m.group(1)
    os.remove(net)
    nets = {}
    for f in b.GetFootprints():
        ref = f.GetReference()
        if f.IsBoardOnly(): continue          # screw holes H1-H5: no symbol, no LCSC, no nets
        f.SetPath(pcbnew.KIID_PATH("/" + ids[ref]))
        f.SetSheetname("/"); f.SetSheetfile("phone.kicad_sch")
        fld = pcbnew.PCB_FIELD(f, pcbnew.FIELD_T_USER, "LCSC"); fld.SetText(spec[ref].get("lcsc", "")); fld.SetVisible(False)
        fld.SetLayer(pcbnew.F_Fab); fld.thisown = False; f.Add(fld)
        for pd in f.Pads():
            name = nc.get((ref, pd.GetNumber()))
            if name and not pd.GetNetname():
                if name not in nets:
                    ni = pcbnew.NETINFO_ITEM(b, name); ni.thisown = False; b.Add(ni); nets[name] = ni
                pd.SetNet(nets[name])

def mm(x, y): return VECTOR2I(FromMM(CX + x), FromMM(CY - y))

def courtyard(f):
    f.BuildCourtyardCaches()
    return f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)

def keepouts(b, fixed):
    made = 0
    # height-limit zones (a number: tallest part allowed, the screen underside) are not keep-outs for Quilter: it may
    # place there, and the order gate's fit_check rejects a candidate that put a part too tall under the screen
    for side, x0, y0, x1, y1, *rule in [k[:5] + (k[5],) for k in KEEP if not isinstance(k[5], float)] + [("C",) + c[:4] for c in CIRCLES]:
        poly = pcbnew.SHAPE_POLY_SET(); poly.NewOutline()
        if side == "C":                      # circle entry: ("C", side, cx, cy, r)
            side, cx, cy, r = x0, y0, x1, y1
            for i in range(48):
                a = 2 * math.pi * i / 48; poly.Append(mm(cx + r * math.cos(a), cy + r * math.sin(a)))
        else:
            for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): poly.Append(mm(x, y))
        clip = pcbnew.SHAPE_POLY_SET(); clip.NewOutline()      # stay inside the board outline (0.05 mm in)
        for x, y in ((-24.95, -50.95), (24.95, -50.95), (24.95, 50.95), (-24.95, 50.95)): clip.Append(mm(x, y))
        poly.BooleanIntersection(clip)
        for f in fixed:
            if ("B" if f.IsFlipped() else "F") != side: continue
            cy_ = pcbnew.SHAPE_POLY_SET(courtyard(f)); cy_.Inflate(FromMM(0.15), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FromMM(0.02))
            poly.BooleanSubtract(cy_)
        poly.Simplify()
        for i in range(poly.OutlineCount()):
            one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(poly.Outline(i))
            for h in range(poly.HoleCount(i)): one.AddHole(poly.Hole(i, h))
            if ToMM(ToMM(one.Area())) < 1.0: continue
            z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetLayer(pcbnew.B_Cu if side == "B" else pcbnew.F_Cu)
            z.SetDoNotAllowFootprints(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False)
            z.SetDoNotAllowPads(False); z.SetDoNotAllowZoneFills(False)
            z.SetZoneName(f"no_parts_{side}_{made}"); one.thisown = False; z.SetOutline(one); b.Add(z); made += 1   # the zone owns `one` now
    return made

def inside_restricted(f):
    p = f.GetPosition(); x, y = ToMM(p.x) - CX, CY - ToMM(p.y); side = "B" if f.IsFlipped() else "F"
    for s, x0, y0, x1, y1, rule in KEEP:
        if isinstance(rule, float): continue
        if s == side and x0 <= x <= x1 and y0 <= y <= y1: return True
    for s, cx, cy, r, rule in CIRCLES:
        if s == side and math.hypot(x - cx, y - cy) <= r: return True
    return False

def project(outd):
    d = json.load(open(os.path.join(HERE, "phone.kicad_pro")))
    ns = d["net_settings"]
    ns["classes"] = [c for c in ns["classes"] if c["name"] != "differentialpair"]   # stale copy from an older run
    for c in ns["classes"]:
        if c["name"] == "CSI100": c["name"] = "differentialpair"
    ns["classes"] = [c for c in ns["classes"] if c["name"] != "USB90"]
    for pt in ns.get("netclass_patterns", []):
        if pt["netclass"] in ("CSI100", "USB90"): pt["netclass"] = "differentialpair"
    d["meta"]["filename"] = "phone.kicad_pro"
    json.dump(d, open(os.path.join(outd, "phone.kicad_pro"), "w"), indent=2)

def build(variant):
    outd = os.path.join(HERE, "quilter", variant); os.makedirs(outd, exist_ok=True)
    subprocess.run([KPY, os.path.join(HERE, "gen_sch.py"), SRC, outd], check=True)
    subprocess.run([CLI, "sch", "upgrade", os.path.join(outd, "phone.kicad_sch")], check=True, capture_output=True)
    project(outd)
    b = pcbnew.LoadBoard(SRC)
    common(b); link(b, outd)
    note = ""
    if variant.startswith("B"):
        fixed = [f for f in b.GetFootprints() if f.GetReference() in ANCHOR or f.IsBoardOnly() or inside_restricted(f)]   # screw holes stay
        fixed_refs = {f.GetReference() for f in fixed}
        nz = keepouts(b, fixed)
        x, y, row = 40.0, 50.0, 0.0                       # off-board parking, right of the board, rows downward
        for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
            if f.GetReference() in fixed_refs: continue
            if f.IsFlipped(): f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            f.SetOrientation(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
            bb = f.GetBoundingBox(False); w, h = ToMM(bb.GetWidth()) + 1.0, ToMM(bb.GetHeight()) + 1.0
            if x + w > 140: x, y, row = 40.0, y - row, 0.0
            f.SetPosition(mm(x + w / 2, y - h / 2)); x += w; row = max(row, h)
        note = f", {len(fixed_refs)} pre-placed, {len(b.GetFootprints()) - len(fixed_refs)} off-board, {nz} keep-outs"
    out = os.path.join(outd, "phone.kicad_pcb")
    strip(b)
    b.Save(out)
    for junk in ("phone.kicad_prl", "sym_uuids.json"):
        if os.path.exists(os.path.join(outd, junk)): os.remove(os.path.join(outd, junk))
    print(f"{variant}: written{note}")

if len(sys.argv) > 1: build(sys.argv[1])
else:   # one process per variant: after a Remove() KiCad 10's SWIG wrappers stay broken for the rest of the process
    for v in ("A-route-only", "B-place-and-route"): subprocess.run([KPY, __file__, v], check=True)
