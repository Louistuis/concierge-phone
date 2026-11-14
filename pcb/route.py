"""6-layer routing helper for phone.kicad_pcb (KiCad's python).
  route.py export -> rules, In1 solid GND plane, In4 3V3 plane, a fan-out via from every GND / 3V3 SMD pad to its plane,
                     phone.dsn for Freerouting (routes on F, In2, In3, B)
  route.py import -> reads phone.ses, re-adds missing fan-outs, pours GND on F/B/In2/In3 leftovers, saves phone_routed.kicad_pcb
Rules: JLCPCB 6-layer class with margin: 0.1 mm track / 0.1 mm clearance, vias 0.35/0.2 mm (JLC min 0.25/0.15)."""
import os, sys, math, pcbnew
from pcbnew import FromMM
HERE = os.path.dirname(os.path.abspath(__file__))
SRC, DSN, SES, OUT = (os.path.join(HERE, n) for n in ("phone.kicad_pcb", "phone.dsn", "phone.ses", "phone_routed.kicad_pcb"))
POWER = ["VBUS", "VBUS_CONN", "VSYS", "VBAT", "VBAT_PACK", "3V8_LTE", "RF_3V3", "DISP_3V3", "CAM_3V3", "SD_3V3",
         "MIC_3V3", "FP_3V3", "1V8_LTE", "TORCH_LED", "SPK_P", "SPK_N", "LRA_P", "LRA_N", "SW1_LTE", "SW2_LTE",
         "L1_3V3", "L2_3V3"]
PLANES = {"GND": pcbnew.In1_Cu, "3V3": pcbnew.In4_Cu}
RF_NETS = ["WIFI_RF", "WIFI_ANT", "LTE_RF", "LTE_ANT", "GNSS_ANT", "GNSS_SAW_IN", "GNSS_RF_IN", "ANT_SUBG_FEED",
           "RF_ANT_SUBG", "RF_SUBGHZ", "CC_RF*", "LORA_RF*", "SUBG_*"]
USB_NETS = ["USB_DP", "USB_DN", "USB_JTAG_DP", "USB_JTAG_DN", "USB_HS_DP", "USB_HS_DN"]
CSI_NETS = ["CSI_*"]
# antenna feeds drawn here (not by Freerouting): straight pad-to-pad chains, RF_W (50 ohm on F.Cu, JLC06101H-3313), locked
CHAINS = [("WIFI_RF", [("U1", "2"), ("C5", "1"), ("R5", "1")]), ("WIFI_ANT", [("R5", "2"), ("C6", "1"), ("J6", "1")]),
          ("LTE_RF", [("U2", "60"), ("C9", "1"), ("R6", "1")]), ("LTE_ANT", [("R6", "2"), ("C10", "1"), ("J5", "1")])]

def critical(b):
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    n = 0
    for net, hops in CHAINS:
        pts = []
        for ref, pad in hops:
            p = [q for q in fp[ref].Pads() if q.GetNumber() == pad][0]
            assert p.GetNetname() == net, (ref, pad, p.GetNetname(), net)
            pts.append(p.GetPosition())
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(c); t.SetWidth(FromMM(RF_W)); t.SetLayer(pcbnew.F_Cu)
            t.SetNet(b.FindNet(net)); t.SetLocked(True); b.Add(t); n += 1
    print(f"antenna feeds: {n} locked 50 ohm segments")
RF_W = 0.14                    # 50 ohm on F.Cu, JLC06101H-3313: 0.135 coplanar at 0.15 gap .. 0.151 microstrip
VIA_D, VIA_DR = 0.4, 0.2       # router vias: 0.1 ring, and 0.1 copper gap = 0.2 hole-to-copper (safe side of JLC's numbers)
VIP_D, VIP_DR = 0.35, 0.15     # via-in-pad (JLC POFV, filled + capped): 0.1 ring, 0.175 + 0.1 - 0.075 = 0.2 hole-to-copper

