"""RF + tools subsystem (CONTRACT.md group "rf"): NFC, 125 kHz RFID, sub-GHz (CC1101 433/868 + SX1262 LoRa EU868),
sub-GHz chip antenna, IR TX/RX, GNSS. Everything on side F, powered from RF_3V3 unless a note says otherwise.

Datasheets used (all read for this file, 2026-11-13; page numbers are the PDF's own page labels):
  ST25R3916B  DS13541 rev 8   https://www.st.com/resource/en/datasheet/st25r3916b.pdf
  CC1101      SWRS061I        https://www.ti.com/lit/ds/symlink/cc1101.pdf
  SX1261/2    DS.SX1261-2.W.APP rev 1.1  https://datasheet.lcsc.com/datasheet/pdf/28cfa981266da05d26af56ac0d14b1fd.pdf
              + AN1200.40 "SX1261/2 Reference Design Explanation" rev 1.1 (E428V03A / E449V01A)
                https://cdn-reichelt.de/documents/datenblatt/A200/SX1262REFERENCE.pdf
  MAX-M10S    UBX-20035208 R08 https://content.u-blox.com/sites/default/files/MAX-M10S_DataSheet_UBX-20035208.pdf
              UBX-20053088 R05 https://content.u-blox.com/sites/default/files/MAX-M10S_IntegrationManual_UBX-20053088.pdf
  PE4259      DOC-03694-5.01  https://www.psemi.com/pdf/datasheets/pe4259ds.pdf
  TLV7011     https://www.ti.com/lit/ds/symlink/tlv7011.pdf ; SN74LVC2G34 https://www.ti.com/lit/ds/symlink/sn74lvc2g34.pdf
  DMG1012T    https://www.diodes.com/assets/Datasheets/ds31783.pdf ; BAT54WS-7-F (Diodes, LCSC C124205 PDF)
  IR12-21C    https://en.everlight.com/wp-content/plugins/ItemRelationship/product_files/pdf/IR12-21C-TR8.pdf
  IRM-H638T   https://www.everlighteurope.com/custom/files/datasheets/DMO-0000008.pdf
  0868AT43A0020 Johanson spec v1.8 (LCSC C3284550 PDF) ; W3011 Pulse spec (LCSC C6604735 PDF)
  SAFFB1G56KB0F0A Murata spec (LCSC C91647 PDF) ; TG2520SMN Epson (LCSC C7527388 PDF) ; YSX321SL YXC (C70591/C15192)
Footprints not in stock KiCad: pcb/gen_rf_pads.py (NFC_ANT_PADS, LF_COIL_PADS, Everlight_IR12-21C, Johanson_0868AT43A0020).

=== Design notes (values + reasoning) =================================================================================
NFC (U30): differential drive, regulators all used (DS fig.2 p.14). Regulator caps 2.2 uF + 10 nF, AGD 1 uF + 10 nF
  (DS p.38). VDD_AM: 22 nF ONLY - DS p.41 "do not insert a 2.2 uF capacitor on VDD_AM when using AWS" (10-50 nF), plus
  1 nF RF decoupling (DS p.39 "100 pF to 2.2 nF"). VDD/VDD_TX from RF_3V3: firmware must set sup3V (IO conf 2) at boot.
  I2C_EN = GND -> SPI mode 1. Crystal 27.12 MHz YSX321SL CL = 20 pF: C = 2 x (20 - ~3 pF stray) = 34 -> 33 pF.
  Antenna network values = ST X-NUCLEO-NFC06A1 (ST25R3916 + ~1 uH-class PCB antenna; databrief schematic p.3,
  https://www.farnell.com/datasheets/2864616.pdf): EMI L 270 nH + C 680 pF, series C 100 pF, parallel 82 pF + 56 pF
  per side to GND, 2R4 damping per side, RFI divider 10 pF / 180 pF. NFC06 also has AAT varactors in parallel with
  the series and parallel caps (they add capacitance); we have no AAT, so a DNP trim footprint sits beside every
  series cap. EVERY matching part: tune with NanoVNA with the Molex antenna in the closed enclosure (ST AN5276/AN5592).
125 kHz (U34/U35/Q300): Flipper-style discrete reader. Flipper Zero firmware furi_hal_rfid.c
  (github.com/flipperdevices/flipperzero-firmware targets/f7/furi_hal/furi_hal_rfid.c): read = timer PWM carrier out
  (TIM1 CH1N) into the coil, envelope into the MCU comparator (COMP1, +in = RFID data, -in = 1/2 VREFINT, high
  hysteresis); emulate = carrier pin held low and the "pull" pin (TIM2) loads the coil; "pull" held low while reading.
  Flipper's RFID schematic PDF is published at docs.flipper.net/zero/development/hardware/schematic but its S3 copy
  refused download (AccessDenied), so the values below are computed here, not copied:
  - Driver: both halves of SN74LVC2G34 from LF_CARRIER, each output through its own 68 R (current sharing).
  - Series LC: L_coil ~0.3 mH (50 turns, to measure) -> C = 1/((2 pi 125 kHz)^2 x 0.3 mH) = 5.40 nF
    -> 4.7 nF + 680 pF C0G 50 V 0603 (5.38 nF) + DNP trim. Re-tune to the measured coil.
  - Current at resonance: fundamental of a 3.3 V square = 4/pi x 1.65 = 2.1 V pk over R = 34 (2x68 || ) + ~6.5
    (driver) + ~5 (coil DCR) = ~46 ohm -> ~46 mA pk total, ~23 mA per buffer (74LVC: 24 mA rated, 50 mA abs max).
    Coil voltage = I x wL = 0.046 x 236 = ~11 V pk -> 50 V C0G, BAT54 (30 V) and DMG1012T (20 V) all fine.
    For more range lower the 68 R to 47 R (~60 mA, ~14 V pk), not below (buffer and Q300 Vds limits).
  - Envelope: capacitive tap 220 pF / 1 nF (ratio 0.18 -> ~2 V pk; tap load 180 pF puts the coil's self-resonance
    near 700 kHz, far above 125 kHz), 100 k DC return, BAT54 peak detector into 2.2 nF || 10 k (tau 22 us: follows
    RF/8 FSK at 15.6 kHz, ~3 carrier periods), then 10 k / 1 nF low-pass (16 kHz) -> LF_FILT.
  - Slicer: TLV7011 compares LF_FILT with its own 10 ms average (100 k / 100 nF) -> LF_DATA (push-pull, 3.3 V).
    TLV7011 has 4.2 mV internal hysteresis (DS elec. char.), so no feedback resistor.
  - Load modulation (emulate): BAT54 + DMG1012T from the coil hot end to GND (half-wave, like ST's EXT_LM
    MOS + diode). The diode keeps the FET body diode from clamping the negative half-cycles while reading.
Sub-GHz (U31 CC1101): TI SWRS061I Fig.10/11 + Table 21 p.25-26 (433 and 868/915 MHz columns). Two TI baluns can NOT
  hang on RF_P/RF_N together: at 868 MHz the 433 network puts C131 = 3.9 pF (-j47 ohm) straight across RF_N, which
  wrecks the 868 match (and vice versa). So the band is switched on the CHIP side by two PE4259 (U37 on RF_P, U38 on
  RF_N, DC-blocked with 100 pF per PE4259 note "RF pins must be DC blocked") and the two balun outputs are combined by
  a third PE4259 (U39) into RF_SUBGHZ, all three on RF_BAND (high = 433, pulled low = 868). Crystal 26 MHz YSX321SL
  CL = 10 pF: C = 2 x (10 - 2.5 pF parasitic, CC1101 DS p.23) = 15 pF. 868 path: LQG15HS multilayer inductors
  used because LQW15 is not stocked (TI note: other inductors per DN032 - re-check harmonics).
  Optional C126/L125 699 MHz trap (TI note) fitted as DNP.
Radio select (U40 PE4259, RF_RADIO high = CC1101 RF_SUBGHZ, pulled low = SX1262) -> RF_ANT_SUBG -> pi -> AE30.
LoRa (U32 SX1262): AN1200.40 E449V01A topology (Fig.10 p.13: TCXO from DIO3 through a ferrite bead, 10 pF DC cut +
  220 R into XTA, XTB open; DS 4.1.4 p.24), DC-DC 15 uH + 470 nF VREG (DS fig 14-2), VDD_IN tied to VBAT (E428/E449),
  TX/RX by PE4259 U41 driven by DIO2 (SetDIO2AsRfSwitchCtrl: DIO2 high in TX -> RF1 = TX).
  Semtech gives the E449 BOM only "upon request"; none of its RF values are public. So:
  - VR_PA decoupling 47 nF + 82 pF and the 47 nH feed: as Heltec WiFi LoRa 32 V3.2 schematic (shipped 868/915 design)
    and DS p.32 ("47 nH").
  - TX chain (L2 C3 L3||C4 C5 C6 L4 C7 in Semtech naming) COMPUTED here: 3-section low-pass + 2nd-harmonic trap
    transforming 50 ohm to an ASSUMED ~12 ohm HP-PA load at 868 MHz. Result 2.2 nH / 6.8 pF / 3.3 nH || 2.4 pF (trap
    1.79 GHz) / 6.8 pF / 47 pF / 10 nH / 2.7 pF: |Zin| 12.6+j0.6 at 868, -0.04 dB 820-915 MHz, 2f0 -42 dB, 3f0 -45 dB,
    worst case with all parts +-5 % -0.15 dB (ideal parts, no PA output capacitance). PLACEHOLDER: replace with the
    Semtech E449V01A/E428V03A BOM before ordering, then verify harmonics on a spectrum analyser.
  - RX balun: L6 15 nH, C12 1.8 pF, C11 2.4 pF (Semtech LoRa forum post quoting the 868 MHz kit BOM, unverified),
    C13 DNP.
  TCXO: Epson TG2520SMN 32 MHz 1.8 V clipped sine (X1G0054210205, C7527388, 2768 at JLC) powered from DIO3 at 1.8 V
  (firmware: SetDIO3AsTCXOCtrl(1.8 V); VBAT >= 2.0 V OK at 3.3 V).
Sub-GHz antenna AE30: Johanson 0868AT43A0020 (858-878 MHz only!). Pi = 0R + 2 DNP (Johanson eval values for a start:
  3.9 pF shunt at the line, 18 nH series, 0.3 pF shunt at the antenna - spec p.1, "client PCB values will differ").
  Ignion NN03-320 (7 x 3 mm, 2 bands, not at JLC) is the better antenna for 433 + 868: consign it and replace this
  footprint if 433 range matters - at 433 MHz the Johanson part is far off resonance (expect 15-20 dB loss).
IR: 2 x IR12-21C, each with its own 47 R from VBAT (VBAT 3.0-4.2 V, VF 1.2-1.5 V -> 37-60 mA each, total ~75-120 mA
  pulses); IR12-21C has NO pulse rating in its datasheet (65 mA continuous abs max), so each LED stays <= 60 mA.
  VBAT (not 3V3) keeps the 38 kHz current pulses off the 3.3 V rail the radios and GNSS share. DMG1012T low side,
  100 R gate + 100 k pull-down (GPIO42 is in the 1.8 V bank at boot; Vth max 1.0 V so it still switches fully).
  RX: IRM-H638T, 100 R + 4.7 uF RC filter (DS p.2: 47-220 R, >= 2.2 uF), output IR_RX (internal pull-up).
GNSS (U33 MAX-M10S): supply option 1 (IM table 42 p.74): VCC = V_IO = 3V3, VIO_SEL open. V_BCKP from 3V3 through a
  BAT54 to a 22 uF MLCC (IM 4.1.3 p.73: avoid series R on V_BCKP; backup current ~28 uA -> the cap only bridges
  short 3V3 dropouts, no supercap is stocked at JLC). I2C at 0x42 (DS p.16 "7-bit I2C address (0x42)"), UART unused
  (open), RESET_N = GNSS_RST (internal pull-up), TIMEPULSE + SAFEBOOT_N to test pads, EXTINT/LNA_EN/VCC_RF open.
  RF: W3011 (pad 1 feed, pad 2 GND per Pulse layout p.5-7) -> pi (0R + 2 DNP; Pulse test board uses 2.2 pF shunt)
  -> SAW footprint Murata SAFFB1G56KB0F0A (DNP) with a fitted 0R bypass -> RF_IN (built-in DC block, IM 4.3 p.77).
  Fit the SAW if LTE/868 MHz TX desense the GNSS (IM 4.3: SAW-LNA-SAW for cellular designs).
Control lines into the PE4259s go through 1 k / 1 nF (Semtech uses 100 R / 1 nF): the RC filters RF leakage and the
  1 k limits clamp current when the expander drives 3.3 V into a switch whose RF_3V3 is off (PE4259 abs max on a
  control pin is VDD + 0.3 V): firmware should still drive RF_BAND/RF_RADIO low before cutting RF_3V3.
  CS lines have 100 k pull-ups to RF_3V3 so no radio is selected while the P4's GPIO48/50/51 float at boot.

=== Nets made up in this file (all local to sch_rf.py) ================================================================
NFC_*, LF_DRV*, LF_TAP, LF_ENV, LF_FILT, LF_REF, LF_LM, LF_PULL_G, CC_*, CC433_*, CC868_*, RF_BAND_F, RF_RADIO_F,
RF_SUBGHZ, RF_ANT_SUBG, ANT_SUBG_FEED, LORA_* (except LORA_CS/DIO1/BUSY/RST), IR_A1/IR_A2/IR_K/IR_TX_G/IR_VCC,
GNSS_VBCKP, GNSS_ANT, GNSS_SAW_IN, GNSS_RF_IN, GNSS_TP, GNSS_SAFEBOOT.
Nets shared with the rest of the board: RF_3V3, 3V3, VBAT, GND, SPI_SCK, SPI_MOSI, SPI_MISO, NFC_CS, NFC_IRQ, CC_CS,
CC_GDO0, LORA_CS, LORA_DIO1, LORA_BUSY, LORA_RST, RF_BAND, RF_RADIO, LF_CARRIER, LF_PULL, LF_DATA, IR_TX, IR_RX,
I2C_SDA, I2C_SCL, GNSS_RST.

=== Ref range note ====================================================================================================
CONTRACT gives this group U30-U39. The design needs 13 ICs/modules (5 x PE4259). U40, U41 (PE4259) and U42 (SAW, DNP)
are outside the range; no other group owns U40-U49. Needs Louis's / the integrator's OK, or renumber.
"""

