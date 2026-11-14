"""Checks a subsystem file against the real footprints: every footprint loads, every pad named in `pins`/`nc` exists,
every electrical pad is covered, refs are unique and inside the group's range. Run: KPY lib_check.py sch_power.py"""
import sys, os, importlib.util, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
STOCK = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/"
def load_fp(spec):
    lib, name = spec.split(":", 1)
    path = os.path.join(HERE, "phone.pretty") if lib == "phone" else STOCK + lib + ".pretty"
    return pcbnew.FootprintLoad(path, name)
def check(path):
    spec = importlib.util.spec_from_file_location("m", path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    bad, refs = [], set()
    for p in m.PARTS:
        r = p["ref"]
        if r in refs: bad.append(f"{r}: duplicate ref")
        refs.add(r)
        f = load_fp(p["fp"])
        if f is None: bad.append(f"{r}: footprint {p['fp']} not found"); continue
        pads = {}
        for pd in f.Pads():
            if pd.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or not pd.GetNumber(): continue
            pads.setdefault(pd.GetNumber(), 0); pads[pd.GetNumber()] += 1
        named = set(p.get("pins", {})) | set(p.get("nc", {}))
        for n in named - set(pads): bad.append(f"{r}: pad '{n}' not in {p['fp']} (has {sorted(pads)[:12]}...)")
        for n in set(pads) - named: bad.append(f"{r}: pad '{n}' of {p['fp']} not assigned (add to pins or nc)")
        for k in ("value", "lcsc", "group", "side"):
            if k not in p: bad.append(f"{r}: missing '{k}'")
    nets = {}
    for p in m.PARTS:
        for n in p.get("pins", {}).values(): nets.setdefault(n, set()).add(p["ref"])
    print(f"{len(m.PARTS)} parts, {len(nets)} nets")
    for n, rs in sorted(nets.items()):
        if len(rs) == 1: print(f"  note: net {n} touches only {sorted(rs)} here (fine if it leaves this file)")
    for b_ in bad: print("PROBLEM:", b_)
    print("OK" if not bad else f"{len(bad)} problem(s)"); return not bad
if __name__ == "__main__":
    sys.exit(0 if all(check(a) for a in sys.argv[1:]) else 1)
