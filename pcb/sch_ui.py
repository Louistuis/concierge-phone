"""UI / audio subsystem of the concierge phone: Talk key (fingerprint module + click), side + volume keys, privacy slide
switch with its hardware gate, two PDM mics, speaker amp, haptics, light ring, microSD. Rules: CONTRACT.md.
Refs: U70-U89, C700-C799, R700-R799, J70-J79, SW70-SW79, D700-D719, LS70, M70.

Every IC pin table below was read from the manufacturer PDF (URL + page in each part's "note") and compared with the pad
numbers of the footprint actually used (stock .kicad_mod, or the phone.pretty file written by the named gen_*.py).
New footprints: gen_xl1010.py (1010 RGB LED), gen_ui_pads.py (speaker spring landing, LRA wire landing).

I2C on this file (7-bit): 0x5A U74 DRV2605L (fixed), 0x2D U75 LP5815 (fixed; LP5817 fallback is also 0x2D).
Neither clashes with CONTRACT.md (0x15 0x22 0x29 0x30 0x36 0x39 0x42 0x43 0x44 0x45 0x46 0x55 0x59 0x5A 0x60 0x64 0x69).
The CONTRACT row "0x68 LED driver" is not used: the ring driver is the LP5815 at 0x2D, so 0x68 stays free.

Rails used: 3V3 (keys, gate inputs, LP5815, DRV2605L, fingerprint switch input), VSYS (MAX98357A, ring LED anodes),
MIC_3V3 (privacy-switched: mics + gate), SD_3V3 (from sch_power U17), FP_3V3 (made here by U76 from 3V3, EN = FP_EN).

Strap check (Espressif ESP32-P4 datasheet pre-release v0.7, p.27 "Priority 3": strapping pins are GPIO34-38 only; p.16
pin 104 GPIO0 has no reset pull and is an LP IO): GPIO0 (TALK_SW) and GPIO1 (SIDE_KEY) are NOT straps, so the 10k pull-up
+ 100 nF on each is safe and does not change the boot mode (BOOT is GPIO35). GPIO0/1 double as XTAL_32K_N/P (p.25):
the Waveshare module does not fit a 32 kHz crystal (pad 88 = GPIO0), so they are plain LP GPIOs = deep-sleep wake OK.
GPIO3/GPIO4 (FP_TX/FP_RX) are listed as pad-JTAG pins (p.27): fine while JTAG stays on USB-Serial-JTAG (eFuse default).

Pulls added here (each decided against sch_power/sch_sense so nothing is doubled):
  TALK_SW, SIDE_KEY, VOL_UP, VOL_DN: 10k up to 3V3 + 100 nF (brief). sch_sense planned PCAL internal pulls for VOL_*;
    with these external ones the firmware should leave the PCAL6524 pulls on VOL_UP/VOL_DN off.
  CAM_EN: 100k down (R714). The gate input must never float: PCAL6524 pins are inputs with pulls off at reset and no
    other file pulls CAM_EN. CAM_EN_SW (gate output) already has 100k down in sch_power (R117), not doubled here.
  MIC_CLK: 100k down at the gate input (R713), P4 GPIO11 floats during reset. MIC_CLK_G: 100k down (R716, brief).
  MIC_DATA: 100k down (R719): both mics tri-state DATA in standby/off, keeps the P4 input defined.
  AMP_SD: no extra pull. MAX98357A SD_MODE has its own 100k (92-108k) pull-down = shutdown while the expander resets.
  FP_TOUCH, PRIV_STATE: U51 PI4IOE5V6408 internal 100k pull-down (on at power-up) as sch_sense planned.
  SD_CD: no external pull, firmware enables the PCAL6524 internal 100k pull-up (sch_sense plan); card in = low.

Nets invented here (not in CONTRACT.md): FP_RST, FP_MOD_RX, FP_MOD_TX, FP_MOD_WAKE, ILIM_FP (fingerprint),
MIC_CLK_B (gate output before the 33 ohm source resistor), MIC_CLK_G (named in the brief), MIC1_DATA / MIC2_DATA (mic
side of the 100 ohm terminations), AMP_SDMODE, AMP_GAIN, SPK_P, SPK_N, DRV_REG, LRA_P, LRA_N, RING_R, RING_G, RING_B,
SD_D1, SD_D2, SD_D3 (pull-up only, 1-bit mode). FP_3V3 and CAM_EN_SW were named in the brief / sch_power.

Placement: Talk key centre = SW70 centre (front, lower half, under the round button). The fingerprint module (Ø19.2
rim, Ø16.5 body) sits on SW70 through a stiff disc; J70 cannot go under the module (its back carries parts and the
socket), so it sits just outside the light ring and the cable runs as a soft service loop.
Ring LEDs D700-D703 on a Ø21 mm circle around SW70 at 45/135/225/315 degrees (see their notes), leaving the 0/90/180/270
axes free for the module socket direction and the carrier ribs. Mics: U71 at the bottom end (main voice mic, next to the
USB-C/speaker grille), U72 at the top end (reference mic for noise cancelling), both bottom-port with a PCB sound hole.
"""

C0402, C0603 = "Capacitor_SMD:C_0402_1005Metric", "Capacitor_SMD:C_0603_1608Metric"
R0402 = "Resistor_SMD:R_0402_1005Metric"
H = {C0402: 0.55, C0603: 0.9, R0402: 0.4}