PARTS = []

C04 = "Capacitor_SMD:C_0402_1005Metric"
C06 = "Capacitor_SMD:C_0603_1608Metric"
C08 = "Capacitor_SMD:C_0805_2012Metric"
R04 = "Resistor_SMD:R_0402_1005Metric"
R06 = "Resistor_SMD:R_0603_1608Metric"
L04 = "Inductor_SMD:L_0402_1005Metric"
L06 = "Inductor_SMD:L_0603_1608Metric"
L08 = "Inductor_SMD:L_0805_2012Metric"
SC70_6 = "Package_TO_SOT_SMD:SOT-363_SC-70-6"

# value -> (LCSC, footprint, height) ; every number checked on jlcpcb.com parts API 2026-11-13
CAP = {
    "1.0pF": ("C1550", C04), "1.5pF": ("C1552", C04), "1.8pF": ("C1553", C04), "2.4pF": ("C48346", C04),
    "2.7pF": ("C1561", C04), "3.3pF": ("C1565", C04), "3.9pF": ("C1566", C04), "5.6pF": ("C1574", C04),
    "6.8pF": ("C1576", C04), "8.2pF": ("C1579", C04), "10pF": ("C1545", C04), "12pF": ("C1547", C04),
    "15pF": ("C1548", C04), "33pF": ("C1562", C04), "47pF": ("C1567", C04), "56pF": ("C1572", C04),
    "82pF": ("C45501", C04), "100pF": ("C1546", C04), "180pF": ("C97862", C04), "220pF": ("C39122", C04),
    "680pF": ("C301953", C04), "1nF C0G": ("C53547", C04), "2.2nF C0G": ("C385029", C04), "1nF": ("C1523", C04),
    "10nF": ("C15195", C04), "22nF": ("C1532", C04), "47nF": ("C82219", C04), "100nF": ("C1525", C04),
    "470nF": ("C5137475", C04), "1uF": ("C52923", C04), "2.2uF": ("C12530", C04), "4.7uF": ("C23733", C04),
    "10uF": ("C19702", C06), "22uF": ("C45783", C08),
    "4.7nF C0G 50V": ("C85980", C06), "680pF C0G 50V": ("C327426", C06),
    "3.9nF C0G 50V": ("C415537", C06), "150pF C0G 50V": ("C1645", C06),
}
RES = {"0R": ("C17168", R04), "68R": ("C25131", R04), "100R": ("C25076", R04), "220R": ("C25091", R04),
       "1k": ("C11702", R04), "10k": ("C25744", R04), "56k 1%": ("C25796", R04), "100k": ("C25741", R04),
       "2.4R 0603": ("C22941", R06), "47R 0603": ("C23182", R06)}
