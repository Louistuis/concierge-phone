"""JLCPCB assembly files from a board + the sch_*.py netlists (KiCad's python):
  jlc_files.py phone_routed.kicad_pcb [--gerbers] [--out DIR]
      -> DIR/BOM.csv, DIR/CPL.csv, DIR/not_placed.csv (+ DIR/gerbers/ and DIR/gerbers.zip with --gerbers). DIR = jlc/.
Run on its own this only makes draft files. Only order_check.py decides what may be uploaded: it runs this into
jlc/check/out/ and copies the files into jlc/ when every gate passes.
Parts swapped to 0201 by make_board.py get their LCSC number from the JLC parts search (basic parts first, then the most
stock); picks are cached in jlc/lcsc_0201.json so they can be reviewed and pinned. Parts with lcsc "" (bare pads, wires,
consigned module, hand-fitted parts) and DNP parts go to not_placed.csv instead. Board-only footprints that are not parts
(mounting holes H1-H5: no symbol, no LCSC) are left out of all three files and listed on screen.
CPL rotation: KiCad's angle, bottom parts mirrored as (180 - angle) % 360 (JLC's convention, as in Bouni's
kicad-jlcpcb-tools fabrication.py and KiBot's mirror_bottom), then the package correction from ROT_FIX / ROT_FIX_LCSC
below. Every corrected part is printed, and so is every part whose package has no agreed correction (ROT_CHECK). Check
every polarised part in JLC's placement preview before paying anyway: their library origins differ per part.
--gerbers wipes DIR/gerbers/ and DIR/gerbers.zip first, so the zip only ever holds this board; zones are checked and
refilled by kicad-cli on export."""
import sys, os, csv, json, glob, re, shutil, subprocess, importlib.util, collections, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "jlc"); os.makedirs(CACHE_DIR, exist_ok=True)
args = [a for a in sys.argv[1:]]
OUTD = CACHE_DIR
if "--out" in args:
    i = args.index("--out"); OUTD = os.path.abspath(args[i + 1]); del args[i:i + 2]
os.makedirs(OUTD, exist_ok=True)
pos_args = [a for a in args if not a.startswith("--")]
BOARD = os.path.abspath(pos_args[0]) if pos_args else os.path.join(HERE, "phone_routed.kicad_pcb")
SPEC = {}
for f in sorted(glob.glob(os.path.join(HERE, "sch_*.py"))):
    s = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    for p in m.PARTS: SPEC[p["ref"]] = p
CACHE = os.path.join(CACHE_DIR, "lcsc_0201.json")
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

# Rotation corrections JLC needs on top of KiCad's angle, added after the bottom mirror (same order as Bouni and KiBot).
# Only the packages on THIS board, and only where both public tables agree (sources, 2026-11-14):
#   Bouni/kicad-jlcpcb-tools default = matthewlai/JLCKicadTools jlc_kicad_tools/cpl_rotations_db.csv
#   KiBot kibot/misc.py DEFAULT_ROTATIONS
# First matching pattern wins. Parts on the board: U34/U70/U37-U41 (SOT-363), U35 (SOT-353), U3/U4 (TSSOP-16),
# U12/U60 (DFN), U11 (VQFN-16), U32 (QFN-24), U7 (USON-10), J4 (HRO TYPE-C-31-M-12), J10 (JST PH S3B).
ROT_FIX = [
    (r"^SOT-353", 180),
    (r"^SOT-363", 180),
    (r"^TSSOP-", 270),
    (r"^DFN-", 270),
    (r"^(.*?_|V)?QFN-(16|20|24|28|40)(-|_|$)", 270),
    (r"^USON-10", 270),
    (r"^USB_C_Receptacle_HRO_TYPE-C-31-M-12", 180),
    (r"^JST_PH_S", 180),
]
# Corrections for one LCSC part (wins over ROT_FIX; 0 switches a pattern off for that part). Fill in from JLC's
# placement preview when a part turns up wrong there: {"C1234": 90}.
ROT_FIX_LCSC = {}
# Packages on this board where the two tables disagree or only one has an entry: no correction applied, flagged loudly.
ROT_CHECK = [
    (r"^SOT-23(-|_|$)", "SOT-23 / SOT-23-6: Bouni says -90, KiBot says 180"),
    (r"^QFN-32", "QFN-32: KiBot says 270 (^QFN-), Bouni has none"),
    (r"^MSOP-", "MSOP: KiBot says 270, Bouni has none"),
]