# LCSC numbers, checked in the JLC parts API 2026-11-13 (stock that day in brackets; "basic" = no feeder fee)
CAP = {"100nF": ("C1525", C0402),    # CL05B104KO5NNNC 16 V X7R, basic (31.97M)
       "1uF": ("C52923", C0402),     # CL05A105KA5NQNC 25 V X5R, basic (10.47M)
       "10uF": ("C19702", C0603)}    # CL10A106KP8NNNC 10 V X5R, basic (11.72M) - VSYS max 4.5 V
RES = {"0": "C17168",                # 0402WGF0000TCE, basic (15.76M)
       "33": "C25105",               # 0402WGF330JTCE, basic (3.49M)
       "100": "C25076",              # 0402WGF1000TCE, basic (10.92M)
       "1k": "C11702",               # 0402WGF1001TCE, basic (31.59M)
       "10k": "C25744",              # 0402WGF1002TCE, basic (21.25M)
       "100k": "C25741"}             # 0402WGF1003TCE, basic (8.51M)

def cap(ref, val, a, near, group, b="GND", side="F", note=""):
    lcsc, fp = CAP[val]
    return {"ref": ref, "fp": fp, "value": val, "lcsc": lcsc, "pins": {"1": a, "2": b}, "group": group,
            "near": near, "side": side, "h": H[fp], "note": note}

def res(ref, val, a, b, near, group, side="F", note="", dnp=False):
    return {"ref": ref, "fp": R0402, "value": val + (" DNP" if dnp else ""), "lcsc": "" if dnp else RES[val],
            "pins": {"1": a, "2": b}, "group": group, "near": near, "side": side, "h": H[R0402],
            "note": ("NOT FITTED (assembly option, lcsc empty on purpose). " if dnp else "") + note}

DS_FP = ("Waveshare UART Fingerprint Sensor (C) User Manual V1.0 "
         "https://files.waveshare.com/upload/4/45/UART_Fingerprint_Sensor_%28C%29_User_Manual_en.pdf")
DS_LS = "Diodes AP22653A DS41186 Rev.5-2 https://diodes.com/datasheet/download/AP22652_AP22653_AP22652A_AP22653A.pdf"
DS_B3U = "Omron B3U datasheet (LCSC C231329 PDF, B3U-1000P p.1-2)"
DS_EVQ = "Panasonic EVQPU side-operated light-touch switch (LCSC C2915192 PDF p.3: EVQPUB02K 2.2 N, 1.65 mm, 100k cycles)"
DS_ALPS = "Alps SSSS8 series SSSS811101 sheet (LCSC C109335 PDF p.1-3: dimensions, land, circuit)"
DS_LVC = "TI SN74LVC2G34 SCES359J https://www.ti.com/lit/ds/symlink/sn74lvc2g34.pdf"
DS_MIC = ("Infineon IM73D122V01 datasheet rev 1.00 2022-08-12 "
          "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2306061210_Infineon-Technologies-IM73D122V01XTMA1_C5563886.pdf")
DS_AMP = "Maxim MAX98357A/B 19-6779 Rev 7 https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf"
DS_DRV = "TI DRV2605L SLOS854D https://www.ti.com/lit/ds/symlink/drv2605l.pdf"
DS_LRA = "LEADER LD0832AA-0099F spec REV.00 (LCSC C2682305 PDF)"
DS_LP = "TI LP5815 SNVSCP2B (Sept 2026) https://www.ti.com/lit/ds/symlink/lp5815.pdf"
DS_LED = "XINGLIGHT XL-B1010RGBT-HF datasheet (LCSC C22464515 PDF p.3-5 ratings, p.8 outline/polarity/land)"
DS_SD = ("Molex 104031-0811 (KiCad footprint descr https://www.molex.com/pdm_docs/sd/1040310811_sd.pdf; Molex summary: "
         "push-pull, 1.42 mm, detect switch 'Open' = normally open)")

PARTS = []

