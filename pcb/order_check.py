"""ONE command before ordering. Run with KiCad's python on the routed board (e.g. the Quilter candidate):
    order_check.py quilter/result/phone.kicad_pcb [boards=5]
Every gate below must say PASS. All checks run on ONE scratch copy, jlc/check/phone.kicad_pcb (zones refilled and saved
by the DRC run), and the gerbers are made from that same file. The order files are first made as drafts in
jlc/check/out/; they are copied into jlc/ (BOM.csv, CPL.csv, not_placed.csv, stock.csv, gerbers.zip) only when every
gate passes. At the start the old order files are removed from jlc/, so after NOT READY there is nothing in jlc/ to
upload (jlc/ORDER_STATUS.txt says why; the drafts in jlc/check/out/ are NOT for upload).
  1 copper: KiCad DRC, all severities, zones refilled, with schematic parity against the generated schematic in
    quilter/B-place-and-route. The rules are forced to JLC's 6-layer limits = what Quilter was given (RULES below:
    track/space 0.0889 = 3.5 mil, via 0.25/0.15, via hole to copper 0.2, edge 0.3). Fails on: every error plus the
    hole warnings in PROMOTE, unless it is on the reviewed footprint-own list (KNOWN: every item of the violation must
    belong to the listed part, a track or via never matches); every schematic parity item of any severity
    (net_conflict, extra/missing footprint, ...); anything unrouted.
  2 JLC 6-layer limits on every track / via / plated pad (track 0.0889, via drill 0.15, via pad 0.25, via ring 0.05,
    PTH pad ring 0.15; via rings < 0.1 are counted, allowed).
  3 netlist: check_nets.py (board == sch_*.py, every pin on its net). Board-only NPTH holes with no net (mounting holes
    H1-H5) are not in sch_*.py; that one check_nets line is excused for them, nothing else.
  4 files: jlc_files.py --gerbers into jlc/check/out; every BOM designator has a CPL row; not_placed.csv is exactly the
    reviewed NOT_PLACED list (anything new fails); gerbers.zip holds this board only.
  5 stock: stock_check.py on the draft BOM (live JLC stock covers N boards + attrition).
  6 fit: fit_check.py on the routed board's own placement (board + screen + battery + antennas + case, 15.5 mm body).
It ends with the list of parts JLC does not fit (bought separately) and what to pick on JLC's order page."""
import os, sys, json, shutil, subprocess, csv, re, collections, zipfile, pcbnew
from pcbnew import ToMM
HERE = os.path.dirname(os.path.abspath(__file__))
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
KPY = sys.executable
BOARD = os.path.abspath(sys.argv[1]); BOARDS = sys.argv[2] if len(sys.argv) > 2 else "5"
JLC = os.path.join(HERE, "jlc")
ORDER_FILES = ("BOM.csv", "CPL.csv", "not_placed.csv", "stock.csv", "gerbers.zip", "gerbers")

# JLC 6-layer (1 oz) limits, jlcpcb.com/capabilities/pcb-capabilities 2026-11-14: track/space 0.09/0.09 mm (3.5/3.5 mil),
# via hole/diameter 0.15/0.25, via hole to track 0.2, via hole to hole 0.2, routed edge to copper 0.2. Quilter job
# 2026-11-14: 0.089 track/space, via 0.25/0.15, margin 0.3. Forced into the copied .kicad_pro so a re-run of
# quilter_prep.py (which copies pcb/phone.kicad_pro) cannot silently change what the gate checks.
RULES = {"min_track_width": 0.0889, "min_clearance": 0.0889, "min_via_diameter": 0.25, "min_through_hole_diameter": 0.15,
         "min_via_annular_width": 0.05, "min_hole_clearance": 0.2, "min_hole_to_hole": 0.2, "min_copper_edge_clearance": 0.3}
CLASS_CLEARANCE = {"Default": 0.0889, "Power": 0.0889}       # RF50 0.15 and differentialpair 0.16 stay (RF / impedance)
PROMOTE = {"hole_to_hole", "holes_co_located"}   # project warnings that are fab failures here

WIFI_CHAIN = {"U1", "C5", "R5", "C6", "J6"}                  # antenna pi-match chains placed pad-to-pad on purpose
LTE_CHAIN = {"U2", "C9", "R6", "C10", "J5"}

def owner(desc):
    """footprint a DRC item belongs to ('Pad 5 [GND] of U72 on F.Cu', 'NPTH pad of J2', 'Rectangle of U54 on B.Mask',
    'Footprint R5'), None for tracks, vias, zones and board edges"""
    s = re.sub(r"\[[^\]]*\]", "", desc).strip()
    m = re.fullmatch(r"Footprint ([A-Z]+\d+)", s) or re.search(r"\bof ([A-Z]+\d+)\b", s)
    return m.group(1) if m else None