def rules(b):
    ds = b.GetDesignSettings()
    ds.m_MinClearance = FromMM(0.1); ds.m_TrackMinWidth = FromMM(0.1); ds.m_ViasMinAnnularWidth = FromMM(0.1)
    ds.m_ViasMinSize = FromMM(0.25); ds.m_MinThroughDrill = FromMM(0.15); ds.m_HoleClearance = FromMM(0.2)
    ns = ds.m_NetSettings
    d = ns.GetDefaultNetclass()
    d.SetClearance(FromMM(0.105)); d.SetTrackWidth(FromMM(0.1))   # 0.105: no 0.0993 rounding hits; d.SetViaDiameter(FromMM(VIA_D)); d.SetViaDrill(FromMM(VIA_DR))
    pw = pcbnew.NETCLASS("Power")
    pw.SetClearance(FromMM(0.105)); pw.SetTrackWidth(FromMM(0.2)); pw.SetViaDiameter(FromMM(0.45)); pw.SetViaDrill(FromMM(0.25))
    ns.SetNetclass("Power", pw)
    for n in POWER: ns.SetNetclassPatternAssignment(n, "Power")
    # controlled impedance, JLC06101H-3313 (6 layers, 1.0 mm; stackup.py), JLC's own impedance calculator 2026-11-14,
    # outer layers (F.Cu over In1, B.Cu over In4, coated microstrip): 50 ohm 0.151, or 0.135 coplanar at 0.15 gap: 0.14
    # with 0.15 clearance (0.20 breaks the own-pad gap of the 0201 pi-match parts); USB 90 ohm 0.123 / 0.127 gap; CSI 100 ohm 0.104 / 0.15 gap. Inner In2/In3 (stripline
    # between In1 and In4) need wider lines: 50 ohm 0.284, 90 ohm 0.178/0.127, 100 ohm 0.128/0.127 (Quilter sizes per layer
    # from the stackup in the file; these classes are the outer-layer values).
    for name, w, c, pats in (("RF50", RF_W, 0.15, RF_NETS), ("USB90", 0.125, 0.127, USB_NETS), ("CSI100", 0.105, 0.15, CSI_NETS)):
        nc = pcbnew.NETCLASS(name); nc.SetClearance(FromMM(c)); nc.SetTrackWidth(FromMM(w))
        nc.SetViaDiameter(FromMM(0.4)); nc.SetViaDrill(FromMM(0.2))
        if name != "RF50": nc.SetDiffPairWidth(FromMM(w)); nc.SetDiffPairGap(FromMM(c))
        ns.SetNetclass(name, nc)
        for n in pats: ns.SetNetclassPatternAssignment(n, name)
    ns.RecomputeEffectiveNetclasses(); b.SynchronizeNetsAndNetClasses(True)

def pour(b, layer, netname, clearance=0.2):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(b.FindNet(netname))
    z.SetLocalClearance(FromMM(clearance)); z.SetMinThickness(FromMM(0.12))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(FromMM(0.2)); z.SetThermalReliefSpokeWidth(FromMM(0.25))
    bb = b.GetBoardEdgesBoundingBox(); ol = z.Outline(); ol.NewOutline()
    for x, y in [(bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())]:
        ol.Append(x, y)
    b.Add(z); return z