# ================================================================ 1. Talk key: fingerprint module + click
PARTS += [
    {"ref": "J70", "fp": "Connector_Molex:Molex_PicoBlade_53261-0671_1x06-1MP_P1.25mm_Horizontal",
     "value": "Molex 53261-0671", "lcsc": "C17393620",   # PicoBlade 1.25 mm side entry, 22,544 at JLC 2026-11-13
     "pins": {"1": "FP_3V3", "2": "GND", "3": "FP_MOD_RX", "4": "FP_MOD_TX", "5": "FP_RST", "6": "FP_MOD_WAKE"},
     "nc": {"MP": "two mechanical solder tabs (Molex PicoBlade drawing), not electrical"},
     "group": "talk", "near": "SW70", "side": "F", "h": 3.4,
     "note": "Waveshare UART Fingerprint Sensor (D) (same pins/protocol as (C)); NOT at JLC, buy from Waveshare/RobotShop. "
             + "CONNECTOR (checked 2026-11-13 against the (D) wiki + package photo): the (D) has a 6-position 1.25 mm MX1.25 "
             "(PicoBlade-compatible) socket and ships with a 'MX1.25-6PIN to 2.54 Dupont 200 mm' lead, so J70 is a PicoBlade "
             "53261-0671 and the cable is a stock 6P 1.25 mm double-ended lead (buy 'same direction' AND 'reverse', fit the "
             "one whose pin 1 lands on VIN; METER IT before plugging, the module's own pin-1 end is not documented). "
             "(The (C) manual's 8-pos 1.0 mm socket does not apply.) " + DS_FP + " p.4 signal list; "
             "photo order seen from the back with the socket at the bottom, left -> right: WAKE, RST, TX, RX, GND, VIN. "
             "Signals p.4: VIN 3.3 V (p.2: 2.7-3.3 V, <50 mA, sleep <16 uA), RX = module serial input, TX = module output, "
             "RST H = powered/run, L = sleep, WAKE = H when a finger touches while asleep. 19200 8N1. "
             "J70 order is OURS (module back, socket at the bottom, left -> right reads IRQ/WAKE, EN/RST, TX, RX, GND, VIN): "
             "1 VIN, 2 GND, 3 module RX (<- P4 FP_TX), 4 module TX (-> P4 FP_RX), 5 RST, 6 WAKE. Meter the finished cable. "
             "Every signal has 1k in series (R701/R702/R706) so a mis-pinned cable cannot short a P4/expander pin. "
             "SUPPLY: our 3V3 is 3.308 V, 8 mV over the module's stated 3.3 V max (DESIGN.md open point). "
             "Height 2.9 mm (JST SH drawing / LCSC listing). Moving button: use a soft cable with a service loop "
             "(extras.md 1.3), the click travel is ~0.25 mm."},
    {"ref": "U76", "fp": "Package_TO_SOT_SMD:SOT-23-6", "value": "AP22653AW6-7", "lcsc": "C1511768",   # 3,922 (sch_power uses 4)
     "pins": {"1": "3V3", "2": "GND", "3": "FP_EN", "4": "LS_FAULT", "5": "ILIM_FP", "6": "FP_3V3"},
     "group": "talk", "near": "J70", "side": "F", "h": 1.45,
     "note": DS_LS + " Pin Descriptions p.2 (SOT26: 1 IN, 2 GND, 3 EN, 4 FAULT, 5 ILIM, 6 OUT = KiCad SOT-23-6 pads 1-6), "
             "same part and pin map as sch_power U14-U17. FP_EN = U50 P2_7 (active high; sch_sense has its 100k pull-down = "
             "module unpowered at boot). Off: 0.1 uA typ / 1 uA max (p.5) and the output discharge is on while disabled "
             "(p.5 note 9) = clean power-cycle reset of a hung matcher. On: 120 uA IQ (p.5), only while the module is used. "
             "FAULT open drain joins the existing LS_FAULT wire-OR (R102 pull-up in sch_power). UVLO 2.65 V."},
    res("R700", "100k", "ILIM_FP", "GND", "U76", "talk",
        note=DS_LS + " p.10: ILIMIT = 28955/R^1.075 (min), 30321/R^1.055 (typ), 31033/R^1.031 (max), R in kOhm, "
             "10k-210k allowed (p.2) -> 205 / 235 / 269 mA at 100k; module draws < 50 mA (Waveshare p.2)."),
    cap("C700", "100nF", "3V3", "U76", "talk", note=DS_LS + " p.2: >= 0.1 uF IN-GND at the pin"),
    cap("C701", "10uF", "FP_3V3", "J70", "talk", note="module supply bulk at J70 (matcher bursts up to 50 mA, Waveshare p.2)"),
    cap("C702", "100nF", "FP_3V3", "J70", "talk", note="HF decoupling at J70 pin 1"),
    res("R701", "1k", "FP_TX", "FP_MOD_RX", "J70", "talk",
        note="P4 GPIO3 FP_TX -> module RX. 1k limits back-power into the unpowered module (~3 mA worst case): firmware "
             "drives FP_TX low/input before dropping FP_EN. 1k x ~20 pF = 20 ns, nothing at 19200 baud."),
    res("R702", "1k", "FP_MOD_TX", "FP_RX", "J70", "talk", note="module TX -> P4 GPIO4 FP_RX, series protection (see R701)"),
    res("R706", "1k", "FP_MOD_WAKE", "FP_TOUCH", "J70", "talk",
        note="module WAKE -> U51 bit 7 FP_TOUCH (PI4IOE internal 100k pull-down = low while the module is unpowered). "
             "With the default fitting (option A below) the module never sleeps, so FP_TOUCH is only live in option B."),
    res("R703", "10k", "FP_3V3", "FP_RST", "J70", "talk",
        note="OPTION A (fitted, default): RST pulled up to FP_3V3 = the matcher runs whenever FP_EN powers it; low power "
             "comes from the load switch (0 uA off). Click on SW70 wakes the P4 (GPIO0), firmware raises FP_EN, "
             "finger still on the glass, match runs. No expander line is free for a separate RST (U50/U51 full)."),
    res("R704", "0", "FP_EN", "FP_RST", "J70", "talk", dnp=True,
        note="OPTION B: fit R704 + R705, remove R703: module always powered from 3V3, FP_EN drives RST (sleep < 16 uA "
             "per Waveshare p.2) and WAKE -> FP_TOUCH reports a finger without a click (touch-to-wake). Pick after "
             "measuring the module's cold-boot time vs. sleep-wake time on the bench."),
    res("R705", "0", "3V3", "FP_3V3", "U76", "talk", dnp=True, note="OPTION B: bypasses U76 (see R704)"),
    {"ref": "SW70", "fp": "phone:SnapDome_4mm", "value": "4 mm metal snap dome", "lcsc": "",
     "pins": {"1": "TALK_SW", "2": "GND"},
     "group": "talk", "side": "F", "h": 0.35,
     "note": "CHANGED 2026-11-14 (fit_check.py): the 1.6 mm B3U tact switch did not fit under the fingerprint module in the "
             "14.9 mm body. Now a 4 mm four-leg metal snap dome (phone practice, ~0.3-0.35 mm tall, ~160-200 gf, e.g. "
             "Snaptron F04-series) applied by hand on its carrier tape after assembly; centre pad = TALK_SW, ring = GND "
             "(gen_ui_pads.py SnapDome_4mm). The fingerprint module presses it through a 1 mm nub. Old note: " + DS_B3U + ": SPST top-actuated, 3.0 x 2.5 x 1.6 mm, 1.53 N, 0.15 mm pretravel, 200k ops; KiCad pads 1/2 are "
             "the two contacts. TALK KEY CENTRE = SW70 centre: the fingerprint module rests on it through a stiff disc "
             "with a ~1 mm nub, hard stop at ~0.25 mm travel (extras.md 1.3). Pressed = TALK_SW low -> P4 GPIO0 "
             "(deep-sleep wake, LP IO, not a strap)."},
    res("R707", "10k", "TALK_SW", "3V3", "SW70", "talk", note="pull-up (brief). 330 uA only while pressed."),
    cap("C703", "100nF", "TALK_SW", "SW70", "talk", note="debounce: 10k x 100 nF = 1 ms rise; firmware adds a 10-20 ms filter"),
]

