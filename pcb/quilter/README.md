# Quilter upload (made by pcb/quilter_prep.py, 2026-11-13)

Upload the **three files** of one folder (no zip): `phone.kicad_pro`, `phone.kicad_sch`, `phone.kicad_pcb`.

| Folder | What Quilter does |
|---|---|
| `B-place-and-route/` (try first) | Places 368 parts itself and routes. 71 parts stay where the case needs them (antennas, keys, connectors, module, modem, Talk ring, antenna feeds, test pads under the battery). Keep-outs stop parts landing under the battery, the fingerprint button, the camera head and the antenna band. |
| `A-route-only/` (backup) | Every part stays where make_board.py put it; Quilter only routes. Same parts, so it can be a second job in the same project. |

Both pass KiCad schematic parity (0 issues). Left-over DRC items are inside the parts' own footprints (mic sound holes, SIM tray NPTH, SW74 pads at the edge) or the deliberately tight antenna pi-match chains.

## Job settings
1. Stackup: JLCPCB 6-layer (or "from input file": In1 = gnd, In4 = pwr).
2. Differential pairs: CSI_* pairs **100 ohm**; USB_DP/DN, USB_HS_DP/DN, USB_JTAG_DP/DN **85 ohm** (USB wants 90, Quilter offers 85 or 100).
3. Single-ended impedance: add by net class **RF50**, 50 ohm.
4. Power nets: net class **Power** (auto-detected).
5. Preserved pours: none.

Free (Non-Commercial) tier: Quilter's terms allow training on what is uploaded. Projects expire.
Download the best candidate as KiCad and put it in `pcb/quilter/result/`; then run DRC, check_nets.py and jlc_files.py on it.
