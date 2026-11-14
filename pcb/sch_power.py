"""Power subsystem of the concierge phone: USB-C port protection, BQ24074 charger/power path, TPS63802 3V3, TPS63020 3V8_LTE
+ modem bulk, four AP22653A load switches, BQ27441-G1 fuel gauge, LM36011 torch, test pads. Rules: CONTRACT.md.
Refs: U10-U20, C100-C199, R100-R199, L100-L109, D100-D109, F100, J10, TP100-TP109.

Every IC pin table below was read from the manufacturer PDF (URL + page in each part's "note") and compared with the pad
numbers of the footprint actually used (stock .kicad_mod, or the phone.pretty file written by the named gen_*.py).

Power tree:
  J4 VBUS -> VBUS_CONN -> F100 PTC -> VBUS (D100 SMF15A clamp) -> U11 BQ24074 IN
  U11 OUT = VSYS -> U10 TPS63802 -> 3V3 (always on) -> U14..U17 AP22653A -> DISP_3V3 / CAM_3V3 / RF_3V3 / SD_3V3
  J10 battery + = VBAT_PACK -> R122 10 mOhm (BQ27441 high-side sense) -> VBAT = U11 BAT, U12 TPS63020 (-> 3V8_LTE), U18 LM36011
Nets invented here (not in CONTRACT.md): VBUS_CONN (named in the brief), USB_DP / USB_DN (connector-side D+/D-, ESD only),
CC1_P / CC2_P (system side of the CC OVP FETs, only the 5.1k Rd hang there), SBU1_P / SBU2_P (named in the brief),
LS_FAULT (wire-OR fault line), VBAT_PACK (cell + before the gauge sense resistor), TORCH_LED, and local nodes
(TPD_VBIAS, ILIM_CHG, ISET_CHG, FB_3V3, SW1_3V3, SW2_3V3, FB_LTE, SW1_LTE, SW2_LTE, VINA_LTE, ILIM_DISP/CAM/RF/SD,
GAUGE_VDD, GAUGE_BIN). CAM_EN_SW = CAM_EN after the privacy slide switch (switch lives in sch_ui.py)."""

C0402, C0603, C0805, C1210 = ("Capacitor_SMD:C_0402_1005Metric", "Capacitor_SMD:C_0603_1608Metric",
                              "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1210_3225Metric")
R0402, R0805 = "Resistor_SMD:R_0402_1005Metric", "Resistor_SMD:R_0805_2012Metric"
H = {C0402: 0.55, C0603: 0.9, C0805: 1.4, C1210: 2.7, R0402: 0.4, R0805: 0.6}   # max part heights (mm)

# LCSC numbers, all checked in the JLC parts API 2026-11-13 (stock that day in brackets; "basic" = no feeder fee)
CAP = {"100nF": ("C1525", C0402),        # CL05B104KO5NNNC 16 V X7R, basic (31.9M)
       "100nF 50V": ("C14663", C0603),   # CC0603KRX7R9BB104 50 V X7R, basic (35.2M) - TPD6S300A VBIAS needs >= 35 V rating
       "1uF": ("C52923", C0402),         # CL05A105KA5NQNC 25 V X5R, basic (10.4M)
       "0.47uF": ("C92361", C0402),      # CL05A474KA5NNNC 25 V X5R (141k)
       "10uF": ("C19702", C0603),        # CL10A106KP8NNNC 10 V X5R, basic (11.7M)
       "4.7uF 25V": ("C69335", C0603),   # CL10A475KA8NQNC 25 V X5R (695k) - on VBUS (up to 10.5 V operating, 24 V clamp)
       "22uF": ("C59461", C0603),        # CL10A226MQ8NRNC 6.3 V X5R, basic (6.28M) - TI's 0603 22 uF class
       "22uF 0805": ("C45783", C0805),   # CL21A226MAQNNNE 25 V X5R, basic (4.19M)
       "100uF": ("C49066", C1210),       # CL32A107MQVNNNE 6.3 V X5R (161k)
       "33pF": ("C1562", C0402),         # 0402CG330J500NT C0G, basic (1.02M)
       "10pF": ("C32949", C0402),        # CL05C100JB5NNNC C0G, basic (2.06M)
       "10nF": ("C15195", C0402)}        # CL05B103KB5NNNC 50 V X7R, basic (5.53M on 2026-11-14)        # CL05C100JB5NNNC C0G, basic (2.06M)
RES = {"10": "C25077", "1.5k": "C25867", "1.78k": "C113478", "1.1k": "C25860", "887": "C474137", "5.1k": "C25905", "10k": "C25744", "60.4k": "C25911",
       "39k": "C25783", "78.7k": "C67239", "75k": "C25798", "91k": "C4147", "100k": "C25741", "180k": "C25760", "511k": "C64042",
       "1.2M": "C43675", "1.18k": "C270651", "910k": "C25800"}