# ---------------------------------------------------------------- light ring around the Talk key
RING = [("D700", 45, (7.42, -7.42)), ("D701", 135, (-7.42, -7.42)), ("D702", 225, (-7.42, 7.42)),
        ("D703", 315, (7.42, 7.42))]
PARTS += [
    {"ref": "U75", "fp": "Package_TO_SOT_SMD:SOT-583-8", "value": "LP5815DRLR", "lcsc": "C47262831",   # 160 (!)
     "pins": {"1": "I2C_SCL", "2": "I2C_SDA", "3": "GND", "4": "3V3", "5": "GND", "6": "RING_B", "7": "RING_G",
              "8": "RING_R"},
     "group": "ring", "near": "SW70", "side": "F", "h": 0.6,
     "note": DS_LP + " Figure 5-1 + Table 5-1 p.4 (DRL top view: 1 SCL, 2 SDA, 3 GND, 4 VCC, 5 STAT, 6 OUT2, 7 OUT1, "
             "8 OUT0; KiCad SOT-583-8 pads 1-4 left top->bottom, 5-8 right bottom->top = same order). I2C 0x2D (Device "
             "Comparison p.3), no address pin. VCC 2.5-5.5 V from 3V3 with 1 uF (p.4). STAT (5) = GND: STAT must be low "
             "for the shutdown command to take effect (p.21 7.4.2) and it disables instant-blink (p.19); shutdown 0.1 uA "
             "typ / 0.3 max (p.6). OUT0 = R, OUT1 = G, OUT2 = B cathodes of all four LEDs. 135 mV headroom (p.1), max "
             "25.5/51 mA per channel. STOCK ONLY 160: buy the board quantity now, or fit LP5817DRLR C47262829 "
             "(1,622 stock, same DRL pinout and 0x2D, no autonomous engine = host animates). Height: DRL 0.6 mm max."},
    cap("C717", "1uF", "3V3", "U75", "ring", note=DS_LP + " p.4: 1 uF VCC-GND close to the device"),
    cap("C718", "1uF", "VSYS", "D700", "ring", note="LED anode supply decoupling at the ring (shared by D700-D703)"),
]
for ref, ang, (x, y) in RING:
    PARTS.append(
        {"ref": ref, "fp": "phone:LED_XINGLIGHT_XL-1615RGBC_1.6x1.5mm", "value": "XL-1615RGBC-RF", "lcsc": "C965840",
         "pins": {"1": "RING_R", "2": "VSYS", "3": "RING_G", "4": "RING_B"},   # 638,302 in stock 2026-11-13
         "group": "ring", "near": "SW70", "side": "F", "h": 0.6,
         "note": f"RING POSITION: {ang} deg on the Ø21 mm circle, centre at (x {x:+.2f}, y {y:+.2f}) mm from the SW70 "
                 "centre (KiCad axes, y down). XINGLIGHT XL-1615RGBC-RF datasheet (LCSC C965840) p.8 top view + circuit: pin 2 "
                 "common anode, 1 R, 3 G, 4 B cathodes; p.3 IF max 20 mA/colour, VR 5 V. (Replaced XL-B1010RGBT-HF "
                 "2026-11-13: its top and bottom views contradict each other.) Anode on VSYS (not "
                 "3V3: blue VF 3.2 V + 0.135 V headroom does not fit under 3.3 V). ~5 mA per LED -> 20 mA per channel. "
                 "Footprint gen_xl1615.py (land 0.45 x 0.65 per datasheet p.8, numbered top view). Frosted PC light "
                 "guide ring ~1.5 mm wide above the LEDs; the module carrier blocks light into the sensor gap."})

