"""Sensors / control subsystem of the concierge phone: two I2C GPIO expanders, IMU, magnetometer, barometer, RH/T, ambient
light, spectral sensor (+ its 1.8 V LDO), VOC/NOx gas sensor, secure element, ToF ranger. Rules: CONTRACT.md.
Refs: U50-U69, C500-C599, R500-R599 (D500-D509 unused).

Every IC pin table below was read from the manufacturer PDF (URL + page in each part's "note") and compared with the pad
numbers of the footprint actually used (stock .kicad_mod, or the phone.pretty file written by the named gen_*.py).
All parts sit on 3V3 and I2C_SDA / I2C_SCL (pull-ups are in core, not here).

I2C map on this file (7-bit): 0x22 U50 PCAL6524 (ADDR=VSS), 0x43 U51 PI4IOE5V6408 (ADDR=GND), 0x69 U52 ICM-42670-P (AD0=1),
0x30 U53 MMC5603NJ (fixed), 0x46 U54 BMP581 (SDO=GND), 0x44 U55 SHT40-AD1B (fixed), 0x45 U56 OPT3004 (ADDR=VDD),
0x39 U57 AS7341 (fixed), 0x59 U59 SGP41 (fixed), 0x60 U60 ATECC608B-MAHDA (factory 0xC0 8-bit), 0x29 U61 VL53L1CX (default).
No clash with the CONTRACT.md map. Traps: PI4IOE5V6408 ADDR=1 would be 0x44 (SHT40), OPT3004 ADDR=GND would be 0x44,
SHT40-BD1B would be 0x45 (OPT3004), ATECC608B-TFLXTLS ships at 0x36 (OV5647) and -TNGLoRaWAN at 0x59 (SGP41): order -MAHDA.

EXP_INT (open drain, 10k pull-up in core) is the wire-OR of U50 INT, U51 INT, U56 OPT3004 INT and U57 AS7341 INT
(all four are open-drain outputs; OPT3004 and AS7341 power up with their interrupt off).

Pull resistors on expander lines (decided per line; parts at boot are inputs, PCAL6524 internal pulls are OFF at power-up,
PI4IOE5V6408 internal 100k PULL-DOWNS are ON at power-up, register 0Bh = FFh / 0Dh = 00h, DS40583 p.9):
  here:   LTE_OE_N 10k up (shifters off at reset, DESIGN.md), LTE_PWRKEY 100k down (2N7002 gate off), USB_SEL 100k down
          (TS3USB221 S low = flashing path at reset, DESIGN.md), SBU_OE_N 100k up (2nd TS3USB221A off at boot), FP_EN 100k
          down (fingerprint off), TOF_INT 10k up (VL53L1 GPIO1 is open drain, ST value), EXP_RST_N 10k up (both RESET pins).
  in sch_power.py already (not duplicated): LTE_EN 10k down (R113), DISP_EN / RF_EN / SD_EN / CAM_EN_SW 100k down,
          CHG_N / PGOOD_N / FUEL_ALRT 10k up.
  none:   TOF_XSHUT uses the PI4IOE default 100k pull-down (ToF held in HW standby until firmware drives it high; ST only asks
          that XSHUT is never floating). GNSS_RST: MAX-M10S RESET_N has its own pull-up; drive it like open drain (output
          low / input) because PI4IOE outputs are push-pull. LTE_DTR_3V / LTE_STATUS_3V / LTE_RI_3V, SD_CD, TP_INT,
          LORA_BUSY, VOL_UP / VOL_DN: firmware enables the PCAL6524 100k pulls (keys + SD_CD: pull-up; floating shifter /
          radio lines: pull-down). LCD_RST, LORA_RST, RF_BAND, RF_RADIO: their parts sit on switched rails that are off at
          boot, so no external pull (a pull-up would back-power them). AMP_SD: left to sch_ui (the MAX98357A SD_MODE
          resistor sets the channel, an extra pull here would shift it). PRIV_STATE / FP_TOUCH: PI4IOE default pull-down.
  Firmware: clear PI4IOE 0Bh bits 0,1,4,5 (CHG_N, PGOOD_N, TOF_INT, FUEL_ALRT have 10k pull-ups: 30 uA each otherwise)
  and bit 2 (GNSS_RST).

Nets invented here (not in CONTRACT.md): EXP_RST_N (shared RESET of U50 + U51), 1V8_SPEC (AS7341 supply from U58),
SGP_VDD (SGP41 VDD after the 4.7 ohm / 1 uF filter Sensirion asks for).

Outside air: U54 BMP581, U55 SHT40, U59 SGP41 share group 'vent' (one vented chamber, membrane; SHT40 away from the SGP41
hotplate and from the PMIC heat). Light: U56 OPT3004 + U57 AS7341 group 'window' under the IR-ink window of the front plate
(AS7341 wants a diffuser over it, DS000504 11.3). ToF U61 side 'B' under a 940 nm window (crosstalk cal after assembly).
U53 magnetometer: keep far from speaker, LRA, battery leads and the torch inductor."""

