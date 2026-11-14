"""Electrical sanity check of a board file against the sch_*.py netlists (stands in for ERC: the design has no schematic).
Run with KiCad's python:  check_nets.py [phone.kicad_pcb | phone_routed.kicad_pcb]
Flags: a part in the netlists missing from the board, a pad whose net differs from its sch_*.py entry, an electrical pad with
no net that is not listed in that part's 'nc', and nets with only one pad. On a routed board it also counts unrouted
connections (KiCad connectivity). Exit code 1 if anything is flagged."""
import sys, os, glob, collections, importlib.util, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
b = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "phone.kicad_pcb"))
SPEC = {}
for f in sorted(glob.glob(os.path.join(HERE, "sch_*.py"))):
    s = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    for p in m.PARTS: SPEC[p["ref"]] = p
problems = []
# board-only footprints (screw holes H1-H5: no pads with nets, no BOM) are not in any netlist on purpose
onboard = {f.GetReference(): f for f in b.GetFootprints() if not f.IsBoardOnly()}
for ref in sorted(set(SPEC) - set(onboard)): problems.append(f"{ref} is in the netlists but not on the board")
pads_by_net = collections.defaultdict(list)
for ref, f in onboard.items():
    sp = SPEC.get(ref)
    if sp is None: problems.append(f"{ref} on the board but in no sch_*.py"); continue
    for p in f.Pads():
        num, n = p.GetNumber(), p.GetNetname()
        if not num or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH: continue
        want = sp.get("pins", {}).get(num)
        if n: pads_by_net[n].append(f"{ref}.{num}")
        if want and n != want: problems.append(f"{ref}.{num} is on '{n}', netlist says '{want}'")
        if not want and num not in sp.get("nc", {}): problems.append(f"{ref}.{num} has no net and no 'nc' reason")
for n, pads in sorted(pads_by_net.items()):
    if n.startswith("unconnected-"): continue   # KiCad's own name for a schematic no-connect pin
    if len({x.split('.')[0] for x in pads}) < 2: problems.append(f"net {n} only touches {pads}")
conn = b.GetConnectivity(); conn.RecalculateRatsnest() if hasattr(conn, "RecalculateRatsnest") else None
unrouted = conn.GetUnconnectedCount(False) if hasattr(conn, "GetUnconnectedCount") else -1
print(f"{len(onboard)} parts, {len(pads_by_net)} nets, unrouted connections: {unrouted}")
for p in problems: print("PROBLEM:", p)
print("OK" if not problems else f"{len(problems)} problem(s)")
sys.exit(1 if problems else 0)