def jlc_search(q):
    """JLC parts search through curl (KiCad's bundled python has no CA bundle)"""
    body = json.dumps({"keyword": q, "currentPage": 1, "pageSize": 25})
    out = subprocess.run(["curl", "-s", "--max-time", "30", "-H", "Content-Type: application/json", "-A", "Mozilla/5.0",
                          "-d", body, "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"],
                         capture_output=True, text=True).stdout
    d = json.loads(out or "{}")
    return (d.get("data") or {}).get("componentPageInfo", {}).get("list") or []

def norm_val(v):
    """'100nF' -> '100nF', '10k' -> '10kΩ', '100R'/'0R'/'0' -> '100Ω'/'0Ω', '4.7' -> '4.7Ω'"""
    v = v.split()[0]
    if v.endswith("R"): v = v[:-1]
    if re.fullmatch(r"[\d.]+[kM]?", v): v += "Ω"
    return v

def pick_0201(kind, value):
    """JLC 0201 part for a value: basic first, then 'preferred' extended (no loading fee), then the most stock.
    Capacitors in pF/1 nF and anything marked C0G must be C0G/NP0; capacitors >= 6.3 V."""
    key = f"{kind}:{value}"
    if key in cache: return cache[key]
    v = norm_val(value)
    want_c0g = kind == "C" and (v.endswith("pF") or v == "1nF" or "C0G" in value)
    def ok(c):
        d = (c.get("describe") or "")
        if c.get("componentSpecificationEn") != "0201" or (c.get("stockCount") or 0) < 2000: return False
        if (kind == "C") != ("apacitor" in (c.get("firstSortName") or "")): return False
        if not re.search(r"(^|\s)" + re.escape(v) + r"(\s|$)", d): return False
        if want_c0g and not ("C0G" in d or "NP0" in d): return False
        if kind == "C":
            m = re.search(r"([\d.]+)V", d)
            if m and float(m.group(1)) < 6.3: return False
        return True
    lst = [c for c in jlc_search(f"{v} 0201") if ok(c)]
    lst.sort(key=lambda c: (c.get("componentLibraryType") != "base", not c.get("preferredComponentFlag"), -(c.get("stockCount") or 0)))
    cache[key] = {"lcsc": lst[0]["componentCode"], "mpn": lst[0].get("componentModelEn"), "desc": lst[0].get("describe"),
                  "stock": lst[0].get("stockCount"), "type": lst[0].get("componentLibraryType"),
                  "preferred": bool(lst[0].get("preferredComponentFlag"))} if lst else {"lcsc": "", "mpn": "NOT FOUND"}
    json.dump(cache, open(CACHE, "w"), indent=1, ensure_ascii=False)
    return cache[key]

def jlc_rotation(f, fpname, lcsc):
    """(rotation for CPL.csv, note or '') : bottom mirrored first, then the package / LCSC correction"""
    rot = f.GetOrientationDegrees()
    if f.IsFlipped(): rot = 180 - rot          # KiCad keeps the top view angle; JLC wants it mirrored for the bottom
    corr, why = None, ""
    if lcsc in ROT_FIX_LCSC: corr, why = ROT_FIX_LCSC[lcsc], f"LCSC {lcsc}"
    else:
        for pat, deg in ROT_FIX:
            if re.search(pat, fpname): corr, why = deg, pat; break
    if corr: rot += corr
    rot = round(rot % 360, 1) % 360
    return rot, (f"{corr:+d} ({why})" if corr else ""), why