# 1.18k 0402WGF1181TCE C270651 (29,367) and 910k 0402WGF9103TCE C25800 (38,319), both extended, checked 2026-11-14.
# UNI-ROYAL 0402WGF series 1 %: 10/1.5k/5.1k/10k/100k basic; 1.78k (4.1k), 60.4k (368k), 78.7k (5.7k), 91k (100k),
# 180k (573k), 511k (157k), 1.2M (77.7k) extended. 39k 0402WGF3902TCE C25783 extended "preferred" (582,916 on 2026-11-14;
# 0201 swap 0201WMF3902TEE C473053, 16,869).

def cap(ref, val, a, b="GND", near=None, h=None, note=""):
    lcsc, fp = CAP[val]
    return {"ref": ref, "fp": fp, "value": val, "lcsc": lcsc, "pins": {"1": a, "2": b}, "group": "power",
            "near": near, "side": "F", "h": h or H[fp], "note": note}

def res(ref, val, a, b, near=None, note="", lcsc=None, fp=R0402):
    return {"ref": ref, "fp": fp, "value": val, "lcsc": RES[val] if lcsc is None else lcsc, "pins": {"1": a, "2": b},
            "group": "power", "near": near, "side": "F", "h": H[fp], "note": note}

def tp(ref, net):
    return {"ref": ref, "fp": "TestPoint:TestPoint_Pad_D1.0mm", "value": net, "lcsc": "", "pins": {"1": net},
            "group": "power", "side": "F", "h": 0.05,
            "note": "bare copper test pad, nothing to place (lcsc empty on purpose)"}

DS_TPD = "TI TPD6S300A SLVSEL8 https://www.ti.com/lit/ds/symlink/tpd6s300a.pdf"
DS_CHG = "TI BQ2407x SLUS810N https://www.ti.com/lit/ds/symlink/bq24074.pdf"
DS_B2B = "TI TPS63802 SLVSEU9D https://www.ti.com/lit/ds/symlink/tps63802.pdf"
DS_LTE = "TI TPS63020 SLVS916I https://www.ti.com/lit/ds/symlink/tps63020.pdf"
DS_LS = "Diodes AP22653A DS41186 Rev.5-2 https://diodes.com/datasheet/download/AP22652_AP22653_AP22652A_AP22653A.pdf"
DS_FG = "TI BQ27441-G1 SLUSBH1C https://www.ti.com/lit/ds/symlink/bq27441-g1.pdf"
DS_TOR = "TI LM36011 SNVSAN5A https://www.ti.com/lit/ds/symlink/lm36011.pdf"

PARTS = []

# ---------------------------------------------------------------- USB-C port protection (sits at J4)
PARTS += [
    {"ref": "U19", "fp": "Package_DFN_QFN:Texas_RUK0020B_WQFN-20-1EP_3x3mm_P0.4mm_EP1.7x1.7mm",
     "value": "TPD6S300ARUKR", "lcsc": "C2876380",   # 332 in stock 2026-11-13 (thin: buy the board quantity up front)
     "pins": {"1": "SBU1", "2": "SBU2", "3": "TPD_VBIAS", "4": "USB_CC1", "5": "USB_CC2",
              "6": "USB_CC2", "7": "USB_CC1",            # RPD_G2/G1 shorted to C_CC2/C_CC1 = dead-battery Rd enabled
              "8": "GND", "9": "LS_FAULT", "10": "3V3", "11": "CC2_P", "12": "CC1_P", "13": "GND",
              "14": "SBU2_P", "15": "SBU1_P", "16": "GND", "17": "GND", "18": "GND",
              "19": "USB_DN", "20": "USB_DP", "21": "GND"},
     "group": "power", "near": "J4", "side": "F", "h": 0.8,
     "note": DS_TPD + " pin table p.4-5 (RUK0020B, matches KiCad pads 1-20 + EP 21), rec. op. p.6, dead battery 8.3.4 p.18. "
             "C_SBUx/C_CCx connector side, SBUx/CCx system side; pins 16/17 N.C. 'Connect to Ground'; D1/D2 = USB2.0 ESD only "
             "(flow-through, D+ and D- of J4). Dead-battery: RPD_Gx tied to C_CCx so the source sees Rd while 3V3 is down; "
             "once VPWR (3V3) is up the FETs close and R100/R101 take over before the internal Rd is removed (TPD6S300A, not -non-A). "
             "FLT open drain (1.7-300k pull-up) joins LS_FAULT. VPWR 2.7-4.5 V, 0.3-1 uF. SBU operating max 4.3 V."},
    cap("C100", "100nF 50V", "TPD_VBIAS", near="U19", note=DS_TPD + " p.4/p.7: VBIAS 0.1 uF, >= 35 V rated (50 V used)"),
    cap("C101", "1uF", "3V3", near="U19", note=DS_TPD + " p.7: VPWR cap 0.3-1 uF effective (1 uF 25 V at 3.3 V ~0.7 uF)"),
    # R100/R101 (5.1k Rd) removed 2026-11-14: U20 TUSB320LA presents Rd itself on CC1_P/CC2_P (RCC_D 4.6-5.6k, and
    # RCC_DB 4.1-6.1k in dead-battery with VDD off, TUSB320 SLLSEN9F 6.5 p.6 + Table 7-4 p.13).
    res("R102", "10k", "LS_FAULT", "3V3", note="single pull-up for the wire-OR LS_FAULT line (U14-U17 FAULT + U19 FLT)"),
    {"ref": "F100", "fp": "Fuse:Fuse_1206_3216Metric", "value": "1206L200/24NR 2A 24V", "lcsc": "C42396578",  # 51,372 on 2026-11-14
     "pins": {"1": "VBUS_CONN", "2": "VBUS"}, "group": "power", "near": "J4", "side": "F", "h": 1.6,
     "note": "LUTE 1206L series PTC, datasheet Revision 2020 (LCSC C42396578 PDF): p.4 1206L200/24NR = 2.00 A hold / 3.50 A trip, "
             "24 V max, 40 A max fault, R1max 0.080 ohm (Rmin 0.015); p.7 body 3.0-3.6 x 1.5-1.9, thickness 0.7-1.6 mm (h = 1.6); "
             "p.4 recommended land 1.00 x 1.80 pads, 1.80 gap: the stock Fuse_1206_3216Metric (1.25 x 1.75 at +-1.4) covers it, "
             "same land as the old 1206L150/24NR. Hold must cover the charger input limit R103 1.1k = 1.36/1.46/1.56 A: p.8 derating "
             "gives 1206L200 hold 1.74 A at 40 C, 1.58 A at 50 C (1206L150 was only 1.17 A at 50 C). Changed 2026-11-14 from "
             "1206L150/24NR C20627120 (1.5 A hold) after the charger limit was raised."},
    {"ref": "D100", "fp": "Diode_SMD:D_SOD-123F", "value": "SMF15A", "lcsc": "C123802",   # MDD 91,464; Littelfuse C151294 10,460
     "pins": {"1": "VBUS", "2": "GND"}, "group": "power", "near": "F100", "side": "F", "h": 1.1,
     "note": "VBUS TVS: VRWM 15 V, VBR 16.7-18.5 V, VC 24.4 V @ 8.2 A < BQ24074 IN abs max 28 V (SLUS810N p.9). "
             "KiCad pad 1 = cathode = VBUS. A 5 V TVS is deliberately NOT used (support-parts.md B)."},
]