def one_part(allowed=None):
    """every item belongs to the same footprint (and it is in `allowed`)"""
    def ok(items):
        o = {owner(i) for i in items}
        return len(o) == 1 and None not in o and (allowed is None or o <= allowed)
    return ok

def part_vs_edge(allowed):
    """the part's own pads against the board edge, nothing else"""
    def ok(items):
        edge = [i for i in items if owner(i) is None and "Edge.Cuts" in i]
        own = {owner(i) for i in items if i not in edge}
        return bool(edge) and bool(own) and None not in own and own <= allowed
    return ok

def in_one_chain(items):
    o = {owner(i) for i in items}
    return None not in o and (o <= WIFI_CHAIN or o <= LTE_CHAIN)

KNOWN = {   # type -> test on the item descriptions; reviewed 2026-11-13, tightened 2026-11-14
    "hole_clearance": one_part({"U71", "U72"}),      # MEMS mic sound hole (NPTH) next to its own GND ring
    "items_not_allowed": one_part({"J2"}),           # SIM holder NPTH inside its own keep-out
    "copper_edge_clearance": part_vs_edge({"SW74"}), # side slide switch: pads overhang the edge by design
    "courtyards_overlap": in_one_chain,              # antenna pi-match chains placed pad-to-pad on purpose
    "solder_mask_bridge": one_part(),                # pads / mask openings of ONE footprint (fine pitch, own mask shape)
}
# Parts JLC does not place, reviewed 2026-11-14 (51): DNP options, bare test pads, consigned module, hand-fitted parts.
NOT_PLACED = {
    "C5", "C6", "C9", "C10", "C319", "C326", "C334", "C368", "C370", "C371", "C385", "C396", "C397", "L312",   # DNP
    "R13", "R15", "R704", "R705", "R721", "U42",                                                             # DNP
    "J32", "J33", "J34", "TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TP7", "TP8", "TP9", "TP10", "TP11",       # test pads
    "TP12", "TP13", "TP14", "TP15", "TP100", "TP101", "TP102", "TP103", "TP104", "TP105", "TP106",
    "U1",                                # Waveshare ESP32-P4 module: consigned (Waveshare ships it to JLC)
    "LS70", "SW70",                      # speaker spring pads, snap dome
    "J31",                               # Coilcraft 4308RV 125 kHz coil: consigned with U1 (not stocked at JLC)
}

results = []
def gate(name, ok, detail=""): results.append((name, ok, detail)); print(("PASS " if ok else "FAIL ") + name + (": " + detail if detail else ""))

def finish():
    ready = bool(results) and all(x[1] for x in results)
    out = os.path.join(work, "out")
    if ready:
        for f in ORDER_FILES:
            src = os.path.join(out, f)
            if os.path.isdir(src): shutil.copytree(src, os.path.join(JLC, f))
            elif os.path.exists(src): shutil.copy(src, JLC)
    with open(os.path.join(JLC, "ORDER_STATUS.txt"), "w") as fh:
        fh.write(("READY TO ORDER" if ready else "NOT READY: nothing in jlc/ may be uploaded; the drafts in jlc/check/out/ are NOT valid order files")
                 + f"\nboard: {BOARD}\n" + "".join(f"{'PASS' if ok else 'FAIL'} {n}: {d}\n" for n, ok, d in results))
    print("\nRESULT:", "READY TO ORDER (order files copied into jlc/)" if ready else
          "NOT READY (see FAIL lines). No order files in jlc/; the drafts in jlc/check/out/ are not for upload.")
    return ready

# ---- 0 scratch copy; old order files out of jlc/ so nothing stale can be uploaded
work = os.path.join(JLC, "check"); shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
for f in ORDER_FILES + ("ORDER_STATUS.txt",):
    p = os.path.join(JLC, f)
    if os.path.isdir(p): shutil.rmtree(p)
    elif os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(HERE, "quilter", "B-place-and-route", "phone.kicad_sch"), work)
pro = json.load(open(os.path.join(HERE, "quilter", "B-place-and-route", "phone.kicad_pro")))
ds = pro["board"]["design_settings"]; ds["rules"].update(RULES)
for t in PROMOTE: ds["rule_severities"][t] = "error"
for c in pro["net_settings"]["classes"]:
    if c["name"] in CLASS_CLEARANCE: c["clearance"] = CLASS_CLEARANCE[c["name"]]
json.dump(pro, open(os.path.join(work, "phone.kicad_pro"), "w"), indent=2)
CHK = os.path.join(work, "phone.kicad_pcb"); shutil.copy(BOARD, CHK)