b = pcbnew.LoadBoard(BOARD)
bom = collections.OrderedDict(); cpl = []; skipped = []; board_only = []; corrected = []; to_check = collections.defaultdict(list)
for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    ref = f.GetReference(); sp = SPEC.get(ref, {})
    fpname = f.GetFPID().GetLibItemName().wx_str()
    if not sp and f.IsBoardOnly():            # mounting holes and other board features: not parts, nothing to buy or place
        board_only.append(ref); continue
    lcsc = sp.get("lcsc", ""); why = "no LCSC: " + sp.get("note", "")[:80] if sp else "NOT IN sch_*.py"
    if "0201_0603Metric" in fpname and sp.get("fp", "").endswith("0402_1005Metric"):
        lcsc = pick_0201(ref[0], sp["value"])["lcsc"]
        if not lcsc: why = f"NO JLC 0201 PART for {sp['value']} (jlc/lcsc_0201.json); keep it 0402 ({sp.get('lcsc', '')}) or pick one"
    dnp = f.IsDNP() or re.search(r"(^|\s)DNP(\s|$)", sp.get("value", ""))
    if dnp or not lcsc:
        skipped.append((ref, f.GetValue(), fpname, "DNP" if dnp else why)); continue
    k = (sp.get("value", f.GetValue()), fpname, lcsc)
    bom.setdefault(k, []).append(ref)
    pos = f.GetPosition(); side = "bottom" if f.IsFlipped() else "top"
    rot, note, _ = jlc_rotation(f, fpname, lcsc)
    if note: corrected.append(f"{ref} ({fpname}, {side}): {note} -> {rot:g}")
    for pat, why in ROT_CHECK:
        if (lcsc not in ROT_FIX_LCSC) and not note and re.search(pat, fpname): to_check[why].append(ref)
    cpl.append((ref, f"{pcbnew.ToMM(pos.x):.3f}mm", f"{-pcbnew.ToMM(pos.y):.3f}mm", side, f"{rot:.1f}"))
with open(os.path.join(OUTD, "BOM.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for (val, fp, lcsc), refs in bom.items(): w.writerow([val, ",".join(refs), fp, lcsc])
with open(os.path.join(OUTD, "CPL.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]); w.writerows(cpl)
with open(os.path.join(OUTD, "not_placed.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Designator", "Value", "Footprint", "Why"]); w.writerows(skipped)
print(f"BOM lines {len(bom)}, placed parts {len(cpl)} ({sum(1 for c in cpl if c[3] == 'bottom')} bottom), "
      f"not placed {len(skipped)}, board-only (no part) {len(board_only)}")
if board_only: print("board-only footprints left out of BOM/CPL:", " ".join(board_only))
print(f"rotation corrections applied: {len(corrected)}")
for c in corrected: print("  ROT", c)
for why, refs in to_check.items(): print(f"  ROT CHECK (no agreed correction, look at it in JLC's preview): {why}: {' '.join(refs)}")
if "--gerbers" in sys.argv:
    g = os.path.join(OUTD, "gerbers"); z = os.path.join(OUTD, "gerbers.zip")
    shutil.rmtree(g, ignore_errors=True); os.makedirs(g)                 # never mix two boards in one zip
    if os.path.exists(z): os.remove(z)
    cli = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
    layers = "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
    subprocess.run([cli, "pcb", "export", "gerbers", "--check-zones", "-o", g + "/", "-l", layers, "--subtract-soldermask", BOARD],
                   check=True, capture_output=True)
    subprocess.run([cli, "pcb", "export", "drill", "-o", g + "/", "--format", "excellon", "--excellon-separate-th", BOARD],
                   check=True, capture_output=True)
    files = sorted(os.listdir(g))
    subprocess.run(["zip", "-jq", z] + [os.path.join(g, x) for x in files], check=True)
    print(f"gerbers.zip written ({len(files)} files from {os.path.basename(BOARD)})")