def vip(b, netname):
    """Via-in-pad for every plane-net SMD pad wide enough to hold one (filled + capped, JLC POFV): no fan-out tracks,
    nothing that blocks the router. Exposed pads get a via grid at 0.8 mm pitch. Returns pads that got nothing."""
    net = b.FindNet(netname); vias = [(t.GetPosition(), t.GetWidth(pcbnew.F_Cu)) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    # a via goes through every layer: keep it clear of rule areas that forbid vias OR tracks (Freerouting treats both as
    # obstacles for a via) and of every other-net pad on BOTH sides, by the 0.1 mm board clearance + 0.02 margin
    keep = [z for z in b.Zones() if z.GetIsRuleArea()]
    keep += [z for f in b.GetFootprints() for z in f.Zones() if z.GetIsRuleArea()]
    CELL = FromMM(2.0); buckets = {}
    for q in b.GetPads():
        if q.GetNetname() == netname: continue
        bb = q.GetBoundingBox(); m = FromMM(0.6)      # inflate: a via near a cell edge must still see this pad
        for i in range((bb.GetLeft() - m) // CELL, (bb.GetRight() + m) // CELL + 1):
            for j in range((bb.GetTop() - m) // CELL, (bb.GetBottom() + m) // CELL + 1):
                buckets.setdefault((i, j), []).append(q)
    def clear_of_pads(pt, rad):
        for q in buckets.get((pt.x // CELL, pt.y // CELL), []):
            for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                if q.IsOnLayer(lay) and q.GetEffectiveShape(lay).Collide(pt, rad + FromMM(0.16)): return False
            if q.HasHole() and (q.GetPosition() - pt).EuclideanNorm() < q.GetDrillSize().x / 2 + rad + FromMM(0.25): return False
        return True
    ufl = [f.GetPosition() for f in b.GetFootprints() if f.GetReference() in ("J5", "J6")]
    def add(pt, d, dr):
        if any((u - pt).EuclideanNorm() < FromMM(2.6) for u in ufl): return False   # U.FL keep-out goes through the board
        for (v, w) in vias:
            if (v - pt).EuclideanNorm() < (w + FromMM(d)) / 2 + FromMM(0.15): return False
        if any(z.Outline().Contains(pt) for z in keep): return False
        if not clear_of_pads(pt, FromMM(d / 2)): return False
        via = pcbnew.PCB_VIA(b); via.SetPosition(pt); via.SetWidth(FromMM(d)); via.SetDrill(FromMM(dr))
        via.SetNet(net); via.SetLocked(True); b.Add(via); vias.append((pt, FromMM(d))); return True
    n = 0; left = []
    for p in b.GetPads():
        if p.GetNetname() != netname or p.HasHole() or p.GetParentFootprint().GetReference().startswith(("J", "AE")): continue   # connectors: pour or offset via, never in-pad
        layer = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        sz = p.GetSize(layer); w, h = pcbnew.ToMM(min(sz.x, sz.y)), pcbnew.ToMM(max(sz.x, sz.y)); c = p.GetPosition()
        if w >= 1.0:
            nx, ny = max(1, int((pcbnew.ToMM(sz.x) - 0.2) / 0.8)), max(1, int((pcbnew.ToMM(sz.y) - 0.2) / 0.8))
            ok = False
            for i in range(nx):
                for j in range(ny):
                    ox = FromMM((i - (nx - 1) / 2) * 0.8); oy = FromMM((j - (ny - 1) / 2) * 0.8)
                    if p.GetOrientation().AsDegrees() % 180: ox, oy = oy, ox
                    ok |= add(pcbnew.VECTOR2I(c.x + ox, c.y + oy), VIP_D, VIP_DR)
            n += ok
            if not ok: left.append(p)
        elif w >= VIP_D and add(c, VIP_D, VIP_DR): n += 1
        else: left.append(p)
    print(f"{netname} via-in-pad: {n} pads, {len(left)} left for an offset via / the router")
    return left

def fanout(b, netname, only_missing=False, clr=0.16, width=0.2):
    """Give every SMD pad of netname (both sides) a locked via next to it (or in the middle of an exposed pad)."""
    net = b.FindNet(netname); r = FromMM(VIA_D / 2)
    others = [p for p in b.GetPads() if p.GetNetname() != netname]
    copper = [t for t in b.GetTracks() if t.GetNetname() != netname] if only_missing else []
    mine = [t for t in b.GetTracks() if t.GetNetname() == netname] if only_missing else []
    keep = [z for z in b.Zones() if z.GetIsRuleArea()]
    keep += [z for f in b.GetFootprints() for z in f.Zones() if z.GetIsRuleArea()]
    edge = b.GetBoardEdgesBoundingBox(); em = FromMM(0.5) + r + FromMM(0.05)   # 0.5 mm edge rule to via copper
    vias = [t.GetPosition() for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    ufl = [f.GetPosition() for f in b.GetFootprints() if f.GetReference() in ("J5", "J6")]
    def ok_point(pt, rad, layer):
        if any((u - pt).EuclideanNorm() < FromMM(2.6) for u in ufl): return False
        if not (edge.GetLeft() + em < pt.x < edge.GetRight() - em and edge.GetTop() + em < pt.y < edge.GetBottom() - em): return False
        for p in others:
            if p.GetEffectiveShape(pcbnew.F_Cu).Collide(pt, rad + FromMM(clr)) or p.GetEffectiveShape(pcbnew.B_Cu).Collide(pt, rad + FromMM(clr)):
                return False
            if p.HasHole() and (p.GetPosition() - pt).EuclideanNorm() < p.GetDrillSize().x / 2 + rad + FromMM(0.25): return False
        for v in vias:
            if (v - pt).EuclideanNorm() < 2 * r + FromMM(clr): return False
        for t in copper:
            if t.GetEffectiveShape(layer).Collide(pt, rad + FromMM(clr)): return False
        for z in keep:
            if z.Outline().Contains(pt): return False
        return True
    def ok_track(a, c, layer):
        n = max(2, int((c - a).EuclideanNorm() / FromMM(0.05)))
        return all(ok_point(pcbnew.VECTOR2I(int(a.x + (c.x - a.x) * i / n), int(a.y + (c.y - a.y) * i / n)), FromMM(width / 2), layer)
                   for i in range(1, n + 1))
    placed = missed = 0
    for p in b.GetPads():
        if p.GetNetname() != netname or p.HasHole(): continue
        if p.GetParentFootprint().GetReference() in ("J5", "J6"): continue   # U.FL: GND tabs join the F.Cu pour (keep-out under the plug)
        layer = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        if only_missing and any(t.GetLayer() == layer and (p.HitTest(t.GetStart()) or p.HitTest(t.GetEnd())) or
                                (t.Type() == pcbnew.PCB_VIA_T and p.HitTest(t.GetPosition())) for t in mine): continue
        c = p.GetPosition(); sz = p.GetSize(layer); fc = p.GetParentFootprint().GetPosition()
        ref = p.GetParentFootprint().GetReference()
        if min(sz.x, sz.y) >= FromMM(1.0) and ref[0] == "U":
            cands = [c]
        else:
            base = math.atan2(c.y - fc.y, c.x - fc.x) if c != fc else 0.0
            cands = []
            for dist in (0.25, 0.5, 0.8, 1.2):
                for k in (0, 1, -1, 2, -2, 3, -3, 4):
                    a = base + k * math.pi / 4
                    reach = max(sz.x, sz.y) / 2 + FromMM(dist) + r
                    cands.append(pcbnew.VECTOR2I(int(c.x + reach * math.cos(a)), int(c.y + reach * math.sin(a))))
        for v in cands:
            if ok_point(v, r, layer) and (v == c or ok_track(c, v, layer)):
                via = pcbnew.PCB_VIA(b); via.SetPosition(v); via.SetWidth(FromMM(VIA_D)); via.SetDrill(FromMM(VIA_DR))
                via.SetNet(net); via.SetLocked(True); b.Add(via); vias.append(v)
                if v != c:
                    t = pcbnew.PCB_TRACK(b); t.SetStart(c); t.SetEnd(v); t.SetWidth(FromMM(width))
                    t.SetLayer(layer); t.SetNet(net); t.SetLocked(True); b.Add(t)
                placed += 1; break
        else:
            missed += 1
    print(f"{netname} fan-out: {placed} vias, {missed} pads left to the router")

if __name__ == "__main__":
    if sys.argv[1] == "export":
        b = pcbnew.LoadBoard(SRC)
        b.SetLayerType(pcbnew.In4_Cu, pcbnew.LT_POWER)
        rules(b)
        critical(b)
        for n, lay in PLANES.items(): pour(b, lay, n, clearance=0.25)
        for n in PLANES: vip(b, n)
        for n in PLANES: fanout(b, n, only_missing=True)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(SRC); print("dsn:", pcbnew.ExportSpecctraDSN(b, DSN))
    else:
        b = pcbnew.LoadBoard(SRC)
        print("ses:", pcbnew.ImportSpecctraSES(b, SES))
        for n in PLANES: fanout(b, n, only_missing=True)
        dangling = 0
        conn = b.GetConnectivity()
        for t in list(b.GetTracks()):     # router vias that ended up touching nothing on any layer
            if t.Type() == pcbnew.PCB_VIA_T and not t.IsLocked() and len(conn.GetConnectedItems(t)) == 0:
                b.Remove(t); dangling += 1
        print("dangling vias removed:", dangling)
        thin = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetWidth() < FromMM(0.1)]
        for t in thin: t.SetWidth(FromMM(0.1))
        for lay in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu): pour(b, lay, "GND")
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(OUT); print("tracks+vias:", len(b.GetTracks()))
        import shutil; shutil.copy(SRC.replace(".kicad_pcb", ".kicad_pro"), OUT.replace(".kicad_pcb", ".kicad_pro"))