C0402, C0603 = "Capacitor_SMD:C_0402_1005Metric", "Capacitor_SMD:C_0603_1608Metric"
R0402 = "Resistor_SMD:R_0402_1005Metric"
H = {C0402: 0.55, C0603: 0.9, R0402: 0.4}

# LCSC numbers, checked in the JLC parts API 2026-11-13 (stock that day in brackets; "basic" = no feeder fee)
CAP = {"100nF": "C1525",     # CL05B104KO5NNNC 16 V X7R 0402, basic (31.98M)
       "10nF": "C15195",     # CL05B103KB5NNNC 50 V X7R 0402, basic (5.55M)
       "1uF": "C52923",      # CL05A105KA5NQNC 25 V X5R 0402, basic (10.47M)
       "2.2uF": "C12530",    # CL05A225MQ5NSNC 6.3 V X5R 0402, basic (3.36M)
       "4.7uF": "C23733"}    # CL05A475MP5NRNC 10 V X5R 0402, basic (643k)
RES = {"10k": "C25744",      # UNI-ROYAL 0402WGF1002TCE, basic (21.26M)
       "100k": "C25741",     # UNI-ROYAL 0402WGF1003TCE, basic (8.51M)
       "4.7": "C137962"}     # YAGEO RC0402FR-074R7L 1 %, extended (310k)

def cap(ref, val, a, near, b="GND", group="sense", side="F", note=""):
    return {"ref": ref, "fp": C0402, "value": val, "lcsc": CAP[val], "pins": {"1": a, "2": b}, "group": group,
            "near": near, "side": side, "h": H[C0402], "note": note}

def res(ref, val, a, b, near, group="sense", side="F", note=""):
    return {"ref": ref, "fp": R0402, "value": val, "lcsc": RES[val], "pins": {"1": a, "2": b}, "group": group,
            "near": near, "side": side, "h": H[R0402], "note": note}

DS_PCAL = ("NXP PCAL6524 Rev.2 15 May 2019 https://www.nxp.com/docs/en/data-sheet/PCAL6524DS.pdf "
           "(read copy: https://cdn.sparkfun.com/assets/7/c/0/3/4/PCAL6524_Datasheet.pdf)")
DS_PI4 = "Diodes PI4IOE5V6408 DS40583 Rev 3-5 https://www.diodes.com/assets/Datasheets/PI4IOE5V6408.pdf"
DS_ICM = ("TDK ICM-42670-P DS-000451 Rev 1.1 "
          "https://datasheet.lcsc.com/datasheet/pdf/826e0bd2b58f8a1f9105becd4b111f93.pdf?productCode=C3288646")
DS_MMC = "MEMSIC MMC5603NJ Rev.B https://www.lcsc.com/datasheet/lcsc_datasheet_1912111437_MEMSIC-MMC5603NJ_C404328.pdf"
DS_BMP = ("Bosch BST-BMP581-DS004-13 rev 1.13 "
          "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp581-ds004.pdf")
DS_SHT = ("Sensirion Datasheet SHT4x Version 1 Oct 2020 "
          "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_Sensirion-SHT40-AD1B-R3_C2848306.pdf")