# ---------------------------------------------------------------- charger / power path
PARTS += [
    {"ref": "U11", "fp": "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm", "value": "BQ24074RGTR",
     "lcsc": "C54313",   # 4,424
     "pins": {"1": "BAT_NTC", "2": "VBAT", "3": "VBAT", "4": "GND", "5": "CHG_EN2", "6": "CHG_EN1", "7": "PGOOD_N", "8": "GND",
              "9": "CHG_N", "10": "VSYS", "11": "VSYS", "12": "ILIM_CHG", "13": "VBUS", "16": "ISET_CHG", "17": "GND"},
     "nc": {"14": "TMR open = default pre/fast-charge safety timers (Table 7-1 p.9)",
            "15": "ITERM open = default 10 % termination (bq24074 only, Table 7-1 p.8)"},
     "group": "power", "near": "F100", "side": "F", "h": 1.0,
     "note": DS_CHG + " Figure 7-2 (RGT0016B top view) + Table 7-1 p.8-9; EP 1.68 x 1.68 (RGT land, p.53) = KiCad pad 17. "
             "CE (4) = GND: charging always enabled. EN2 (5) / EN1 (6) set by the USB-C source's advertised current "
             "(fixed 2026-11-14, VIN-DPM is only active in USB100/USB500, p.12 + 9.3.4.1.1 p.22): U20 TUSB320LA OUT1 low = "
             "source offers 1.5 A or 3 A -> EN1 = 0, EN2 = 1 (Q100 inverts) = ILIM mode, R103 1.18k = 1.27/1.36/1.46 A. "
             "Default USB / USB-A cable -> EN1 = 1, EN2 = 0 = USB500 with VIN-DPM. 3V3 down (dead battery) -> both 0 = USB100. "
             "Every change passes through USB100, never standby (EN2 rises via R127/C132 ~1 ms, falls through Q100). "
             "ISET 887 R -> ~1.0 A charge (R103/R104 notes). "
             "TS (1) = BAT_NTC from the pack 10k NTC (103AT class): 0-50 C window, 75 uA source, cold 2.1 V / hot 0.3 V (p.9, "
             "9.3.6 p.30). BQ24074 VOVP 10.5 V, IN abs max 28 V. OUT regulates to 4.4 V (Device Comparison p.6)."},
    cap("C102", "4.7uF 25V", "VBUS", near="U11", note=DS_CHG + " Table 7-1 p.8: IN bypass 1-10 uF"),
    cap("C103", "10uF", "VSYS", near="U11", note=DS_CHG + " Table 7-1 p.8: OUT bypass 4.7-47 uF"),
    cap("C104", "10uF", "VBAT", near="U11", note=DS_CHG + " Table 7-1 p.8: BAT bypass 4.7-47 uF"),
    dict(keep0402=True, **res("R103", "1.18k", "ILIM_CHG", "GND", near="U11", note=DS_CHG + " eq.1 p.21 / KILIM 1500-1720 A-ohm p.12: 1.27 / 1.36 / 1.46 A input limit (1.1-8 k range), max stays under a 1.5 A source. Only used when U20 sees a 1.5 A / 3 A source (U11 note); 1 A charging of the 2500 mAh cell")),
    dict(keep0402=True, **res("R104", "887", "ISET_CHG", "GND", near="U11", note=DS_CHG + " eq.2 p.25 / KISET 797-975 A-ohm p.12: 0.90 / 1.00 / 1.10 A fast charge (590-8.9k range) = 0.4C for the 2500 mAh cell, full in ~3 h. Raised 2026-11-14 from 500 mA; thermal regulation (125 C) trims it if the charger gets hot")),
    res("R105", "10k", "CHG_N", "3V3", note="CHG open drain pull-up (1k-100k allowed, Table 7-1 p.8) -> U51 P0"),
    res("R106", "10k", "PGOOD_N", "3V3", note="PGOOD open drain pull-up (1k-100k allowed, Table 7-1 p.8) -> U51 P1"),
    # U20: USB-C current detect -> charger mode (2026-11-14 review fix, no firmware, no GPIO). TI TUSB320 SLLSEN9F (pin
    # functions Table 5-1 p.4 = TUSB320LA datasheet p.3, OUT1/OUT2 Table 7-3 p.13): OUT1 L = Medium 1.5 A or High 3 A attached.
    {"ref": "U20", "fp": "Package_DFN_QFN:Texas_X2QFN-12_1.6x1.6mm_P0.4mm", "value": "TUSB320LAIRWBR", "lcsc": "C132554",  # 1,378
     "pins": {"1": "CC1_P", "2": "CC2_P", "3": "GND", "4": "VBUS_DET", "7": "CHG_EN1", "10": "GND", "11": "GND", "12": "3V3"},
     "nc": {"5": "ADDR open = GPIO mode, I2C off (Table 5-1)", "6": "OUT3 audio-accessory flag, unused",
            "8": "OUT2: Medium vs High not needed (OUT1 covers both)", "9": "ID: DFP-only output, unused in UFP"},
     "group": "power", "near": "U19", "side": "F", "h": 0.4,
     "note": "PORT (3) = GND: UFP/sink only. EN_N (11) = GND: always enabled. VDD 3V3 (2.7-5 V). CC1/CC2 on the protected side "
             "of U19 (replaces R100/R101 Rd). VBUS_DET through R125 (900k class, abs max 4 V on the pin). OUT1 open drain -> "
             "CHG_EN1 with R126 pull-up. Back-drive note (Table 5-1 fn 1): OUT1 pulled to the same 3V3 as VDD."},
    cap("C131", "100nF", "3V3", near="U20", note="TUSB320 VDD bypass"),
    res("R125", "910k", "VBUS", "VBUS_DET", near="U20", note="TUSB320 VBUS_DET series R (datasheet: 900 kOhm, Figure 7-2 p.10); 910k 1 %: 20 V on VBUS -> pin stays well under 4 V abs max"),
    res("R126", "100k", "CHG_EN1", "3V3", near="U20", note="OUT1 open-drain pull-up = BQ24074 EN1 (VIH 1.4 V). 3V3 down -> EN1 low"),
    {"ref": "Q100", "fp": "Package_TO_SOT_SMD:SOT-523", "value": "DMG1012T-7", "lcsc": "C20512",
     "pins": {"1": "CHG_EN1", "2": "GND", "3": "CHG_EN2"}, "group": "power", "near": "U11", "side": "F", "h": 0.8,
     "note": "Inverter EN1 -> EN2. Diodes DS31783 p.1 top view: 1 G, 2 S, 3 D. VGS(th) 0.5-1.0 V < EN logic 1.4 V, so EN2 is "
             "pulled low before EN1 reads high (passes USB100, never standby)."},
    res("R127", "100k", "CHG_EN2", "3V3", near="U11", note="EN2 pull-up (high = ILIM mode when Q100 is off)"),
    cap("C132", "10nF", "CHG_EN2", near="U11", note="with R127: EN2 rises ~1 ms after EN1 falls (USB100 in between, never standby)"),
    res("R107", "10k", "BAT_NTC", "GND", near="U11", lcsc="",
        note="DNP. Fit ONLY for a pack without NTC: Table 7-1 p.9 'connect a 10-kOhm fixed resistor from TS to VSS'. "
             "With the pack NTC on J10 it must stay empty (it would halve the NTC reading)."),
]