IND = {"2.2nH": ("C86061", L04, "LQG15HS2N2S02D"), "3.3nH": ("C86064", L04, "LQG15HS3N3S02D"),
       "10nH": ("C77103", L04, "LQG15HS10NJ02D"), "12nH": ("C77104", L04, "LQG15HS12NJ02D"),
       "15nH": ("C86059", L04, "LQG15HS15NJ02D"), "18nH": ("C86060", L04, "LQG15HS18NJ02D"),
       "22nH": ("C12670", L04, "LQG15HS22NJ02D"), "27nH": ("C12669", L04, "LQG15HS27NJ02D"),
       "47nH": ("C97998", L04, "LQG15HS47NJ02D"), "270nH": ("C162661", L08, "LQW2BASR27J00L 350mA"),
       "15uH": ("C486329", L06, "MGFL1608F150MT-LF 220mA"), "FB600": ("C76884", L04, "BLM15AG601SN1D 600R@100MHz")}
H = {C04: 0.55, R04: 0.4, L04: 0.55, C06: 0.95, R06: 0.55, L06: 1.0, C08: 1.35, L08: 1.2}

_n = {"C": 300, "R": 300, "L": 300}
_lim = {"C": 399, "R": 399, "L": 399}
TUNE = "tune with NanoVNA"


def _ref(k):
    r = f"{k}{_n[k]}"
    assert _n[k] <= _lim[k], f"{k} range exhausted"
    _n[k] += 1
    return r


def add(ref, fp, value, lcsc, pins, group, near=None, h=1.0, note="", nc=None, dnp=False):
    p = {"ref": ref, "fp": fp, "value": value, "lcsc": lcsc, "pins": pins, "group": "rf", "side": "F", "h": h,
         "note": f"[{group}] {note}".strip()}
    if near:
        p["near"] = near
    if nc:
        p["nc"] = nc
    if dnp:
        p["dnp"] = True
    PARTS.append(p)
    return ref


def cap(val, a, b, near, group, note="", dnp=False, tune=False):
    lc, fp = CAP[val.split(" DNP")[0]] if not dnp else ("", C04)
    n = (TUNE + "; " if tune else "") + note
    if dnp:
        n = "DNP (not placed): " + n
    return add(_ref("C"), fp, ("DNP " if dnp else "") + val, lc, {"1": a, "2": b}, group, near, H[fp], n, dnp=dnp)


def res(val, a, b, near, group, note="", tune=False):
    lc, fp = RES[val]
    return add(_ref("R"), fp, val.split(" ")[0], lc, {"1": a, "2": b}, group, near, H[fp],
               (TUNE + "; " if tune else "") + note)


def ind(val, a, b, near, group, note="", dnp=False, tune=False):
    lc, fp, mpn = IND[val]
    n = f"{mpn}; " + (TUNE + "; " if tune else "") + note
    if dnp:
        lc, n = "", "DNP (not placed): " + n
    return add(_ref("L"), fp, ("DNP " if dnp else "") + val, lc, {"1": a, "2": b}, group, near, H[fp], n, dnp=dnp)


# ======================================================================================================================
# 1. NFC  ST25R3916B-AQET (UFQFPN-32 5x5, EP 3.5 mm; ST footprint example fig.41 p.159 = EP 3.45, pads 0.30 x 0.75)
# ======================================================================================================================
G = "nfc"
add("U30", "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm", "ST25R3916B-AQET", "C17315217", {
    "1": "RF_3V3",        # VDD_IO
    "3": "NFC_VDD_D", "4": "NFC_XTO", "5": "NFC_XTI", "6": "GND",       # GND_D
    "7": "NFC_VDD_A", "8": "RF_3V3",                                    # VDD
    "9": "NFC_VDD_RF", "10": "RF_3V3",                                  # VDD_TX
    "11": "NFC_VDD_AM", "12": "GND",                                    # GND_DR1
    "13": "NFC_RFO1", "14": "NFC_VDD_RF",                               # VDD_DR tied to VDD_RF (fig.2)
    "15": "NFC_RFO2", "16": "GND",                                      # GND_DR2
    "20": "GND",                                                        # I2C_EN low = SPI
    "21": "GND",                                                        # VSS
    "22": "NFC_RFI1", "23": "NFC_RFI2", "24": "NFC_AGD", "26": "GND",   # GND_A
    "27": "NFC_IRQ", "29": "NFC_CS", "30": "SPI_SCK", "31": "SPI_MOSI", "32": "SPI_MISO",
    "33": "GND"},                                                       # exposed pad
    G, h=0.6, nc={"2": "TAD1 test output (DS table 2)", "17": "EXT_LM: only for external MOS load modulation (unused)",
                  "18": "AAT_A: no automatic antenna tuning varactors", "19": "AAT_B: no AAT varactors",
                  "25": "TAD2 test output", "28": "MCU_CLK clock output not used"},
    note="DS13541 rev 8 table 2 p.20-21 (VFQFPN32/UFQFPN32 numbering, pad 33 = exposed pad GND); fig.2 p.14 "
         "differential minimum system. SPI mode 1, max 10 MHz. VDD 3.3 V mode: set sup3V after power-up.")