DS_OPT = "TI OPT3004 SBOS929A https://www.ti.com/lit/ds/symlink/opt3004.pdf"
DS_AS = ("ams AS7341 DS000504 v2-00 "
         "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_Advanced-Monolithic-Systems-AS7341-DLGM_C2649486.pdf")
DS_LDO = ("Torex XC6206 ETR0305_005 "
          "https://datasheet.lcsc.com/datasheet/pdf/8662c19cf5b04655a06f75aaacb98df2.pdf?productCode=C21659")
DS_SGP = ("Sensirion SGP41 v1.0 Dec 2021 "
          "https://sensirion.com/media/documents/5FE8673C/61E96F50/Sensirion_Gas_Sensors_Datasheet_SGP41.pdf")
DS_ATE = ("Microchip ATECC608B Summary DS40002239B "
          "https://ww1.microchip.com/downloads/aemDocuments/documents/SCBU/ProductDocuments/DataSheets/"
          "ATECC608B-CryptoAuthentication-Device-Summary-Data-Sheet-DS40002239B.pdf")
DS_TOF = ("ST VL53L1X DocID031281 Rev 2 (VL53L1CXV0FY/1) "
          "https://datasheet.lcsc.com/datasheet/pdf/41a9cbfba8e851db4eb7624b914311e9.pdf?productCode=C190004")

PARTS = []

# ---------------------------------------------------------------- U50 PCAL6524 24-bit expander, 0x22
P0 = ["LTE_EN", "LTE_PWRKEY", "LTE_DTR_3V", "LTE_OE_N", "LTE_STATUS_3V", "LTE_RI_3V", "CAM_EN", "DISP_EN"]
P1 = ["RF_EN", "SD_EN", "SD_CD", "AMP_SD", "LCD_RST", "TP_INT", "IMU_INT", "USB_SEL"]
P2 = ["SBU_OE_N", "RF_BAND", "RF_RADIO", "LORA_BUSY", "LORA_RST", "VOL_UP", "VOL_DN", "FP_EN"]
u50 = {str(1 + i): n for i, n in enumerate(P0 + P1 + P2)}   # HUQFN32 pins 1-8 P0_0..P0_7, 9-16 P1_x, 17-24 P2_x
u50.update({"25": "GND", "26": "GND", "27": "3V3", "28": "EXP_RST_N", "29": "I2C_SCL", "30": "I2C_SDA", "31": "3V3",
            "32": "EXP_INT", "33": "GND"})
PARTS += [
    {"ref": "U50", "fp": "Package_DFN_QFN:HVQFN-32-1EP_5x5mm_P0.5mm_EP3.1x3.1mm", "value": "PCAL6524HEAZ", "lcsc": "C3000497",
     "pins": u50, "group": "sense", "side": "F", "h": 0.6,
     "note": DS_PCAL + ": Table 3 pin description p.6-7 (HUQFN32: 1-8 P0_0-7, 9-16 P1_0-7, 17-24 P2_0-7, 25 VSS, 26 ADDR, "
             "27 VDD(P), 28 RESET, 29 SCL, 30 SDA, 31 VDD(I2C-bus), 32 INT), Fig 2 p.5 (pin 1 top-left, CCW). "
             "Table 4 p.7: ADDR=VSS -> 44h 8-bit = 0x22. INT open drain (p.2, p.27). Package SOT1426-1 HUQFN32 5x5x0.56 "
             "p.60 (EP 3.0 nom), NXP footprint Fig 42 p.65 (lands 0.29x0.9 at 0.5, EP land 3.0); stock HVQFN-32 EP3.1 has the "
             "same pin order (pad 1 top-left CCW) and 0.875x0.25 lands. Pad 33 = exposed pad: datasheet silent on its net, "
             "soldered to GND (NXP HVQFN practice) - UNVERIFIED. Port lines per CONTRACT.md. Internal 100k pulls are off at "
             "power-up (regs 4Ch-4Eh = 00h, p.12)."},
    cap("C500", "100nF", "3V3", "U50", note=DS_PCAL + " Table 3 p.6: VDD(P) pin 27, 0.1 uF bypass required, close"),
    cap("C501", "100nF", "3V3", "U50", note=DS_PCAL + ": VDD(I2C-bus) pin 31 bypass"),
    res("R500", "10k", "EXP_RST_N", "3V3", "U50",
        note="RESET pull-up for U50 pin 28 (" + DS_PCAL + " Table 3 p.7) and U51 pin 10 (" + DS_PI4 + " p.2): no active reset"),
    res("R501", "10k", "LTE_OE_N", "3V3", "U50", note="U50 P0_3: both SN74AXC4T774 OE high = off at reset (CONTRACT.md, DESIGN.md)"),
    res("R502", "100k", "LTE_PWRKEY", "GND", "U50",
        note="U50 P0_1: holds the PWRKEY 2N7002 gate off while the expander pin is still an input (DESIGN.md: 2N7002 open "
             "drain to PWRKEY). Core: do not add a second gate pull-down."),
    res("R503", "100k", "USB_SEL", "GND", "U50", note="U50 P1_7: TS3USB221 S low at reset = flashing path (DESIGN.md)"),
    res("R504", "100k", "SBU_OE_N", "3V3", "U50", note="U50 P2_0: 2nd TS3USB221A OE high = off at boot (DESIGN.md)"),
    res("R505", "100k", "FP_EN", "GND", "U50", note="U50 P2_7: fingerprint module off until firmware enables it"),
]