# ---------------------------------------------------------------- battery connector (back side)
PARTS += [
    {"ref": "J10", "fp": "Connector_JST:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal",
     "value": "S3B-PH-SM4-TB(LF)(SN)", "lcsc": "C265101",   # JST genuine, 22,363
     "pins": {"1": "VBAT_PACK", "2": "BAT_NTC", "3": "GND"},
     "nc": {"MP": "two mechanical hold-down tabs, not electrical (JST drawing)"},
     "group": "power", "side": "B", "h": 5.5,
     "note": "Battery: 2500 mAh 50 x 60 x 7.3 mm 1S 4.2 V Li-ion pouch with PCM (DESIGN.md fit pass 2026-11-14; replaces the "
             "VARTA 1400 mAh pack). Its NTC must be a 10k 103AT-type thermistor (B ~3435) so the BQ24074 TS window (0-50 C, "
             "SLUS810N 9.3.6) is right; order the pack with 3 bare leads +, NTC, - (a 2-wire pack without NTC needs R107 fitted). "
             "We crimp our own JST PHR-3 housing, so the order is ours: pad 1 = +, pad 2 = NTC, pad 3 = - (check the vendor's "
             "lead colours). "
             "NTC in the middle keeps + and - apart (no crimp-slip short across the cell). KiCad footprint: pads 1/2/3 at "
             "x = -2 / 0 / +2 on the rear row (y = -2.85), plug opening toward +y; seen looking INTO the header opening with the "
             "PCB below, pad 1 (+) is on the RIGHT, pad 3 (-) on the LEFT (mirror of the plug face, same trap as "
             "support-parts.md 8.2). Silkscreen '+' at pad 1 and 'T' at pad 2; meter the crimped pack before first plug-in "
             "(BQ24074 BAT has no reverse protection). Height 5.5 mm per JLC listing. 2 A per contact."},
]