cap("100nF", "RF_3V3", "GND", "U30", G, "VDD_IO pin 1")
cap("2.2uF", "RF_3V3", "GND", "U30", G, "VDD pin 8")
cap("10nF", "RF_3V3", "GND", "U30", G, "VDD pin 8")
cap("4.7uF", "RF_3V3", "GND", "U30", G, "VDD_TX pin 10 (driver current up to ~250 mA; NFC06 uses 4u7)")
cap("10nF", "RF_3V3", "GND", "U30", G, "VDD_TX pin 10")
for net, why in (("NFC_VDD_D", "VDD_D reg pin 3"), ("NFC_VDD_A", "VDD_A reg pin 7"), ("NFC_VDD_RF", "VDD_RF/VDD_DR pins 9/14")):
    cap("2.2uF", net, "GND", "U30", G, why + " (DS p.38: 2.2 uF || 10 nF)")
    cap("10nF", net, "GND", "U30", G, why)
cap("22nF", "NFC_VDD_AM", "GND", "U30", G, "VDD_AM pin 11, AWS mode: 10-50 nF, NO 2.2 uF (DS p.41)")
cap("1nF", "NFC_VDD_AM", "GND", "U30", G, "VDD_AM RF decoupling 100 pF-2.2 nF (DS p.39)")
cap("1uF", "NFC_AGD", "GND", "U30", G, "AGDC pin 24 (DS p.38: 1 uF || 10 nF)")
cap("10nF", "NFC_AGD", "GND", "U30", G, "AGDC pin 24")
add("Y30", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", "27.12MHz X32252712MSB4SI", "C70591",
    {"1": "NFC_XTI", "3": "NFC_XTO", "2": "GND", "4": "GND"}, G, "U30", 0.8,
    "YXC YSX321SL 27.12 MHz CL 20 pF +-10 ppm; pads 1/3 crystal, 2/4 GND (YXC datasheet p.1 'Top View Crystal Connection')")
cap("33pF", "NFC_XTI", "GND", "Y30", G, "load cap: 2 x (CL 20 pF - ~3 pF stray)")
cap("33pF", "NFC_XTO", "GND", "Y30", G, "load cap")
# antenna network, two mirrored halves (X-NUCLEO-NFC06A1 values; series/parallel get trim footprints)
for s in ("1", "2"):
    ind("270nH", f"NFC_RFO{s}", f"NFC_EMI{s}", "U30", G, "EMI filter L (NFC06 L300/L301 270 nH; 350 mA rated)", tune=True)
    cap("680pF", f"NFC_EMI{s}", "GND", "U30", G, "EMI filter C (NFC06 C305/C308)", tune=True)
    cap("100pF", f"NFC_EMI{s}", f"NFC_M{s}", "U30", G, "series matching C (NFC06 C303/C310)", tune=True)
    cap("10pF", f"NFC_EMI{s}", f"NFC_M{s}", "U30", G, "series trim, parallel to the series C (stands in for NFC06's AAT varactor)", dnp=True, tune=True)
    cap("82pF", f"NFC_M{s}", "GND", "J30", G, "parallel matching C (NFC06 C315/C316)", tune=True)
    cap("56pF", f"NFC_M{s}", "GND", "J30", G, "parallel matching C (NFC06 C306/C309)", tune=True)
    res("2.4R 0603", f"NFC_M{s}", f"NFC_ANT{s}", "J30", G, "antenna Q damping (NFC06 R300/R302 2R4); 0603 for ~0.1 W", tune=True)
    cap("10pF", f"NFC_M{s}", f"NFC_RFI{s}", "U30", G, "RFI divider top (NFC06 C301/C312)", tune=True)
    cap("180pF", f"NFC_RFI{s}", "GND", "U30", G, "RFI divider bottom (NFC06 C300/C313)", tune=True)
add("J30", "phone:Pogo_KTR47003_D2.0", "BWCD-L5.5W2.0H3.0", "C2826550", {"1": "NFC_ANT1"}, G, "U30", 4.8,
    "NFC antenna contact 1: SMD pogo pin pressing the Molex 1462360111 antenna tab (2.5 mm pitch, drawing 146236 rev H). "
    "BAT Wireless BWCD-L5.5W2.0H3.0 (drawing Aug-21-2025-A01): free 5.5 +-0.1, base 2.0, barrel 4.0, plunger 0.9 with "
    "1.5 exposed, 70 g at working height (not dimensioned: ~4.8 used). Board to tab 4.83 mm in the 15.5 mm body "
    "(fit_check.py), 0.67 mm into the 1.5 mm stroke. Same 2.0 base as the old KTR47003, so the pad stays. "
    "Antenna (C17350773) is stuck under the front plate by hand. h = working height (fit_check TOUCH).")
add("J35", "phone:Pogo_KTR47003_D2.0", "BWCD-L5.5W2.0H3.0", "C2826550", {"1": "NFC_ANT2"}, G, "J30", 4.8,
    "NFC antenna contact 2, 2.5 mm from J30 (antenna tab pitch). Same part as J30.")

# ======================================================================================================================
# 2. 125 kHz RFID (Flipper-style discrete)
# ======================================================================================================================
G = "lf125"
add("U34", SC70_6, "SN74LVC2G34DCKR", "C14461", {
    "1": "LF_CARRIER", "2": "GND", "3": "LF_CARRIER", "4": "LF_DRV2", "5": "RF_3V3", "6": "LF_DRV1"}, G, "J31", 1.1,
    note="TI SN74LVC2G34 pin functions p.3 (1 1A, 2 GND, 3 2A, 4 2Y, 5 VCC, 6 1Y). Both buffers driven together, each "
         "output through its own 68 R. Stocked TI part used instead of C52140488 (MDD clone, same pinout). Ioff: input "
         "safe while RF_3V3 is off. GPIO40 is in the 1.8 V bank: firmware must set VO4 = 3.3 V before reading.")
cap("100nF", "RF_3V3", "GND", "U34", G, "U34 VCC")
res("68R", "LF_DRV1", "LF_DRV", "U34", G, "drive current limit, ~23 mA per buffer at resonance (see header)", tune=True)
res("68R", "LF_DRV2", "LF_DRV", "U34", G, "drive current limit, 2nd buffer", tune=True)
cap("3.9nF C0G 50V", "LF_DRV", "LF_COIL1", "J31", G, "series resonance C (3.9n + 150p = 4.05 nF for the 0.40 mH Coilcraft 4308RV-404 at 125 kHz = its datasheet matching C); ~14 V pk across", tune=True)
cap("150pF C0G 50V", "LF_DRV", "LF_COIL1", "J31", G, "series resonance C, part 2", tune=True)
add(_ref("C"), C06, "DNP 220pF C0G 50V", "", {"1": "LF_DRV", "2": "LF_COIL1"}, G, "J31", H[C06],
    "DNP (not placed): resonance trim, fit after measuring the coil; " + TUNE, dnp=True)