# ================================================================ 2. side + volume keys
def key(sw, net, r, c, where, gpio):
    return [
        {"ref": sw, "fp": "Button_Switch_SMD:Panasonic_EVQPUK_EVQPUB", "value": "EVQPUB02K", "lcsc": "C2915192",  # 1,249
         "pins": {"1": net, "2": "GND"},
         "group": "keys", "side": "F", "h": 1.65,
         "note": f"{where}. " + DS_EVQ + ". Side-operated, 4.7 x 3.5 mm, 0.3 mm travel; KiCad pads '1' (x2) and '2' (x2) "
                 f"are the two contact pairs. Plunger flush with the PCB edge, pre-loaded key cap (no rattle). {gpio}."},
        res(r, "10k", net, "3V3", sw, "keys", note="pull-up (brief)"),
        cap(c, "100nF", net, sw, "keys", note="debounce 1 ms"),
    ]
PARTS += key("SW71", "SIDE_KEY", "R708", "C704", "Side key (camera / power) on the right edge", "SIDE_KEY -> P4 GPIO1, "
             "deep-sleep wake (LP IO, not a strap)")
PARTS += key("SW72", "VOL_UP", "R709", "C705", "Volume up, left edge", "VOL_UP -> U50 P2_5 (PCAL6524 INT -> EXP_INT); "
             "leave its internal pull off")
PARTS += key("SW73", "VOL_DN", "R710", "C706", "Volume down, left edge below SW72", "VOL_DN -> U50 P2_6")

# ================================================================ 3. privacy switch + hardware gate
PARTS += [
    {"ref": "SW74", "fp": "Button_Switch_SMD:SW_SPDT_PCM12", "value": "SSSS811101", "lcsc": "C109335",   # 41,967
     "pins": {"1": "MIC_3V3", "2": "3V3"},
     "nc": {"3": "privacy throw left open: tying it to GND would short 3V3 if the slider ever makes before it breaks "
                 "(changeover timing 'not specified', Alps p.1); PRIV_STATE reads the MIC_3V3 side instead"},
     "group": "privacy", "side": "F", "h": 1.4,
     "note": DS_ALPS + ": SPDT, 2 = common (circuit diagram p.3), 1.4 mm tall, 1.5 mm travel, 1.5 N, 0.3 A 5 V max / "
             "50 uA 3 V min (load here ~2 mA), 10k cycles. Land p.3 (top view): terminals 0.7 wide at x -2.25 / +0.75 / "
             "+2.25 from the centre of two Ø0.9 holes 3.0 apart, pads 1.0-2.5 mm from the hole line, 4 ground tabs "
             "1.0 x 0.8 at x +-3.65, y +-1.1: identical to KiCad SW_SPDT_PCM12 (pads 1/2/3 + unnumbered tabs + NPTH), "
             "checked pad by pad. Tabs are unnumbered in the footprint (mechanical, unconnected). Position 1-2 = mics "
             "allowed, 2-3 = privacy (MIC_3V3 dead). Edge-mounted: actuator through a 2.8 x 1.5 mm side slot, PCB edge "
             "within ~0.3 mm of the inner wall (extras.md 2.1). Firmware cannot override it."},
    {"ref": "U70", "fp": "Package_TO_SOT_SMD:SOT-363_SC-70-6", "value": "SN74LVC2G34DCKR", "lcsc": "C14461",   # 23,639
     "pins": {"1": "MIC_CLK", "2": "GND", "3": "CAM_EN", "4": "CAM_EN_SW", "5": "MIC_3V3", "6": "MIC_CLK_B"},
     "group": "privacy", "near": "SW74", "side": "F", "h": 1.1,
     "note": DS_LVC + " Pin Functions p.3 (DCK: 1 1A, 2 GND, 3 2A, 4 2Y, 5 VCC, 6 1Y = KiCad SOT-363 pads 1-6). "
             "VCC = MIC_3V3, so the gate only runs while the slide switch allows the mics. Ioff (p.1, p.5): with VCC = 0 "
             "the inputs (P4 MIC_CLK, expander CAM_EN at 3.3 V) cannot back-power MIC_3V3 and the outputs go high-Z, "
             "where R716 (MIC_CLK_G) and sch_power R117 (CAM_EN_SW) hold them low: no mic clock, camera load switch "
             "U15 off. 1A = MIC_CLK (P4 GPIO11) -> 1Y -> 33 ohm -> MIC_CLK_G (both mics). 2A = CAM_EN (U50 P0_6) -> 2Y = "
             "CAM_EN_SW (sch_power U15 EN). 4.8 MHz PDM clock is far inside the 'LVC2G34 range (4.1 ns @ 3.3 V)."},
    cap("C707", "100nF", "MIC_3V3", "U70", "privacy", note=DS_LVC + " p.10 Power Supply Recommendations: 0.1 uF at VCC"),
    res("R711", "100k", "MIC_3V3", "GND", "SW74", "privacy",
        note="bleed: MIC_3V3 (~2.3 uF total) falls in ~0.2 s after the switch opens even with the mics in clock-off "
             "mode (1 uA, IM73 p.8). 33 uA while the mics are allowed."),
    res("R712", "10k", "MIC_3V3", "PRIV_STATE", "SW74", "privacy",
        note="readback to U51 bit 6: high = mics allowed, low = privacy or mid-travel. With the PI4IOE 100k pull-down on: "
             "3.3 x 100/110 = 3.0 V high; switched off, R711 + the pull-down give 0 V. Firmware may clear that pull-down "
             "(R711 still pulls low)."),
    res("R713", "100k", "MIC_CLK", "GND", "U70", "privacy", note="gate input defined while the P4 resets (GPIO11 floats)"),
    res("R714", "100k", "CAM_EN", "GND", "U70", "privacy",
        note="gate input defined while U50 resets (PCAL6524 pulls off at power-up); nobody else pulls CAM_EN"),
    res("R715", "33", "MIC_CLK_B", "MIC_CLK_G", "U70", "privacy",
        note="source termination for the ~80 mm clock run to the two mics at opposite ends (sharp 'LVC edges)"),
    res("R716", "100k", "MIC_CLK_G", "GND", "U70", "privacy",
        note="brief: gated clock low when the gate is unpowered; also IM73 'clock off' mode (CLOCK pulled low, 1 uA, p.8)"),
]