# ---------------------------------------------------------------- fuel gauge (high-side sense, per datasheet)
PARTS += [
    {"ref": "U13", "fp": "phone:TI_DRZ0012A_VSON-12_2.5x4mm", "value": "BQ27441DRZT-G1A",
     "lcsc": "C2864880",   # 502 in stock (250-reel); the DRZR-G1A reel C473397 had only 65
     "pins": {"1": "I2C_SDA", "2": "I2C_SCL", "3": "GND", "5": "GAUGE_VDD", "6": "VBAT_PACK", "7": "VBAT",
              "8": "VBAT_PACK", "10": "GAUGE_BIN", "12": "FUEL_ALRT", "13": "GND"},
     "nc": {"4": "NC 'may be left floating or tied to VSS' (p.4)", "9": "NC (p.4)", "11": "NC (p.4)"},
     "group": "power", "near": "R122", "side": "F", "h": 1.0,
     "note": DS_FG + " Pin Functions p.4, land p.26 (footprint gen_bq27441.py). I2C 0x55 (no clash with OV5647 at 0x36). "
             "SENSE IS HIGH-SIDE, not in the ground path: p.4 'SRP to PACKP side of the sense resistor, SRN to VSYS side', "
             "simplified schematic p.1. So R122 sits between J10 + (VBAT_PACK) and VBAT. BAT (6) Kelvin to PACKP with 1 uF, VDD "
             "0.47 uF (p.5, 11.1 p.18). BIN: embedded pack -> 10k to VSS (p.4). GPOUT open drain, pull-up 1.62-3.6 V (p.5) -> 10k to "
             "3V3 -> FUEL_ALRT (U51 P5). Thermal pad 13 to GND (p.25 note 3, p.26 vias). LAYOUT: route SRP/SRN/BAT as Kelvin "
             "traces from R122's pads, not from the power copper. G1A = 4.2 V LiCoO2 chem ID 0x0128 (p.3), for the 4.2 V "
             "2500 mAh 50 x 60 x 7.3 mm 1S Li-ion pouch (DESIGN.md fit pass 2026-11-14). Firmware must write Design Capacity = "
             "2500 mAh (plus Design Energy, Terminate Voltage, Taper Rate for that cell) into the gauge's data memory at first "
             "boot; the gauge does not read the pack NTC (that goes to the BQ24074 TS pin)."},
    {"ref": "R122", "fp": R0805, "value": "10mR 1% 0.5W", "lcsc": "C163089",   # TA-I RLM10FTSMR010 alloy, 84,810
     "pins": {"1": "VBAT_PACK", "2": "VBAT"}, "group": "power", "near": "J10", "side": "F", "h": 0.6,
     "note": DS_FG + " p.4: 'external 10 mOhm, 1 % sense resistor in the high-side current path', pre-calibrated. "
             "3 A LTE + torch peak = 90 mW (0.5 W part). Pad 1 = pack side (SRP), pad 2 = system side (SRN)."},
    cap("C128", "1uF", "VBAT_PACK", near="U13", note=DS_FG + " p.4 / 11.1 p.18: >= 1 uF BAT to VSS at the gauge"),
    cap("C129", "0.47uF", "GAUGE_VDD", near="U13", note=DS_FG + " p.4 / p.5 CLDO18: 0.47 uF VDD to VSS"),
    res("R123", "10k", "GAUGE_BIN", "GND", near="U13", note=DS_FG + " p.4: embedded battery -> 10k BIN pull-down"),
    res("R124", "10k", "FUEL_ALRT", "3V3", near="U13", note=DS_FG + " p.4: GPOUT must not float, 10k pull-up recommended"),
]