add("J31", "phone:Coilcraft_4308RV", "4308RV-404XJL", "", {"1": "LF_COIL1", "2": "LF_COIL2"}, G, "U34", 2.74,
    "Coilcraft 4308RV-404XJL 125 kHz ferrite-rod coil, 0.40 mH +-5 %, Q 26 min, DCR 7.1, SRF 5 MHz, 11.43 x 3.15 x 2.74 "
    "(Doc 324-1/-2). Replaces the hand-wound coil (2026-11-14 night: no hand soldering). Not stocked at JLC: buy from "
    "Coilcraft and consign it to JLC with U1. Reads off the rod ends: no copper within 1 mm of the ends (rule area). "
    "Coil at ~46 mA: ~14 V pk, fine for the 50 V C0G series C, BAT54 and DMG1012T.")
res("0R", "LF_COIL2", "GND", "J31", G, "coil cold end to GND (0R so the coil return can be opened for measurement)")
cap("220pF", "LF_COIL1", "LF_TAP", "J31", G, "capacitive tap top (50 V C0G); ratio 0.18 -> ~2 V pk", tune=True)
cap("1nF C0G", "LF_TAP", "GND", "D300", G, "capacitive tap bottom", tune=True)
res("100k", "LF_TAP", "GND", "D300", G, "tap DC return")
add("D300", "Diode_SMD:D_SOD-323", "BAT54WS", "C124205", {"1": "LF_ENV", "2": "LF_TAP"}, G, "U35", 1.1,
    "envelope detector. Diodes BAT54WS-7-F datasheet p.1: SOD-323, cathode band = pad 1 (KiCad D_SOD-323 pad 1 = K)")
cap("2.2nF C0G", "LF_ENV", "GND", "D300", G, "peak hold, tau 22 us with 10 k", tune=True)
res("10k", "LF_ENV", "GND", "D300", G, "peak detector discharge", tune=True)
res("10k", "LF_ENV", "LF_FILT", "U35", G, "carrier ripple low-pass 16 kHz")
cap("1nF C0G", "LF_FILT", "GND", "U35", G, "carrier ripple low-pass 16 kHz")
res("100k", "LF_FILT", "LF_REF", "U35", G, "slicer reference = 10 ms average of the envelope")
cap("100nF", "LF_REF", "GND", "U35", G, "slicer reference averaging")
add("U35", "Package_TO_SOT_SMD:SOT-353_SC-70-5", "TLV7011DCKR", "C193688", {
    "1": "LF_DATA", "2": "GND", "3": "LF_FILT", "4": "LF_REF", "5": "RF_3V3"}, G, "D300", 1.1,
    note="TI TLV7011 Pin Functions p.4 (DCK SC70: 1 OUT, 2 VEE, 3 IN+, 4 IN-, 5 VCC), push-pull, 4.2 mV internal hysteresis. "
         "LF_DATA -> GPIO26 (RMT capture).")
cap("100nF", "RF_3V3", "GND", "U35", G, "U35 VCC")
add("D301", "Diode_SMD:D_SOD-323", "BAT54WS", "C124205", {"1": "LF_LM", "2": "LF_COIL1"}, G, "Q300", 1.1,
    "load-modulation diode (blocks the FET body diode on negative half-cycles while reading)")
add("Q300", "Package_TO_SOT_SMD:SOT-523", "DMG1012T-7", "C20512", {"1": "LF_PULL_G", "2": "GND", "3": "LF_LM"}, G, "J31", 0.8,
    "emulate load modulation. Diodes DS31783 p.1 top view: 1 G, 2 S, 3 D. Vds 20 V max vs ~11 V coil peak.")
res("100R", "LF_PULL", "LF_PULL_G", "Q300", G, "gate series R")
res("100k", "LF_PULL_G", "GND", "Q300", G, "gate pull-down: FET off while GPIO41 floats / RF_3V3 off")

# ======================================================================================================================
# 3. Sub-GHz CC1101 + band switching
# ======================================================================================================================
G = "subghz"
add("U31", "Package_DFN_QFN:Texas_RGP0020H_VQFN-20-1EP_4x4mm_P0.5mm_EP2.4x2.4mm", "CC1101RGPR", "C29953", {
    "1": "SPI_SCK", "2": "SPI_MISO", "3": "CC_GDO2", "4": "RF_3V3", "5": "CC_DCOUPL", "6": "CC_GDO0", "7": "CC_CS",
    "8": "CC_XOSC1", "9": "RF_3V3", "10": "CC_XOSC2", "11": "RF_3V3", "12": "CC_RFP", "13": "CC_RFN",
    "14": "RF_3V3", "15": "RF_3V3", "16": "GND", "17": "CC_RBIAS", "18": "RF_3V3", "19": "GND", "20": "SPI_MOSI",
    "21": "GND"}, G, h=1.0,
    note="TI SWRS061I table 19 p.21 (1 SCLK, 2 SO/GDO1, 3 GDO2, 4 DVDD, 5 DCOUPL, 6 GDO0, 7 CSn, 8 XOSC_Q1, 9/11/14/15 "
         "AVDD, 10 XOSC_Q2, 12 RF_P, 13 RF_N, 16 GND, 17 RBIAS, 18 DGUARD, 19 GND, 20 SI; die pad = GND, pad 21). "
         "RGP0020H/RGP0020C both EP 2.4 mm (package addendum). SO is tri-stated while CSn high (IOCFG1 default).")
cap("100nF", "RF_3V3", "GND", "U31", G, "DVDD pin 4")
cap("100nF", "CC_DCOUPL", "GND", "U31", G, "DCOUPL pin 5 (C51 100 nF, Table 21); never load this pin")
for p in ("9", "11", "14", "15"):
    cap("100nF", "RF_3V3", "GND", "U31", G, f"AVDD pin {p}, own via to GND (DS 7.8)")
cap("100nF", "RF_3V3", "GND", "U31", G, "DGUARD pin 18")
cap("10uF", "RF_3V3", "GND", "U31", G, "bulk for CC1101 + switches")
res("56k 1%", "CC_RBIAS", "GND", "U31", G, "R171 56 k 1 % (Table 21)")
add("Y31", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", "26MHz X322526MMB4SI", "C15192",
    {"1": "CC_XOSC1", "3": "CC_XOSC2", "2": "GND", "4": "GND"}, G, "U31", 0.8,
    "YXC YSX321SL 26 MHz CL 10 pF +-10 ppm; 1/3 crystal, 2/4 GND (YXC datasheet p.1)")
cap("15pF", "CC_XOSC1", "GND", "Y31", G, "C81: 2 x (CL 10 pF - 2.5 pF parasitic, DS p.23)")
cap("15pF", "CC_XOSC2", "GND", "Y31", G, "C101")
add("J32", "TestPoint:TestPoint_Pad_D1.0mm", "TP CC_GDO2", "", {"1": "CC_GDO2"}, G, "U31", 0.1,
    "test pad: CC1101 GDO2 (raw RX data / clock out for debugging); not placed")
res("100k", "CC_CS", "RF_3V3", "U31", G, "CSn pull-up: deselected while GPIO51 floats at boot")

PE_NOTE = ("pSemi PE4259 DOC-03694-5.01 table 7 p.11 (1 RF1, 2 GND, 3 RF2, 4 CTRL, 5 RFC, 6 VDD); single-pin mode "
           "(pin 6 = VDD) table 5 p.5: CTRL high = RFC-RF1, low = RFC-RF2. RF pins DC-blocked or at 0 V.")