# ---------------------------------------------------------------- U51 PI4IOE5V6408 8-bit expander, 0x43
PARTS += [
    {"ref": "U51", "fp": "Package_DFN_QFN:UQFN-16_1.8x2.6mm_P0.4mm", "value": "PI4IOE5V6408ZTAEX", "lcsc": "C526717",
     "pins": {"1": "EXP_INT", "2": "3V3", "3": "PRIV_STATE", "4": "FP_TOUCH", "5": "FUEL_ALRT", "6": "TOF_INT",
              "7": "TOF_XSHUT", "8": "GNSS_RST", "9": "GND", "10": "EXP_RST_N", "11": "PGOOD_N", "12": "CHG_N",
              "13": "I2C_SCL", "14": "I2C_SDA", "15": "3V3", "16": "GND"},
     "group": "sense", "side": "F", "h": 0.55,
     "note": DS_PI4 + ": pin table p.2 (1 INT, 2 VDD(P), 3 P7, 4 P6, 5 P5, 6 P4, 7 P3, 8 P2, 9 ADDR, 10 RESET, 11 P1, 12 P0, "
             "13 SCL, 14 SDA, 15 VDD(I2C), 16 GND; CCW). Address Table 1 p.8: ADDR=0 -> 1000011 = 0x43 (ADDR=1 would be 0x44 = "
             "SHT40); p.14 example confirms 86h. INT open drain (p.1). Package ZTA UQFN-16 1.8x2.6 P0.4 no EP, land pattern "
             "p.15: pin 1 top of the left (2.6 mm) side, CCW = stock UQFN-16_1.8x2.6mm_P0.4mm pad order (stock lands 0.8 long "
             "vs Diodes 0.5, same inner edge). Port 0..7 = CHG_N, PGOOD_N, GNSS_RST, TOF_XSHUT, TOF_INT, FUEL_ALRT, "
             "PRIV_STATE, FP_TOUCH (CONTRACT.md). Power-up: all inputs, 100k pull-DOWN on every port pin (p.9)."},
    cap("C502", "100nF", "3V3", "U51", note=DS_PI4 + ": VDD(P) pin 2 bypass"),
    cap("C503", "100nF", "3V3", "U51", note=DS_PI4 + ": VDD(I2C) pin 15 bypass"),
]