# ---------------------------------------------------------------- 3V3 main rail
PARTS += [
    {"ref": "U10", "fp": "phone:TI_DLA_VSON-HR-10_2x3mm", "value": "TPS63802DLAR", "lcsc": "C2845237",   # 21,068
     "pins": {"1": "VSYS", "2": "GND", "3": "GND", "4": "FB_3V3", "6": "3V3", "7": "SW2_3V3", "8": "GND",
              "9": "SW1_3V3", "10": "VSYS"},
     "nc": {"5": "PG open drain, 'leave the PG pin unconnected when not used' (p.12)"},
     "group": "power", "near": "U11", "side": "F", "h": 1.0,
     "note": DS_B2B + " Table 7-1 p.4, land p.36 (footprint gen_tps63802.py, pads match 1-10). EN (1) tied to VIN = always on "
             "(must not float, p.4). MODE (2) = GND: power-save mode for standby current. AGND (3) joins GND at the IC "
             "(layout rule: R109 return to pin 3). Divider Table 10-5 p.20: 511k/91k -> 3.308 V (R2 <= 100k). "
             "L 0.47 uH (0.37-0.57 eff., p.5), Cout 22 uF typ (Table 10-1 p.17), 2x fitted for camera + panel transients."},
    {"ref": "L100", "fp": "Inductor_SMD:L_Murata_DFE201610P", "value": "DFE201612E-R47M=P2 0.47uH 5.5A", "lcsc": "C668312",
     "pins": {"1": "SW1_3V3", "2": "SW2_3V3"}, "group": "power", "near": "U10", "side": "F", "h": 1.2,
     "note": DS_B2B + " Table 10-2 p.19 lists Toko/Murata DFE201612E 0.47 uH, Isat 5.5 A, 26 mOhm. 2016 land same as DFE201610P. "
             "13,233 in stock."},
    cap("C105", "10uF", "VSYS", near="U10", note=DS_B2B + " Table 10-4/10-6 p.19-20: 10 uF at VIN"),
    cap("C106", "22uF", "3V3", near="U10", note=DS_B2B + " Table 10-3/10-6: GRM188R60J226 class, 22 uF 0603 6.3 V"),
    cap("C107", "22uF", "3V3", near="U10", note="second 22 uF on 3V3 (support-parts.md 1.2: camera + AMOLED on this rail)"),
    res("R108", "511k", "3V3", "FB_3V3", near="U10", note=DS_B2B + " Table 10-5 p.20 R1 for 3.3 V"),
    res("R109", "91k", "FB_3V3", "GND", near="U10", note=DS_B2B + " Table 10-5 p.20 R2 (<= 100k)"),
]