# control RC filters (shared)
res("1k", "RF_BAND", "RF_BAND_F", "U39", G, "RF_BAND filter + clamp-current limit (Semtech uses 100R/1nF)")
cap("1nF", "RF_BAND_F", "GND", "U39", G, "RF_BAND filter")
res("100k", "RF_BAND_F", "GND", "U39", G, "default = 868 MHz path while the expander pin is an input")
res("1k", "RF_RADIO", "RF_RADIO_F", "U40", G, "RF_RADIO filter")
cap("1nF", "RF_RADIO_F", "GND", "U40", G, "RF_RADIO filter")
res("100k", "RF_RADIO_F", "GND", "U40", G, "default = SX1262 (LoRa) on the antenna")
# chip-side band switches
cap("100pF", "CC_RFP", "CC_RFP_SW", "U37", G, "DC block RF_P -> U37 RFC (PE4259 note)")
cap("100pF", "CC_RFN", "CC_RFN_SW", "U38", G, "DC block RF_N -> U38 RFC")
add("U37", SC70_6, "PE4259-63", "C470892", {"1": "CC433_P", "2": "GND", "3": "CC868_P", "4": "RF_BAND_F",
    "5": "CC_RFP_SW", "6": "RF_3V3"}, G, "U31", 1.1, "CC1101 RF_P band switch. " + PE_NOTE)
add("U38", SC70_6, "PE4259-63", "C470892", {"1": "CC433_N", "2": "GND", "3": "CC868_N", "4": "RF_BAND_F",
    "5": "CC_RFN_SW", "6": "RF_3V3"}, G, "U31", 1.1, "CC1101 RF_N band switch. " + PE_NOTE)
cap("100nF", "RF_3V3", "GND", "U37", G, "U37/U38 VDD")
# 433 MHz balun + LC filter (TI fig.10, table 21 433 column)
cap("3.9pF", "CC433_P", "CC433_X", "U37", G, "C121 433", tune=True)
ind("27nH", "CC433_P", "CC433_B", "U37", G, "L121 433", tune=True)
cap("220pF", "CC433_B", "GND", "U37", G, "C124 433", tune=True)
ind("27nH", "CC433_N", "CC433_X", "U38", G, "L131 433", tune=True)
cap("3.9pF", "CC433_N", "GND", "U38", G, "C131 433", tune=True)
ind("22nH", "CC433_X", "CC433_F1", "U39", G, "L122 433", tune=True)
cap("8.2pF", "CC433_F1", "GND", "U39", G, "C122 433", tune=True)
ind("27nH", "CC433_F1", "CC433_F2", "U39", G, "L123 433", tune=True)
cap("5.6pF", "CC433_F2", "GND", "U39", G, "C123 433", tune=True)
cap("220pF", "CC433_F2", "CC433_OUT", "U39", G, "C125 433 (DC block toward U39 RF1)", tune=True)
# 868 MHz balun + LC filter (TI fig.11, table 21 868/915 column)
ind("12nH", "CC868_P", "CC868_A", "U37", G, "L121 868", tune=True)
ind("12nH", "CC868_N", "CC868_B", "U38", G, "L131 868", tune=True)
cap("1.0pF", "CC868_A", "CC868_B", "U37", G, "C121 868", tune=True)
cap("1.5pF", "CC868_B", "GND", "U38", G, "C131 868", tune=True)
ind("18nH", "CC868_B", "CC868_X", "U38", G, "L132 868", tune=True)
ind("18nH", "CC868_A", "CC868_C", "U37", G, "L122 868", tune=True)
cap("100pF", "CC868_C", "GND", "U37", G, "C124 868", tune=True)
cap("1.5pF", "CC868_A", "CC868_X", "U37", G, "C122 868", tune=True)
ind("12nH", "CC868_X", "CC868_F", "U39", G, "L123 868", tune=True)
cap("3.3pF", "CC868_F", "GND", "U39", G, "C123 868", tune=True)
ind("12nH", "CC868_F", "CC868_G", "U39", G, "L124 868", tune=True)
cap("12pF", "CC868_G", "CC868_OUT", "U39", G, "C125 868 (DC block toward U39 RF2)", tune=True)
cap("47pF", "CC868_G", "CC868_H", "U39", G, "C126 868: optional 699 MHz trap (TI fig.11 note)", dnp=True, tune=True)
ind("3.3nH", "CC868_H", "CC868_OUT", "U39", G, "L125 868: optional 699 MHz trap", dnp=True, tune=True)
add("U39", SC70_6, "PE4259-63", "C470892", {"1": "CC433_OUT", "2": "GND", "3": "CC868_OUT", "4": "RF_BAND_F",
    "5": "RF_SUBGHZ", "6": "RF_3V3"}, G, "U40", 1.1, "CC1101 band combiner -> RF_SUBGHZ. " + PE_NOTE)
add("U40", SC70_6, "PE4259-63", "C470892", {"1": "RF_SUBGHZ", "2": "GND", "3": "LORA_RF", "4": "RF_RADIO_F",
    "5": "RF_ANT_SUBG", "6": "RF_3V3"}, G, "AE30", 1.1,
    "Radio select: RF_RADIO high = CC1101, low = SX1262 -> RF_ANT_SUBG. REF OUTSIDE U30-39 (see header). " + PE_NOTE)
cap("100nF", "RF_3V3", "GND", "U40", G, "U39/U40 VDD")

# ======================================================================================================================
# 5. Sub-GHz antenna (Johanson 0868AT43A0020) + pi
# ======================================================================================================================
G = "subghz-ant"
cap("3.9pF", "RF_ANT_SUBG", "GND", "AE30", G, "pi shunt, line side (Johanson eval: 3.9 pF)", dnp=True, tune=True)
res("0R", "RF_ANT_SUBG", "ANT_SUBG_FEED", "AE30", G, "pi series (Johanson eval: 18 nH)", tune=True)
cap("0.3pF", "ANT_SUBG_FEED", "GND", "AE30", G, "pi shunt, antenna side (Johanson eval: 0.3 pF)", dnp=True, tune=True)
add("AE30", "phone:Johanson_0868AT43A0020", "0868AT43A0020E", "C3284550", {"1": "ANT_SUBG_FEED"}, G, "U40", 0.9,
    "Johanson 0868AT43A0020 spec v1.8 p.1: terminal 1 feeding point, 2 NC (carries the tuning stub). 858-878 MHz only. "
    "Board corner, ~11 x 10 mm free of copper on all layers (p.3), TOP end of the phone. Alternative: Ignion NN03-320 "
    "(433+868, consign).",
    nc={"2": "NC per Johanson (terminal 2 + stub copper are part of the radiator)"})