# ---------------------------------------------------------------- U52 ICM-42670-P IMU, 0x69
PARTS += [
    {"ref": "U52", "fp": "Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y", "value": "ICM-42670-P", "lcsc": "C3288646",
     "pins": {"1": "3V3", "4": "IMU_INT", "5": "3V3", "6": "GND", "7": "GND", "8": "3V3", "12": "3V3",
              "13": "I2C_SCL", "14": "I2C_SDA"},
     "nc": {"2": "RESV: no connect allowed (Table 9 p.18)", "3": "RESV: no connect allowed (Table 9 p.18)",
            "9": "INT2 unused (all interrupts mapped to INT1)", "10": "RESV: no connect allowed (Table 9 p.18)",
            "11": "RESV: no connect allowed (Table 9 p.18)"},
     "group": "sense", "side": "F", "h": 0.81,
     "note": DS_ICM + ": Table 9 / Fig 4 p.18 (1 AP_SDO/AD0, 2-3 RESV, 4 INT1, 5 VDDIO, 6 GND, 7 FSYNC, 8 VDD, 9 INT2, 10-11 RESV, "
             "12 AP_CS, 13 SCL, 14 SDA; 1-4 left top->bottom, 5-7 bottom, 8-11 right bottom->top, 12-14 top). Package p.37: "
             "D 3.0 x E 2.5, 4 pads on the 2.5 sides = stock LGA-14_3x2.5 (pad 1 top-left, same order). AD0 high -> 1101001 = "
             "0x69 (p.13). FSYNC to GND when unused (p.18). AP_CS to VDDIO for I2C (p.18). INT1 push-pull to U50 P1_6. "
             "Caps Fig 5 p.19 / Table 10 p.20: VDD 0.1 uF + 2.2 uF, VDDIO 10 nF. Mount near board centre, away from flex."},
    cap("C504", "100nF", "3V3", "U52", note=DS_ICM + " Table 10 p.20: VDD C1 0.1 uF"),
    cap("C505", "2.2uF", "3V3", "U52", note=DS_ICM + " Table 10 p.20: VDD C2 2.2 uF"),
    cap("C506", "10nF", "3V3", "U52", note=DS_ICM + " Table 10 p.20: VDDIO C3 10 nF"),
]

# ---------------------------------------------------------------- U53 MMC5603NJ magnetometer, 0x30
PARTS += [
    {"ref": "U53", "fp": "phone:MEMSIC_WLP-4_0.8x0.8mm_P0.4mm", "value": "MMC5603NJ", "lcsc": "C404328",
     "pins": {"A1": "GND", "A2": "I2C_SCL", "B1": "3V3", "B2": "I2C_SDA"},
     "group": "sense", "side": "F", "h": 0.43,
     "note": DS_MMC + ": pin table p.4 (A1 VSA, A2 SCL, B1 VDD, B2 SDA), package p.17, land p.18 -> phone footprint by "
             "gen_mmc5603.py. Address 0110000 = 0x30 (p.12). VDD 1.62-3.6 V, min 2.2 uF bypass close (p.5). 0.4 mm pitch "
             "WLP: check JLC can place it (0.23 mm lands). Keep far from speaker, LRA, battery leads, inductors."},
    cap("C507", "2.2uF", "3V3", "U53", note=DS_MMC + " p.5: minimum 2.2 uF bypass in close proximity to VDD"),
]

# ---------------------------------------------------------------- U54 BMP581 barometer, 0x46  (vent)
PARTS += [
    {"ref": "U54", "fp": "phone:Bosch_BMP581_LGA-10_2x2mm_P0.5mm", "value": "BMP581", "lcsc": "C5362283",
     "pins": {"1": "3V3", "2": "I2C_SCL", "3": "GND", "4": "I2C_SDA", "5": "GND", "6": "3V3", "7": "GND", "8": "GND",
              "9": "GND", "10": "3V3"},
     "group": "vent", "near": "U55", "side": "F", "h": 0.8,
     "note": DS_BMP + ": Table 28 + Fig 23 p.46 (1 VDDIO, 2 SCK, 3 VSS, 4 SDI, 5 SDO, 6 CSB, 7 INT, 8-9 VSS, 10 VDD); outline "
             "p.68, land p.69 -> phone footprint by gen_bmp581.py. I2C: CSB to VDDIO (6.2.3 p.48), SDO=GND -> 0x46 (p.38, "
             "SDO must not float). INT not used: tied to GND, INT_CONFIG.int_en must stay 0 (6.2 p.46). Caps Fig 26 p.48: "
             "100 nF on VDD and VDDIO. No vias/traces/mask under the part (p.69). Port hole on the lid: vented chamber."},
    cap("C508", "100nF", "3V3", "U54", group="vent", note=DS_BMP + " Fig 26 p.48: VDD 100 nF"),
    cap("C509", "100nF", "3V3", "U54", group="vent", note=DS_BMP + " Fig 26 p.48: VDDIO 100 nF"),
]