# ---------------------------------------------------------------- 3V8_LTE rail from VBAT + modem bulk
PARTS += [
    {"ref": "U12", "fp": "Package_DFN_QFN:DFN-14-1EP_3x4mm_P0.5mm_EP1.7x3.3mm", "value": "TPS63020DSJR", "lcsc": "C15483",
     "pins": {"1": "VINA_LTE", "2": "GND", "3": "FB_LTE", "4": "3V8_LTE", "5": "3V8_LTE", "6": "SW2_LTE", "7": "SW2_LTE",
              "8": "SW1_LTE", "9": "SW1_LTE", "10": "VBAT", "11": "VBAT", "12": "LTE_EN", "13": "GND", "15": "GND"},
     "nc": {"14": "PG open drain 'can be left open' (Pin Functions p.4)"},
     "group": "power", "near": "U2", "side": "F", "h": 1.0,
     "note": DS_LTE + " Pin Functions p.4 (pins 1-7 left top->bottom, 8-14 right bottom->top = KiCad pads 1-14, EP = 15 = PGND). "
             "Stock land is the Linear DE DFN (support-parts.md 2.3): EP 0.12 mm wider / 0.45 mm longer than TI's 2.85x1.58, "
             "still 0.25 mm from signal pads. VIN from VBAT (not VSYS) so 1 A modem bursts never pass the BQ24074 path. "
             "VINA from VBAT via R110 10 ohm + C110 100 nF (<= 0.22 uF, 8.2.2.5 p.15). EN (12) = LTE_EN (expander P0_0), "
             "R113 10k pull-down = off at boot (must not float). PS/SYNC (13) = GND: power-save on, lowest standby draw with "
             "the modem registered (~1.6 mA); bursts push it into PWM anyway. Divider 1.2M/180k -> 3.833 V (eq.3, R2 ~180k, "
             "Table 3 p.15). L 1.5 uH (Table 2 p.15), Cout 3x22 uF (Table 4)."},
    {"ref": "L101", "fp": "Inductor_SMD:L_Coilcraft_XxL4020", "value": "XFL4020-152MEC 1.5uH", "lcsc": "C3033018",
     "pins": {"1": "SW1_LTE", "2": "SW2_LTE"}, "group": "power", "near": "U12", "side": "F", "h": 2.1,
     "note": DS_LTE + " Table 2 p.15 (XFL4020-152ME). Isat 5.1 A > 4.5 A max switch limit, 15 mOhm. 19,264 in stock."},
    cap("C108", "10uF", "VBAT", near="U12", note=DS_LTE + " 8.2.2.4 p.15 / Fig.7: 2x10 uF at VIN"),
    cap("C109", "10uF", "VBAT", near="U12", note=DS_LTE + " Fig.7 p.13: C1 = 2x10 uF"),
    cap("C110", "100nF", "VINA_LTE", near="U12", note=DS_LTE + " 8.2.2.5 p.15: 0.1 uF VINA cap, never > 0.22 uF"),
    res("R110", "10", "VBAT", "VINA_LTE", near="U12", note="VINA feed from the battery node, 10 ohm + C110 = RC filter "
        "(datasheet rev I removed the drawn VINA-VIN link; VINA still needs the supply, UVLO sensed there, p.6/p.10)"),
    cap("C111", "22uF 0805", "3V8_LTE", near="U12", note=DS_LTE + " Table 4 p.15: 3x22 uF out; 0805 25 V keeps more C at 3.8 V"),
    cap("C112", "22uF 0805", "3V8_LTE", near="U12"),
    cap("C113", "22uF 0805", "3V8_LTE", near="U12"),
    res("R111", "1.2M", "3V8_LTE", "FB_LTE", near="U12", note=DS_LTE + " eq.3 p.15: R1 = 180k x (3.8/0.5 - 1) -> 1.2M = 3.833 V"),
    res("R112", "180k", "FB_LTE", "GND", near="U12", note=DS_LTE + " 8.2.3 p.15: R2 'in the range of 200 kOhm', Table 3 uses 180k"),
    res("R113", "10k", "LTE_EN", "GND", note="LTE rail off at boot while the expander pin is still an input (brief: 10k)"),
    # modem bulk: physically at EG915U U2 pins 32/33 (VBAT_BB) and 52/53 (VBAT_RF)
    cap("C114", "100uF", "3V8_LTE", near="U2", note="EG915U VBAT bulk, Quectel EG915U QuecOpen HW design (datasheets/) + DESIGN.md LTE"),
    cap("C115", "100uF", "3V8_LTE", near="U2"),
    cap("C116", "100uF", "3V8_LTE", near="U2", note="1210 is 2.5 mm thick (2.7 max): keep clear of the display stack"),
    cap("C117", "100nF", "3V8_LTE", near="U2", note="EG915U VBAT HF decoupling (Quectel: 100 nF + 33 pF + 10 pF per rail)"),
    cap("C118", "33pF", "3V8_LTE", near="U2", note="EG915U VBAT RF decoupling, at VBAT_RF 52/53"),
    cap("C119", "10pF", "3V8_LTE", near="U2", note="EG915U VBAT RF decoupling, at VBAT_RF 52/53"),
    {"ref": "D101", "fp": "Diode_SMD:D_SOD-323", "value": "PTVSHC3D4V5U", "lcsc": "C319211",   # 13,030
     "pins": {"1": "3V8_LTE", "2": "GND"}, "group": "power", "near": "U2", "side": "F", "h": 1.1,
     "note": "Prisemi TVS VRWM 4.5 V, 1.4 kW 8/20 us (specs from the JLC listing, support-parts.md 7a: Prisemi PDF not readable). "
             "Pad 1 = cathode = 3V8_LTE. 3.83 V rail leaves 0.67 V to VRWM."},
]

# ---------------------------------------------------------------- load switches from 3V3 (AP22653A, latch-off, active high)
LS_NOTE = (DS_LS + " Pin Descriptions p.2 (SOT26: 1 IN, 2 GND, 3 EN, 4 FAULT, 5 ILIM, 6 OUT = KiCad SOT-23-6 pads 1-6), "
           "ILIM best-fit eq. p.10 (10k-210k). Latch-off after 6 ms overcurrent until EN toggles (p.11). VIH 1.5 V, UVLO 2.65 V. "
           "FAULT open drain wire-ORed on LS_FAULT (one 10k pull-up R102; no expander pin is free, so it goes to TP106 and "
           "firmware detects a tripped rail by the load not answering, then toggles EN). 145 C thermal shutdown.")
def load_switch(u, rail, en, ilim_net, rlim, rlim_ref, rpd_ref, cin, cout, load, limit):
    return [
        {"ref": u, "fp": "Package_TO_SOT_SMD:SOT-23-6", "value": "AP22653AW6-7", "lcsc": "C1511768",   # 3,922
         "pins": {"1": "3V3", "2": "GND", "3": en, "4": "LS_FAULT", "5": ilim_net, "6": rail},
         "group": "power", "side": "F", "h": 1.45,
         "note": f"{rail} switch ({load}). " + LS_NOTE},
        res(rlim_ref, rlim, ilim_net, "GND", near=u, note=f"RLIM {rlim} 1 %: {limit} (min/typ/max, p.10). Short trace."),
        res(rpd_ref, "100k", en, "GND", near=u, note="EN pull-down: rail off while the expander resets (support-parts.md 4.1)"),
        cap(cin, "100nF", "3V3", near=u, note=DS_LS + " p.2: >= 0.1 uF ceramic IN-GND at the pin"),
        cap(cout, "1uF", rail, near=u, note=DS_LS + " p.2: 0.1 uF + bulk at OUT (load-side caps are in the load's group)"),
    ]