# ======================================================================================================================
# 4. LoRa SX1262 (QFN-24 4x4, EP 2.7 per Semtech land pattern fig.15-3 p.102)
# ======================================================================================================================
G = "lora"
add("U32", "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm", "SX1262IMLTRT", "C191341", {
    "1": "RF_3V3", "2": "GND", "3": "LORA_XTA", "5": "GND", "6": "LORA_DIO3", "7": "LORA_VREG", "8": "GND",
    "9": "LORA_DCC", "10": "RF_3V3", "11": "RF_3V3", "12": "LORA_DIO2", "13": "LORA_DIO1", "14": "LORA_BUSY",
    "15": "LORA_RST", "16": "SPI_MISO", "17": "SPI_MOSI", "18": "SPI_SCK", "19": "LORA_CS", "20": "GND",
    "21": "LORA_RFIP", "22": "LORA_RFIN", "23": "LORA_RFO", "24": "LORA_VRPA", "25": "GND"}, G, h=0.9,
    nc={"4": "XTB left open with a TCXO (DS 4.1.4 p.24)"},
    note="Semtech DS.SX1261-2.W.APP rev 1.1 table 2-1 p.12 (1 VDD_IN, 2 GND, 3 XTA, 4 XTB, 5 GND, 6 DIO3, 7 VREG, "
         "8 GND, 9 DCC_SW, 10 VBAT, 11 VBAT_IO, 12 DIO2, 13 DIO1, 14 BUSY, 15 NRESET, 16 MISO, 17 MOSI, 18 SCK, 19 NSS, "
         "20 GND, 21 RFI_P, 22 RFI_N, 23 RFO, 24 VR_PA, 0/EP GND). VDD_IN on VBAT as in SX1262 refs E428/E449. "
         "TX +22 dBm draws ~118 mA from RF_3V3. EU868: +14 dBm ERP max in most sub-bands, +27 dBm only 869.4-869.65.")
cap("100nF", "RF_3V3", "GND", "U32", G, "VDD_IN pin 1 (C16)")
cap("100nF", "RF_3V3", "GND", "U32", G, "VBAT/VBAT_IO pins 10/11 (C18)")
cap("10uF", "RF_3V3", "GND", "U32", G, "bulk for 120 mA TX bursts")
ind("15uH", "LORA_DCC", "LORA_VREG", "U32", G, "L7 DC-DC inductor DCC_SW -> VREG (DS fig.14-2); core only, few mA")
cap("470nF", "LORA_VREG", "GND", "U32", G, "C17 VREG (DS fig.14-2)")
cap("47nF", "LORA_VRPA", "GND", "U32", G, "C2 VR_PA (Heltec V3.2: 47 nF)")
cap("82pF", "LORA_VRPA", "GND", "U32", G, "C1 VR_PA RF decoupling (Heltec V3.2: 82 pF)")
ind("47nH", "LORA_VRPA", "LORA_PA", "U32", G, "L1 PA feed VR_PA -> RFO node (DS p.32 '47 nH')")
ind("2.2nH", "LORA_RFO", "LORA_PA", "U32", G, "L2 (computed, assumed 12 ohm PA load; replace with Semtech BOM)", tune=True)
cap("6.8pF", "LORA_PA", "GND", "U32", G, "C3 (computed)", tune=True)
ind("3.3nH", "LORA_PA", "LORA_TX1", "U41", G, "L3, with C4 = 2nd-harmonic trap 1.79 GHz (computed)", tune=True)
cap("2.4pF", "LORA_PA", "LORA_TX1", "U41", G, "C4 trap (computed)", tune=True)
cap("6.8pF", "LORA_TX1", "GND", "U41", G, "C5 (computed)", tune=True)
cap("47pF", "LORA_TX1", "LORA_TX2", "U41", G, "C6 DC block (computed)", tune=True)
ind("10nH", "LORA_TX2", "LORA_TX", "U41", G, "L4 (computed)", tune=True)
cap("2.7pF", "LORA_TX", "GND", "U41", G, "C7 (computed)", tune=True)
ind("15nH", "LORA_RFIN", "LORA_RFIP", "U32", G, "L6 RX balun (868 kit BOM per Semtech forum, unverified)", tune=True)
cap("1.8pF", "LORA_RFIP", "GND", "U32", G, "C12 RX balun (unverified)", tune=True)
cap("2.4pF", "LORA_RFIN", "LORA_RX", "U41", G, "C11 RX balun + DC block (unverified)", tune=True)
cap("1.0pF", "LORA_RX", "GND", "U41", G, "C13 RX match", dnp=True, tune=True)
res("100R", "LORA_DIO2", "LORA_DIO2_F", "U41", G, "R3 DIO2 -> switch CTRL (Semtech 100R/1nF)")
cap("1nF", "LORA_DIO2_F", "GND", "U41", G, "C15")
add("U41", SC70_6, "PE4259-63", "C470892", {"1": "LORA_TX", "2": "GND", "3": "LORA_RX", "4": "LORA_DIO2_F",
    "5": "LORA_RF", "6": "RF_3V3"}, G, "U32", 1.1,
    "SX1262 TX/RX switch, CTRL = DIO2 (high in TX -> RF1 = TX), as Semtech fig.14-2. REF OUTSIDE U30-39. " + PE_NOTE)
cap("100nF", "RF_3V3", "GND", "U41", G, "U41 VDD")
add("Y32", "Oscillator:Oscillator_SMD_SeikoEpson_TG2520SMN-xxx-xxxxxx-4Pin_2.5x2.0mm", "TCXO 32MHz 1.8V TG2520SMN",
    "C7527388", {"2": "GND", "3": "LORA_TCXO_OUT", "4": "LORA_TCXO_VCC"}, G, "U32", 0.8,
    "Epson X1G0054210205 = TG2520SMN 32 MHz, 1.8 V (1.7-1.9 V), clipped sine >= 0.8 Vpp, 1.8 mA, +-0.5 ppm; pin "
    "information: 1 NC (TCXO), 2 GND, 3 OUT, 4 VCC; needs external DC cut (Epson note). Keep away from the PA (heat).",
    nc={"1": "N.C. on the TCXO version (Vc only on VC-TCXO)"})
ind("FB600", "LORA_DIO3", "LORA_TCXO_VCC", "Y32", G, "FB1 ferrite bead DIO3 -> TCXO VCC (AN1200.40 fig.10 E449V01A)")
cap("100nF", "LORA_TCXO_VCC", "GND", "Y32", G, "TCXO supply cap (DS fig.4-2: 100 nF)")
cap("10pF", "LORA_TCXO_OUT", "LORA_TCXO_AC", "Y32", G, "DC-cut 10 pF (DS 4.1.4)")
res("220R", "LORA_TCXO_AC", "LORA_XTA", "U32", G, "220 R series into XTA (DS 4.1.4)")
res("100k", "LORA_CS", "RF_3V3", "U32", G, "NSS pull-up: deselected while GPIO48 floats at boot")

# ======================================================================================================================
# 6. IR
# ======================================================================================================================
G = "ir"
res("47R 0603", "VBAT", "IR_A1", "D303", G, "LED 1 current: (VBAT - 1.4 V)/47 = 34-60 mA (<= 65 mA abs max)")
res("47R 0603", "VBAT", "IR_A2", "D304", G, "LED 2 current")
cap("10uF", "VBAT", "GND", "D303", G, "local reservoir for the 38 kHz pulses (keeps them off the battery wiring)")
for d, a in (("D303", "IR_A1"), ("D304", "IR_A2")):
    add(d, "phone:Everlight_IR12-21C", "IR12-21C/TR8", "C53672", {"1": a, "2": "IR_K"}, G, "Q301", 2.0,
        "Everlight DIR-0000971 rev 8 p.2: 1 anode, 2 cathode; 940 nm right-angle lens, IF 65 mA abs max (no pulse "
        "rating given). TOP edge, lens out through the dark insert.")
add("Q301", "Package_TO_SOT_SMD:SOT-523", "DMG1012T-7", "C20512", {"1": "IR_TX_G", "2": "GND", "3": "IR_K"}, G, "D303", 0.8,
    "IR LED low-side switch, ~120 mA pk (630 mA rated). Diodes DS31783 p.1: 1 G, 2 S, 3 D.")