# ---------------------------------------------------------------- U55 SHT40-AD1B RH/T, 0x44  (vent)
PARTS += [
    {"ref": "U55", "fp": "Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad", "value": "SHT40-AD1B-R3",
     "lcsc": "C2848306", "pins": {"1": "I2C_SDA", "2": "I2C_SCL", "3": "3V3", "4": "GND"},
     "group": "vent", "side": "F", "h": 0.6,
     "note": DS_SHT + ": pins p.13 (1 SDA, 2 SCL, 3 VDD, 4 VSS; pin 1 top-left, 2 bottom-left, 3 bottom-right, 4 top-right "
             "= stock footprint), land p.12 (die pad not soldered, no copper under the sensor), app circuit p.3 (100 nF). "
             "AD1B = 0x44 (p.1, p.15). Thermal slots around it; away from the SGP41 hotplate and charger heat."},
    cap("C510", "100nF", "3V3", "U55", group="vent", note=DS_SHT + " Fig 1 p.3: 100 nF VDD-GND"),
]

# ---------------------------------------------------------------- U56 OPT3004 ambient light, 0x45  (window)
PARTS += [
    {"ref": "U56", "fp": "phone:TI_DNP0006A_USON-6-1EP_2x2mm_P0.65mm_EP0.65x1.35mm", "value": "OPT3004DNPR",
     "lcsc": "C2655153",
     "pins": {"1": "3V3", "2": "3V3", "3": "GND", "4": "I2C_SCL", "5": "EXP_INT", "6": "I2C_SDA", "7": "GND"},
     "group": "window", "side": "F", "h": 0.65,
     "note": DS_OPT + ": Table 6-1 p.3 (1 VDD, 2 ADDR, 3 GND, 4 SCL, 5 INT open drain, 6 SDA), DNP0006A outline p.47, land "
             "p.48 -> phone footprint by gen_opt3004.py, thermal pad 7 to GND (11.1 p.34). Table 8-1 p.13: ADDR=VDD -> "
             "1000101 = 0x45. INT open drain -> EXP_INT (powers up in shutdown, no interrupt until configured). 100 nF "
             "bypass (10 p.33). Optical: under the IR-ink window, no reflective parts around it (11.1)."},
    cap("C511", "100nF", "3V3", "U56", group="window", note=DS_OPT + " 10 p.33: 100 nF bypass close to VDD"),
]