# ================================================================ 4. microphones (PDM, bottom port)
def mic(u, lr, data, cs, cb, rt, where, group):
    return [
        {"ref": u, "fp": "Sensor_Audio:Infineon_PG-LLGA-5-2", "value": "IM73D122V01XTMA1", "lcsc": "C5563886",  # 2,820
         "pins": {"1": data, "2": "MIC_3V3", "3": "MIC_CLK_G", "4": lr, "5": "GND"},
         "group": group, "side": "F", "h": 1.2,
         "note": f"{where}. NEEDS AN ACOUSTIC HOLE: the footprint's NPTH is Ø0.8 mm (Infineon p.12 recommends a Ø0.8 PCB "
                 "port, 0.6-0.8 mm is fine); keep it unplated, no via/paste inside the GND ring, gasket on the B side "
                 "ducting to the enclosure hole. " + DS_MIC + " Table 9 p.11: 1 DATA, 2 VDD, 3 CLOCK, 4 LR, 5 GND. "
                 "Pad check: Fig.12 bottom view (pin 1 top-left, 2 below it, 3 top-right, 4 below 3, port below) and "
                 "Fig.13 top-view land (pin 1 bottom-left, port at the top, pads 0.75 x 0.45, rows 0.7, columns 1.7, "
                 "GND ring R0.58-R1.04) map onto the KiCad IM73A135 footprint exactly: pad 1 (-1.5,-0.85), 2 (-0.8,-0.85), "
                 "3 (-1.5,+0.85), 4 (-0.8,+0.85), 5 = GND ring, port at +0.68. So NO renumbering is needed: the stock "
                 "numbers already equal the IM73D122 pin numbers. VDD 1.62-3.6 V; ultrasonic mode 4.56-5.04 MHz clock "
                 "(900 uA typ); standby 25 uA. Stereo (p.10 Table 8): " +
                 ("LR = GND -> DATA driven on the FALLING clock edge." if lr == "GND" else
                  "LR = VDD -> DATA driven on the RISING clock edge.") +
                 " PCB holes and the enclosure must not be blocked by the gasket; cover the port during assembly "
                 "(p.14, no air blow, no washing)."},
        cap(cs, "100nF", "MIC_3V3", u, group, note=DS_MIC + " p.10 Fig.11 note: 100 nF at VDD"),
        cap(cb, "1uF", "MIC_3V3", u, group, note=DS_MIC + " p.7 note 4: 1 uF bypass close to VDD for best SNR"),
        res(rt, "100", data, "MIC_DATA", u, group, note=DS_MIC + " p.10: ~100 ohm RTERM on DATA against ringing"),
    ]
PARTS += mic("U71", "GND", "MIC1_DATA", "C708", "C709", "R717",
             "BOTTOM END (main voice mic, next to USB-C and the speaker, port to the bottom end wall)", "mic_bottom")
PARTS += mic("U72", "MIC_3V3", "MIC2_DATA", "C710", "C711", "R718",
             "TOP END (reference mic for noise cancelling / beamforming, port to the top end or the back near the "
             "camera; keep >= 60 mm from U71)", "mic_top")
PARTS += [res("R719", "100k", "MIC_DATA", "GND", "U71", "mic_bottom",
              note="MIC_DATA pull-down: both mics tri-state DATA in standby and are unpowered in privacy (same as the S3 "
                   "board's R6). P4 GPIO13 input.")]