res("100R", "IR_TX", "IR_TX_G", "Q301", G, "gate series R (GPIO42, RMT 38 kHz)")
res("100k", "IR_TX_G", "GND", "Q301", G, "gate pull-down: LEDs off at boot / while GPIO42 floats")
add("U36", "phone:Vishay_TSOP57xxx_3.95x3.95mm", "TSOP57338TT1", "C3742877", {"1": "IR_RX", "5": "IR_VCC", "6": "GND", "8": "GND"},
    G, "D303", 0.8,
    "CHANGED 2026-11-14 (fit_check.py): Vishay TSOP57338TT1, 38 kHz top-view, 3.95 x 3.95 x 0.8 mm, 2.0-5.5 V, TSOP573 = short-"
    "burst AGC (Sony/NEC/RC5 friendly, the TSOP574 drops Sony). Datasheet doc 82434 p.7 pinning: 1 OUT, 4/5 VS, 2/3/6/7/8 GND "
    "(2/3/4/7 internal, no pad). Active-low open-collector-style output with internal pull-up -> IR_RX. Replaces the 4.0 mm "
    "Everlight IRM-H638T that hit the front glass. OLD: "
    "HEIGHT 4.00 +-0.3 above the PCB (Everlight datasheet p.6), too tall under the front glass: to be replaced by a low-profile receiver (fit_check.py). Everlight DMO-0000008 rev 3 p.1 pin configuration (1 GND, 2 GND, 3 OUT, 4 Vcc) = KiCad Everlight_IRM-H6xxT; 38 kHz, "
    "2.7-5.5 V. Height ~3 mm (verify on part). Output has an internal pull-up -> IR_RX (GPIO20).")
res("100R", "RF_3V3", "IR_VCC", "U36", G, "RC filter R (DS p.2: 47-220 R)")
cap("4.7uF", "IR_VCC", "GND", "U36", G, "RC filter C (DS p.2: >= 2.2 uF), at the Vcc/GND pins")

# ======================================================================================================================
# 7. GNSS u-blox MAX-M10S
# ======================================================================================================================
G = "gnss"
add("U33", "RF_GPS:ublox_MAX", "MAX-M10S-00B", "C4153167", {
    "1": "GND", "4": "GNSS_TP", "6": "GNSS_VBCKP", "7": "3V3", "8": "3V3", "9": "GNSS_RST", "10": "GND",
    "11": "GNSS_RF_IN", "12": "GND", "16": "I2C_SDA", "17": "I2C_SCL", "18": "GNSS_SAFEBOOT"}, G, h=2.7,
    nc={"2": "TXD: UART unused, I2C only (leave open, DS table 10)", "3": "RXD: leave open if unused (internal pull-up)",
        "5": "EXTINT: leave open if unused (internal pull-up)",
        "13": "LNA_EN: no external LNA / active antenna (pin cannot be reused)",
        "14": "VCC_RF: only for an active antenna supply", "15": "VIO_SEL open = 3.3 V V_IO (DS table 10)"},
    note="u-blox UBX-20035208 R08 table 10 p.9 (1 GND, 2 TXD, 3 RXD, 4 TIMEPULSE, 5 EXTINT, 6 V_BCKP, 7 V_IO, 8 VCC, "
         "9 RESET_N, 10 GND, 11 RF_IN, 12 GND, 13 LNA_EN, 14 VCC_RF, 15 VIO_SEL, 16 SDA, 17 SCL, 18 SAFEBOOT_N); same "
         "LCC-18 as MAX-7/8 (KiCad ublox_MAX). I2C 0x42. VCC = V_IO = 3V3 (always on, IM table 42 option 1). "
         "Height 2.5 typ / 2.7 max (DS table 21). Ground the area under the module on L1/L2 (IM 4.4).")
cap("10uF", "3V3", "GND", "U33", G, "VCC bulk")
cap("100nF", "3V3", "GND", "U33", G, "VCC pin 8")
cap("100nF", "3V3", "GND", "U33", G, "V_IO pin 7")
add("D302", "Diode_SMD:D_SOD-323", "BAT54WS", "C124205", {"1": "GNSS_VBCKP", "2": "3V3"}, G, "U33", 1.1,
    "V_BCKP feed from 3V3 (no back-feed into 3V3 when it drops); 3V3 - ~0.25 V = ~3.05 V (1.65-3.6 V allowed)")
cap("22uF", "GNSS_VBCKP", "GND", "U33", G, "V_BCKP hold-up (~28 uA backup current: bridges short 3V3 dropouts only; "
    "no supercap stocked at JLC - a Seiko CPH3225A would give hours)")
add("J33", "TestPoint:TestPoint_Pad_D1.0mm", "TP GNSS_TP", "", {"1": "GNSS_TP"}, G, "U33", 0.1,
    "test pad TIMEPULSE (shares SAFEBOOT_N via internal 1 k); not placed")
add("J34", "TestPoint:TestPoint_Pad_D1.0mm", "TP GNSS_SAFEBOOT", "", {"1": "GNSS_SAFEBOOT"}, G, "U33", 0.1,
    "test pad SAFEBOOT_N: short to GND at power-up for firmware recovery; not placed")
add("AE31", "RF_Antenna:Pulse_W3011", "W3011", "C6604735", {"1": "GNSS_ANT", "2": "GND"}, G, "U33", 1.1,
    "Pulse W3011 1575 MHz chip antenna, datasheet p.5-7: one end feed, other end ground contact (KiCad pad 1 feed, pads 2 "
    "ground). 4.00 x 4.25 mm ground clearance under the antenna. TOP end of the phone, away from LTE + sub-GHz antennas.")
cap("2.2pF", "GNSS_ANT", "GND", "AE31", G, "pi shunt at the antenna (Pulse test board: 2.2 pF shunt)", dnp=True, tune=True)
res("0R", "GNSS_ANT", "GNSS_SAW_IN", "AE31", G, "pi series", tune=True)
cap("1.0pF", "GNSS_SAW_IN", "GND", "U42", G, "pi shunt, line side", dnp=True, tune=True)
add("U42", "Filter:Filter_1109-5_1.1x0.9mm", "DNP SAFFB1G56KB0F0A", "", {"1": "GNSS_SAW_IN", "4": "GNSS_RF_IN",
    "2": "GND", "3": "GND", "5": "GND"}, G, "U33", 0.5,
    "DNP (not placed): Murata SAFFB1G56KB0F0A GNSS SAW (JLC C91647 'R1X' reel, 9346 stock): spec p.1 (1) and (4) "
    "unbalanced ports, others GND; KiCad Filter_1109-5 pads match (5,4 top row, 1 left, 2,3 bottom). Fit and remove the "
    "0R bypass if LTE/sub-GHz TX desensitise the GNSS (IM 4.3). REF OUTSIDE U30-39.", dnp=True)
res("0R", "GNSS_SAW_IN", "GNSS_RF_IN", "U42", G, "SAW bypass, fitted; remove when U42 is fitted")

# NFC CS pull-up + misc (kept here so all SPI chip-selects are together)
res("100k", "NFC_CS", "RF_3V3", "U30", "nfc", "BSS pull-up: deselected while GPIO50 floats at boot")

assert all(p["ref"] for p in PARTS)