# ---------------------------------------------------------------- U57 AS7341 spectral, 0x39 + U58 1.8 V LDO  (window)
PARTS += [
    {"ref": "U57", "fp": "Package_LGA:AMS_OLGA-8_2x3.1mm_P0.8mm", "value": "AS7341-DLGM", "lcsc": "C2649486",
     "pins": {"1": "1V8_SPEC", "2": "I2C_SCL", "3": "GND", "5": "GND", "7": "EXP_INT", "8": "I2C_SDA"},
     "nc": {"4": "LDR LED current sink: no flash/indicator LED driven by the sensor (LED_ACT reset 0)",
            "6": "GPIO: unused; input buffer off at reset (GPIO_IN_EN=0, reg 0xBE p.29), photodiode off (0x73 p.28)"},
     "group": "window", "near": "U56", "side": "F", "h": 1.0,
     "note": DS_AS + ": pin diagram + description p.6 (1 VDD, 2 SCL, 3 GND, 4 LDR, 5 PGND, 6 GPIO, 7 INT open drain, 8 SDA; "
             "portrait top view, 1-4 left top->bottom, 5-8 right bottom->top = stock AMS_OLGA-8 footprint, made for this "
             "part from p.63 of v3-00), PCB pad layout p.59. Address 0x39 (p.21). VDD 1.7-2.0 V (p.8, abs max 2.2 V p.7) -> "
             "U58 1.8 V LDO. SCL/SDA/INT abs max 3.6 V, VIH 1.26 V (p.7-8): runs on the 3.3 V bus with no shifter (3.3 V +5 % "
             "is under 3.6 V). INT open drain -> EXP_INT (off at reset). Needs a diffuser over the window (11.3 p.60). "
             "LCSC C2649486 is listed as 'Advanced-Monolithic-Systems' AS7341-DLGM, 5,240 in stock 2026-11-13."},
    cap("C512", "100nF", "1V8_SPEC", "U57", group="window", note="AS7341 VDD local bypass (" + DS_AS + " p.6)"),
    {"ref": "U58", "fp": "Package_TO_SOT_SMD:SOT-23", "value": "XC6206P182MR", "lcsc": "C21659",
     "pins": {"1": "GND", "2": "1V8_SPEC", "3": "3V3"},
     "group": "window", "near": "U57", "side": "F", "h": 1.3,
     "note": DS_LDO + ": PIN ASSIGNMENT p.2 (SOT-23: 1 VSS, 2 VOUT, 3 VIN), 1.8 V +-2 %, 1 uA Iq, ceramic-stable, CIN = CL "
             "= 1 uF (test circuits). Load: AS7341 0.3 mA max (p.8). Genuine Torex part (32,386 at JLC)."},
    cap("C513", "1uF", "3V3", "U58", group="window", note=DS_LDO + ": CIN 1 uF"),
    cap("C514", "1uF", "1V8_SPEC", "U58", group="window", note=DS_LDO + ": CL 1 uF"),
]

# ---------------------------------------------------------------- U59 SGP41 VOC/NOx, 0x59  (vent)
PARTS += [
    {"ref": "U59", "fp": "phone:Sensirion_DFN-6-1EP_2.44x2.44mm_P0.8mm_SGP4x", "value": "SGP41-D-R4", "lcsc": "C3659325",
     "pins": {"1": "SGP_VDD", "2": "GND", "3": "I2C_SDA", "4": "GND", "5": "3V3", "6": "I2C_SCL", "7": "GND"},
     "group": "vent", "near": "U54", "side": "F", "h": 0.95,
     "note": DS_SGP + ": Table 6 p.7 (1 VDD, 2 VSS, 3 SDA, 4 n/a -> GND, 5 VDDH, 6 SCL; die pad = GND, solder it), "
             "Fig 6 p.8 (VDD through 4.7 ohm + 1 uF RC, VDDH 1 uF, both from the same supply), outline p.18, land p.19 -> "
             "phone footprint by gen_sgp41.py. Address 0x59 (4.2 p.12). 3.0-4.2 mA average at 3.3 V while measuring (Table 2 p.5). Sensor opening "
             "on the top face: vented chamber, no bright light on it (2.6 p.8), assemble in the last reflow (p.19)."},
    res("R506", "4.7", "3V3", "SGP_VDD", "U59", group="vent", note=DS_SGP + " Fig 6 p.8: 4.7 ohm VDD filter resistor"),
    cap("C515", "1uF", "SGP_VDD", "U59", group="vent", note=DS_SGP + " Fig 6 p.8: 1 uF after the 4.7 ohm (VDD RC)"),
    cap("C516", "1uF", "3V3", "U59", group="vent", note=DS_SGP + " 2.5 p.7: 1 uF recommended on VDDH"),
]