# ================================================================ 5. speaker amp
PARTS += [
    {"ref": "U73", "fp": "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm", "value": "MAX98357AETE+T",
     "lcsc": "C910544",   # 27,906
     "pins": {"1": "AMP_DIN", "2": "AMP_GAIN", "3": "GND", "4": "AMP_SDMODE", "7": "VSYS", "8": "VSYS", "9": "SPK_P",
              "10": "SPK_N", "11": "GND", "14": "AMP_WS", "15": "GND", "16": "AMP_BCLK", "17": "GND"},
     "nc": {"5": "N.C. (Pin Description p.15)", "6": "N.C. (p.15)", "12": "N.C. (p.15)", "13": "N.C. (p.15)"},
     "group": "amp", "near": "LS70", "side": "F", "h": 0.8,
     "note": DS_AMP + " Pin Configurations + Pin Description p.15 (TQFN: 1 DIN, 2 GAIN_SLOT, 3/11/15 GND, 4 SD_MODE, "
             "5/6/12/13 N.C., 7/8 VDD, 9 OUTP, 10 OUTN, 14 LRCLK, 16 BCLK, EP = KiCad pad 17 to GND for heat). Same pin "
             "table as the reviewed voice-device U4. VDD = VSYS (2.5-5.5 V; DESIGN.md: amp from the battery side, not 3V3). "
             "LEFT CHANNEL: SD_MODE driven high through R720 (Table 5 p.17: > B2 1.245-1.5 V = left; RSMALL for 'right' "
             "at 3.3 V would be 210k, Table 6). Shutdown 0.6 uA when AMP_SD is low (p.5). GAIN_SLOT open = 9 dB (p.5, "
             "8.4-9.6 dB). Input: standard I2S on its own P4 port (AMP_BCLK GPIO9, AMP_WS GPIO10, AMP_DIN GPIO12). "
             "Speaker 8 ohm ~1 W: at VSYS 4.2 V the amp can deliver ~1 W, so firmware caps digital volume to the "
             "speaker's rating."},
    res("R720", "10k", "AMP_SD", "AMP_SDMODE", "U73", "amp",
        note=DS_AMP + " p.17: SD_MODE has a 92-108k pull-down (p.7). AMP_SD (U50 P1_3, 3.3 V push-pull) high -> "
             "3.3 x 92/(92+10) = 2.98 V worst case > B2 max 1.5 V = LEFT; floating/low -> shutdown. The series R also "
             "limits current into SD_MODE when VSYS (= amp VDD) sags below 3.3 V at the end of discharge, the case the "
             "datasheet asks a series resistor for (p.17, '~2 kOhm'); 10k keeps 2x margin on the left threshold."),
    res("R721", "100k", "AMP_GAIN", "GND", "U73", "amp", dnp=True,
        note="GAIN strap option (p.5/Table 8): open = 9 dB (default), fit 0 ohm to GND = 12 dB, fit 100k to GND = 15 dB. "
             "Start at 9 dB and set loudness in firmware."),
    cap("C712", "10uF", "VSYS", "U73", "amp", note=DS_AMP + " typical application p.29-30: 10 uF + 0.1 uF at VDD"),
    cap("C713", "100nF", "VSYS", "U73", "amp", note=DS_AMP + " p.29-30: 0.1 uF at VDD pins 7/8"),
    {"ref": "LS70", "fp": "phone:SPK_SPRING_PADS_2P_P2.4mm", "value": "Same Sky CMS-16093-078S", "lcsc": "",
     "pins": {"1": "SPK_P", "2": "SPK_N"},
     "group": "amp", "side": "F", "h": 0.05,
     "note": "CHANGED 2026-11-14: speaker = Same Sky CMS-16093-078S (16 x 9 x 3.0 mm, 8 ohm 0.7 W, spring contacts 4.0 free / "
             "3.0 working, drawing 09/11/2024 p.2); it is a driver, the case gives it a sealed back volume. Pads 1.3 x 1.6 "
             "on 2.4 mm per the drawing's recommended layout. Older note: speaker landing only (gen_ui_pads.py): 2 bare ENIG pads for the gold spring "
             "contacts of a ~15 x 11 mm box speaker (AAC/Ruiside 1511 class, bought separately) at the bottom end; a "
             "wired FUET FS16MS0810-H4.0 (C482306, 16 mm round, 4.0 mm, 8 ohm 1 W, only 77 at JLC) can be soldered here "
             "instead. lcsc empty: nothing for JLC to place. Pad 1 = OUTP. Filterless class D with < 10 mm leads: no "
             "ferrites fitted (add them if radiated EMI shows up near the LTE antenna at the bottom end)."},
]