# ---- 1 DRC + parity (all severities, zones refilled and saved into CHK)
rep = os.path.join(work, "drc.json")
r = subprocess.run([CLI, "pcb", "drc", "--schematic-parity", "--severity-all", "--refill-zones", "--save-board",
                    "--format", "json", "-o", rep, CHK], capture_output=True, text=True)
if not os.path.exists(rep):
    gate("KiCad DRC ran", False, (r.stdout + r.stderr)[-300:]); finish(); sys.exit(1)
d = json.load(open(rep))
unknown, known, warn = [], 0, collections.Counter()
for v in d["violations"]:
    items = [i["description"] for i in v["items"]]
    if v["severity"] != "error" and v["type"] not in PROMOTE: warn[v["type"]] += 1; continue
    if v["type"] in KNOWN and KNOWN[v["type"]](items): known += 1; continue
    unknown.append(f'{v["type"]}: ' + " | ".join(items))
gate("DRC errors + hole warnings (beyond the reviewed footprint-own list)", not unknown,
     f"{len(unknown)} new" if unknown else f"{known} known only")
for u in unknown[:25]: print("     ", u)
if warn: print("      (other warnings, not gated: " + ", ".join(f"{k} {n}" for k, n in warn.most_common()) + ")")
gate("everything routed", len(d.get("unconnected_items", [])) == 0, f'{len(d.get("unconnected_items", []))} unrouted')
par = d.get("schematic_parity", [])
gate("schematic parity (all severities)", not par, f"{len(par)} mismatches: " + ", ".join(f"{k} {n}" for k, n in
     collections.Counter(v["type"] for v in par).most_common()) if par else "0 mismatches")
for v in par[:15]: print("     ", v["type"] + ": " + " | ".join(i["description"] for i in v["items"]))

# ---- 2 JLC 6-layer fab limits
b = pcbnew.LoadBoard(CHK); fab = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        dr, dia = ToMM(t.GetDrillValue()), ToMM(t.GetWidth(pcbnew.F_Cu))
        if dr < 0.149 or dia < 0.249 or (dia - dr) / 2 < 0.049: fab.append(f"via {dia:.2f}/{dr:.2f} at {ToMM(t.GetPosition().x):.2f},{ToMM(t.GetPosition().y):.2f}")
    elif ToMM(t.GetWidth()) < 0.0885: fab.append(f"track {ToMM(t.GetWidth()):.3f} mm on {t.GetNetname()}")   # JLC 3.5 mil = 0.0889
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH: continue
        ds_, sz = p.GetDrillSize(), p.GetSize(pcbnew.F_Cu)
        ring = min(ToMM(sz.x - ds_.x), ToMM(sz.y - ds_.y)) / 2
        if ring < 0.149: fab.append(f"PTH pad {f.GetReference()}.{p.GetNumber()} ring {ring:.3f} mm (JLC min 0.15)")
# board-only mechanical footprints (mounting holes H1-H5): board-only attribute, NPTH pads only, no net
MECH = {f.GetReference() for f in b.GetFootprints() if f.IsBoardOnly() and len(f.Pads()) and
        all(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and not p.GetNetname() for p in f.Pads())}
nvia = sum(1 for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA))
thin = sum(1 for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA) and (ToMM(t.GetWidth(pcbnew.F_Cu)) - ToMM(t.GetDrillValue())) / 2 < 0.099)
gate("JLC 6-layer limits (track 0.0889, via 0.25/0.15, PTH ring 0.15)", not fab, f"{len(fab)} below" if fab else f"{nvia} vias, {thin} with ring < 0.1 (allowed, tighter yield)")
for x in fab[:15]: print("     ", x)
del b

# ---- 3 netlist
r = subprocess.run([KPY, os.path.join(HERE, "check_nets.py"), CHK], capture_output=True, text=True)
lines = [l for l in r.stdout.splitlines() if l.startswith(("PROBLEM", "OK")) or "parts," in l]
probs = [l for l in lines if l.startswith("PROBLEM")]
mech = [l for l in probs if re.fullmatch(r"PROBLEM: (\S+) on the board but in no sch_\*\.py", l) and l.split()[1] in MECH]
real = [l for l in probs if l not in mech]     # check_nets.py does not know board-only holes; only those are excused
ok = r.returncode == 0 or (r.returncode == 1 and probs and not real)
gate("board == netlists (check_nets)", ok, (lines[0] if lines else r.stderr[-200:]) +
     (f"; board-only holes ignored: {' '.join(sorted(MECH))}" if mech else ""))
for l in real[:15]: print("     ", l)