# ---------------------------------------------------------------- U60 ATECC608B-MAHDA secure element, 0x60
PARTS += [
    {"ref": "U60", "fp": "Package_DFN_QFN:DFN-8-1EP_3x2mm_P0.5mm_EP1.3x1.5mm", "value": "ATECC608B-MAHDA-S",
     "lcsc": "C1518773",
     "pins": {"4": "GND", "5": "I2C_SDA", "6": "I2C_SCL", "8": "3V3", "9": "GND"},
     "nc": {"1": "NC (Table 1 / Fig 1 p.2)", "2": "NC (Table 1 / Fig 1 p.2)", "3": "NC (Table 1 / Fig 1 p.2)",
            "7": "NC (Table 1 / Fig 1 p.2)"},
     "group": "sense", "side": "F", "h": 0.6,
     "note": DS_ATE + ": Fig 1 p.2 8-pad UDFN top view (1-3 NC, 4 GND, 5 SDA, 6 SCL, 7 NC, 8 VCC; paddle to GND), UDFN Q4B "
             "2x3x0.55 drawing p.20-21 (D 2.0 along the pin rows, EP 1.5 x 1.3), land C04-23355 p.22 (pads 0.3x0.85 at "
             "C 2.90, centre pad up to 1.6 x 1.4) = stock DFN-8-1EP_3x2mm_P0.5mm_EP1.3x1.5mm (Microchip YNZ UDFN, pad 1 "
             "top-left, 1-4 down the left, 5-8 up the right; pad 9 = paddle). Ordering p.27: MAHDA = UDFN, I2C, blank "
             "(TrustCUSTOM-equivalent, p.13). Address: factory 0xC0 8-bit = 0x60 - NOT in the summary sheet (full sheet is "
             "NDA); from Microchip online docs for the generic ATECC608B. Trust variants differ: TNGTLS 0x35, TFLXTLS 0x36 "
             "(= OV5647 clash), TNGLoRaWAN 0x59 (= SGP41 clash). VCC 2.0-5.5 V. Firmware: the wake pulse (address 0x00) is a "
             "General Call; never follow it with data 06h or PCAL6524/SGP41/SHT40 reset."},
    cap("C517", "100nF", "3V3", "U60", note=DS_ATE + ": VCC bypass"),
]

# ---------------------------------------------------------------- U61 VL53L1CX ToF, 0x29  (back side, under a window)
PARTS += [
    {"ref": "U61", "fp": "Sensor_Distance:ST_VL53L1x", "value": "VL53L1CXV0FY/1", "lcsc": "C190004",
     "pins": {"1": "3V3", "2": "GND", "3": "GND", "4": "GND", "5": "TOF_XSHUT", "6": "GND", "7": "TOF_INT", "9": "I2C_SDA",
              "10": "I2C_SCL", "11": "3V3", "12": "GND"},
     "nc": {"8": "DNC: do not connect, must be left floating (Table 2 p.5)"},
     "group": "sense", "side": "B", "h": 1.56,
     "note": DS_TOF + ": Table 2 + Fig 2 (bottom view) p.5 (1 AVDDVCSEL, 2 AVSSVCSEL, 3 GND, 4 GND2, 5 XSHUT, 6 GND3, 7 GPIO1, "
             "8 DNC, 9 SDA, 10 SCL, 11 AVDD, 12 GND4). Mirrored to top view and turned 90 deg it is the stock ST_VL53L1x "
             "order (1-5 top row, 6 right, 7-11 bottom row, 12 left). AVDD 2.6-3.5 V (Table 14 p.23): 3V3 is fine. I/O: 1V8 "
             "mode at reset, inputs failsafe to 3.6 V; the driver must switch to 2V8 mode (IOVDD = AVDD) for 3.3 V levels "
             "(Table 14 note 3-4). Address 0x52 8-bit = 0x29 (p.19). XSHUT = TOF_XSHUT (U51 P3, held low by its 100k default "
             "pull-down = HW standby until enabled); GPIO1 open drain = TOF_INT (U51 P4) with 10k pull-up (p.6). "
             "Caps 100 nF + 4.7 uF at AVDDVCSEL (Fig 3 p.6). Mounted on the BACK side under a <1.5 mm 940 nm window."},
    cap("C518", "100nF", "3V3", "U61", side="B", note=DS_TOF + " Fig 3 p.6: 100 nF close to AVDDVCSEL/AVSSVCSEL"),
    cap("C519", "4.7uF", "3V3", "U61", side="B", note=DS_TOF + " Fig 3 p.6: 4.7 uF close to AVDDVCSEL/AVSSVCSEL"),
    res("R507", "10k", "TOF_INT", "3V3", "U61", side="B", note=DS_TOF + " p.6: GPIO1 open drain, 10k pull-up recommended"),
]