# ================================================================ 6. haptics
PARTS += [
    {"ref": "U74", "fp": "Package_SO:MSOP-10_3x3mm_P0.5mm", "value": "DRV2605LDGSR", "lcsc": "C527464",   # 6,080
     "pins": {"1": "DRV_REG", "2": "I2C_SCL", "3": "I2C_SDA", "4": "GND", "5": "3V3", "6": "3V3", "7": "LRA_P",
              "8": "GND", "9": "LRA_N", "10": "3V3"},
     "group": "haptic", "near": "M70", "side": "F", "h": 1.1,
     "note": DS_DRV + " DGS Pin Functions p.5 (1 REG, 2 SCL, 3 SDA, 4 IN/TRIG, 5 EN, 6 VDD/NC, 7 OUT+, 8 GND, 9 OUT-, "
             "10 VDD; DGS = VSSOP-10 3x3 0.5 mm = KiCad MSOP-10 land, pads 1-10). Same pin table as the reviewed "
             "voice-device U5. I2C 0x5A (p.25). EN (5) tied to 3V3 (brief: no free expander line) and the part is parked "
             "with the STANDBY bit: 4.1 uA typ / 7 max (p.7). IN/TRIG (4) to GND: rev D 'connect to GND if not used' "
             "(p.2). VDD/NC (6) tied to VDD (p.5). CHANGE vs the S3 board: VDD = 3V3, not the battery rail, because EN/SDA/"
             "SCL abs max is VDD + 0.3 V (p.6) and the I2C bus is 3.3 V while VSYS can sag below 3.0 V; 2-5.2 V supply, "
             "the 1.8 Vrms LRA needs only ~2.6 V peak. Firmware: LRA mode, rated 1.8 Vrms, ODclamp ~1.9 Vrms, 235 Hz, "
             "run auto-calibration once."},
    cap("C714", "1uF", "DRV_REG", "U74", "haptic", note=DS_DRV + " p.5: REG needs 1 uF"),
    cap("C715", "1uF", "3V3", "U74", "haptic", note=DS_DRV + " p.5: VDD needs 1 uF"),
    cap("C716", "100nF", "3V3", "U74", "haptic", note="HF decoupling at VDD (as on the reviewed S3 board, C8)"),
    {"ref": "M70", "fp": "phone:GSwitch_GT-BTP20002-0170B_2P_P2.0", "value": "GT-BTP20002-0170B-020A (LRA VG0832009L)",
     "lcsc": "C55079717", "pins": {"1": "LRA_P", "2": "LRA_N"},
     "group": "haptic", "side": "F", "h": 2.0,
     "note_2026_11_14": "No-solder LRA (Louis: click together): Vybronics VG0832009L, 8.0 x 3.25 mm, 1.8 Vrms, 235 Hz, "
             "22.5 ohm, 1.0-1.8 G, pressure-contact flex tail (4.75 wide, to 8.55 from the motor centre, 2 gold pads "
             "~1.2 x 2.5 on ~1.8 mm facing the board). Motor bonded under the cover glass, tail pointing +y; this JLC-placed "
             "2-pin spring (working height 2.0) presses the tail pads. Buy the motor at DigiKey (1670-VG0832009L-ND). "
             "MUST-verify the tail pad spacing on a sample. The text below is the older LD0832AA note (same drive).",
     "note": DS_LRA + ": Ø8 x 3.25 mm coin LRA, 1.8 Vrms rated (0.1-1.9), 235 +-10 Hz, 24 ohm +-10 %, 90 mA rms max, "
             "AWG32 UL3302 leads (p.13). Landing pads only (gen_ui_pads.py): the motor is bought as C2682305 (1,012 at "
             "JLC) but hand-soldered by its wires and bonded to the enclosure/frame with its adhesive, so lcsc is "
             "empty. Mount it near the Talk key (where the hand is) and keep it >= 15 mm from the magnetometer U53."},
]

# ================================================================ 8. microSD (back side, beside the camera)
PARTS += [
    {"ref": "J71", "fp": "Connector_Card:microSD_HC_Molex_104031-0811", "value": "104031-0811", "lcsc": "C585350",  # 47,866
     "pins": {"1": "SD_D2", "2": "SD_D3", "3": "SD_CMD", "4": "SD_3V3", "5": "SD_CLK", "6": "GND", "7": "SD_D0",
              "8": "SD_D1", "9": "SD_CD", "10": "GND", "SH": "GND"},
     "group": "sd", "side": "B", "h": 1.5,
     "note": DS_SD + ". microSD contact order (SD spec / Molex): 1 DAT2, 2 CD/DAT3, 3 CMD, 4 VDD, 5 CLK, 6 VSS, 7 DAT0, "
             "8 DAT1 = KiCad pads 1-8 (1.1 mm pitch row); pads 9/10 = card-detect switch (normally open), 4 'SH' = "
             "shell tabs to GND. 1-bit SD mode on SDMMC slot 0: SD_D0 GPIO39, SD_CLK GPIO43, SD_CMD GPIO44 (VO4 bank, "
             "firmware sets 3.3 V before SD_EN; SD_3V3 is off at boot so the pull-ups cannot back-feed the 1.8 V bank). "
             "CD: pad 9 = SD_CD (U50 P1_2, PCAL internal pull-up), pad 10 = GND -> card in = low. UNVERIFIED: which of "
             "pads 9/10 is the switch common was not read from the Molex drawing (Molex site blocks downloads); the "
             "switch is 2-terminal so either works UNLESS one terminal is tied to the shell inside: meter a sample "
             "(pad 9 must be open to SH with no card). 1.42 mm tall (h 1.5). SIDE B: back, beside the camera J3, card "
             "slot opening at the board edge."},
    cap("C719", "10uF", "SD_3V3", "J71", "sd", side="B", note="card supply bulk (write peaks ~100-200 mA)"),
    cap("C720", "100nF", "SD_3V3", "J71", "sd", side="B", note="HF decoupling at pin 4"),
    res("R722", "10k", "SD_CMD", "SD_3V3", "J71", "sd", side="B", note="CMD pull-up (SD spec 10-100k, brief 10k)"),
    res("R723", "10k", "SD_D0", "SD_3V3", "J71", "sd", side="B", note="DAT0 pull-up (brief 10k)"),
    res("R724", "10k", "SD_D1", "SD_3V3", "J71", "sd", side="B", note="DAT1 unused in 1-bit mode: pull-up (SD spec)"),
    res("R725", "10k", "SD_D2", "SD_3V3", "J71", "sd", side="B", note="DAT2 unused in 1-bit mode: pull-up (SD spec)"),
    res("R726", "10k", "SD_D3", "SD_3V3", "J71", "sd", side="B",
        note="CD/DAT3 pull-up: keeps the card in SD (not SPI) mode at CMD0 (SD spec)"),
]

for p in PARTS:                       # drop empty placement hints
    if p.get("near") is None: p.pop("near", None)