# ---- 4 order files (drafts in jlc/check/out, from the same refilled file DRC checked)
out = os.path.join(work, "out")
r = subprocess.run([KPY, os.path.join(HERE, "jlc_files.py"), CHK, "--gerbers", "--out", out], capture_output=True, text=True)
gate("BOM / CPL / gerbers drafted", r.returncode == 0, (r.stdout.strip().splitlines() or [r.stderr[-300:]])[0])
for l in r.stdout.splitlines()[1:]: print("     ", l)
if r.returncode == 0:
    bom = {x for row in csv.DictReader(open(os.path.join(out, "BOM.csv"))) for x in row["Designator"].split(",")}
    cpl = {row["Designator"] for row in csv.DictReader(open(os.path.join(out, "CPL.csv")))}
    gate("every BOM part has a placement row", bom == cpl, f"missing {sorted(bom ^ cpl)[:10]}" if bom != cpl else f"{len(cpl)} parts")
    np_ = {row["Designator"]: row["Why"] for row in csv.DictReader(open(os.path.join(out, "not_placed.csv")))}
    new = sorted(set(np_) - NOT_PLACED)
    gate("not placed by JLC = the reviewed list", not new, f"{len(new)} new: " + ", ".join(f"{x} ({np_[x][:40]})" for x in new[:10])
         if new else f"{len(np_)} parts, all reviewed")
    gone = sorted(NOT_PLACED - set(np_))
    if gone: print("      (on the reviewed list but now placed or gone: " + " ".join(gone) + ")")
    with zipfile.ZipFile(os.path.join(out, "gerbers.zip")) as zf: names = zf.namelist()
    stem = os.path.splitext(os.path.basename(CHK))[0]
    gate("gerbers.zip = this board only", bool(names) and all(n.startswith(stem) for n in names), f"{len(names)} files")

    # ---- 5 stock
    r = subprocess.run(["python3", os.path.join(HERE, "stock_check.py"), BOARDS, os.path.join(out, "BOM.csv")], capture_output=True, text=True)
    gate(f"JLC stock for {BOARDS} boards", r.returncode == 0, r.stdout.strip().splitlines()[0] if r.stdout.strip() else r.stderr[-200:])
    for l in r.stdout.splitlines()[1:12]: print("     ", l)

# ---- 6 3D fit (the routed board's real placement inside the case)
bj = os.path.join(work, "board.json")
with open(bj, "w") as fh: subprocess.run([KPY, os.path.join(HERE, "export_view.py"), CHK], stdout=fh, stderr=subprocess.DEVNULL)
r = subprocess.run(["python3", os.path.join(HERE, "fit_check.py"), bj], capture_output=True, text=True)
gate("3D fit in the 54 x 108 x 15.5 mm body (fit_check)", r.returncode == 0, (r.stdout.strip().splitlines() or ["no output"])[-1])
for l in [l for l in r.stdout.splitlines() if l.startswith("CLASH")][:15]: print("     ", l)

ready = finish()
print("""
JLC order page: 6 layers, 1.0 mm, stackup JLC06101H-3313 (impedance control ON; widths in phone.kicad_pro net classes come
  from JLC's own calculator for that stackup, 2026-11-14), ENIG, outer 1 oz / inner 0.5 oz, via-in-pad epoxy filled + capped
  (JLC default on 6 layers). PCBA Standard, both sides, 'Confirm parts placement' ON (check every polarised part in their
  preview, above all the ROT CHECK parts). U1 side reflowed LAST (Waveshare: reflow the module once). Consigned parts
  (Parts Manager > Consign Parts, shipped to JLC before the order): U1 Waveshare ESP32-P4-Module (from Waveshare) and J31
  Coilcraft 4308RV-404XJL (from Coilcraft).
In the box for the owner (plug in / stick on / screw, no soldering): Waveshare UART Fingerprint Sensor (D) + 6-pin MX1.25
  lead, 1.8" AMOLED panel (Waveshare ESP32-S3-Touch-AMOLED-1.8 donor), Arducam OV5647 spy camera (8.5 mm head, 15-pin
  1.0 mm flex), LiPol LP665056 2400 mAh 1S (6.6 x 50 x 56, PCM, 10k NTC, JST-PH 3-pin plug fitted), Same Sky CMS-16093-078S
  speaker, Vybronics VG0832009L LRA (DigiKey), 4 mm metal snap dome (SW70), Molex 1462360111 NFC antenna, 5 M1.4 screws,
  0.2 mm USB-C bracket, 1.75 mm Talk plunger nub, Taoglas FXP40.07.0085A (LTE) + FXP74 (Wi-Fi) flex antennas with U.FL,
  nano-SIM, microSD. Full list: not_placed.csv (jlc/, or jlc/check/out/ when NOT READY).""")
sys.exit(0 if ready else 1)