PARTS += load_switch("U14", "DISP_3V3", "DISP_EN", "ILIM_DISP", "60.4k", "R114", "R115", "C120", "C121",
                     "AMOLED panel, ~200 mA peak", "352/401/452 mA")
PARTS += load_switch("U15", "CAM_3V3", "CAM_EN_SW", "ILIM_CAM", "75k", "R116", "R117", "C122", "C123",
                     "OV5647 module ~150 mA; EN = CAM_EN after the privacy slide switch (sch_ui), so the pull-down also holds it "
                     "off when the switch is open", "~278/318/361 mA (75k: 78.7k has no 0201 stock at JLC, 2026-11-13)")
PARTS += load_switch("U16", "RF_3V3", "RF_EN", "ILIM_RF", "39k", "R118", "R119", "C124", "C125",
                     "NFC + 125 kHz + CC1101/SX1262 + IR RX; NFC field alone ~250 mA, DESIGN.md needs >= 500 mA",
                     "564/636/710 mA (best-fit eq. p.10 at 39k; still >= 558 mA min at 39k +1 %). Was 60.4k = 352 mA min, "
                     "too low for NFC + a radio; changed 2026-11-14")
PARTS += load_switch("U17", "SD_3V3", "SD_EN", "ILIM_SD", "75k", "R120", "R121", "C126", "C127",
                     "microSD, ~100-200 mA write peaks", "~278/318/361 mA (75k, see U15)")

# ---------------------------------------------------------------- torch
PARTS += [
    {"ref": "U18", "fp": "phone:TI_YKB0008_DSBGA-8_0.8x1.5mm_P0.35mm", "value": "LM36011YKBR", "lcsc": "C213547",   # 556
     "pins": {"A1": "GND", "A2": "VBAT", "C1": "VBAT", "B2": "GND", "C2": "I2C_SDA", "D2": "I2C_SCL", "D1": "TORCH_LED"},
     "nc": {"B1": "'No Connect' (Pin Functions p.3)"},
     "group": "power", "near": "D102", "side": "F", "h": 0.5,
     "note": DS_TOR + " Pin Functions p.3 (YKB top view A1 top-left), package TI 4223222/A https://www.ti.com/lit/pdf/MXBG377 "
             "(0.35 mm pitch: the stock 0.4 mm DSBGA-8 does NOT fit; footprint gen_lm36011.py). Inductorless high-side current "
             "source from VBAT, I2C 0x64. No HWEN or TORCH pin on this part; STROBE (B2) tied to GND (it has a 300k internal "
             "pull-down, hardware flash not used; torch/flash only by I2C). FIRMWARE LIMIT: the XL-3030 LED is rated 300 mA "
             "continuous / 500 mA pulsed <= 0.1 ms, so torch code <= ~300 mA (max torch 376 mA) and flash mode must never exceed "
             "300 mA (LM36011 flash goes to 1.5 A). 0.35 mm pitch, 0.2 mm pads: check the fab's BGA rules."},
    cap("C130", "10uF", "VBAT", near="U18", note=DS_TOR + " p.3: IN bypass 10 uF or larger"),
    {"ref": "D102", "fp": "phone:LED_XINGLIGHT_XL-3030_3.0x3.0mm", "value": "XL-3030UWC-1W-3V", "lcsc": "C2843891",  # 61,223
     "pins": {"2": "TORCH_LED", "1": "GND"}, "group": "power", "near": "J3", "side": "B", "h": 0.65,
     "note": "XINGLIGHT datasheet (LCSC C2843891) p.7: pad 1 = cathode (-), pad 2 = anode (+, the large 2.2x2.4 pad = heat path; "
             "give TORCH_LED copper area). Grounded cathode as LM36011 wants. VF 3.0-3.4 V @ 300 mA, IF max 300 mA. "
             "SIDE B ON PURPOSE: the torch must shine out of the back beside the camera (DESIGN.md), so it is the one part "
             "besides J10 not on F; U18 may sit on F with a via pair, or move it to B next to D102 if routing prefers."},
]

# ---------------------------------------------------------------- test pads
PARTS += [tp("TP100", "VBUS"), tp("TP101", "VBAT"), tp("TP102", "VSYS"), tp("TP103", "3V3"), tp("TP104", "3V8_LTE"),
          tp("TP105", "GND"), tp("TP106", "LS_FAULT")]

for p in PARTS:                       # drop empty placement hints
    if p.get("near") is None: p.pop("near", None)
