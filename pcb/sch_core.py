"""Core of the concierge phone: U1 Waveshare ESP32-P4-Module, U2 Quectel EG915U-EU + its UART shifters, nano-SIM, display
socket, camera FPC, USB-C receptacle + the two TS3USB221A switches (USB data, SBU expansion), Wi-Fi / LTE U.FL feeds,
I2C pull-ups, test pads. Rules: CONTRACT.md (refs U1-U9, C1-C99, R1-R99, Q1-Q9, J1-J9, TP1-TP49).

Sources (pin tables compared with the pad numbers of the footprint actually used):
  U1  pcb/gen_wsp4.py PINS (Waveshare ESP32-P4-Module V1.1 schematic + land DXF); GPIO -> net = CONTRACT.md.
  U2  pcb/gen_eg915u.py PINS (Quectel EG915U QuecOpen HW design V1.0, datasheets/).
  U3/U4 SN74AXC4T774PWR: research/support-parts.md sec. 5 (TI SCES899): 1 DIR1, 2 DIR2, 3 A1, 4 A2, 5 A3, 6 A4,
      7 DIR3, 8 DIR4, 9 OE (active low), 10 GND, 11 B4, 12 B3, 13 B2, 14 B1, 15 VCCB, 16 VCCA. DIRx high = A->B.
      Each I/O is referenced to the side it sits on; Ioff + VCC isolation keep the modem side safe while 1V8_LTE is off.
  U5/U6 TS3USB221A RSE (datasheets/ts3usb221a.pdf, pin functions p.3, truth table p.1): 1 1D+, 2 1D-, 3 2D+, 4 2D-,
      5 GND, 6 OE, 7 D-, 8 D+, 9 S, 10 VCC. OE low + S low = D <-> 1D, OE low + S high = D <-> 2D, OE high = all off.
  U7  TPD4E05U06DQAR: support-parts.md: 1, 2, 4, 5 = IO channels, 3/8 GND, 6/7/9/10 NC (flow-through pads).
  J1  pcb/gen_a4s.py PINS (Waveshare 1.8" AMOLED panel FPC). J2 pcb/gen_nanosim.py PINS. J3 Raspberry Pi 15-pin camera
      pinout = Espressif ESP32-P4-Function-EV-Board J9 (DESIGN.md). J4 HRO TYPE-C-31-M-12 stock KiCad footprint.

Decisions:
  - Modem UART at 1.8 V through two SN74AXC4T774 (U3 = TXD, RTS out / RXD, CTS in; U4 = DTR out / RI, STATUS in),
    both OE on LTE_OE_N (10k up in sch_sense = off at reset). DIR straps tie to the A side (VCCA) or GND.
    U4 channel 2 is unused: DIR2 = GND (B->A), B2 input grounded, A2 tied to GND (input while OE is high).
  - Modem net names on the 1.8 V side follow the modem pin: M_RXD (34, modem input), M_TXD (35), M_CTS (36), M_RTS (37),
    M_DTR (30), M_RI (39), M_STATUS (20).
  - PWRKEY: Q1 2N7002 open drain (gate LTE_PWRKEY, 100k down in sch_sense). RESET_N left open (LTE_EN power cut = reset).
  - SIM: 22 ohm series on RST/CLK/DATA + 33 pF at the holder + TPD4E05U06 + 100 nF/33 pF on USIM_VDD (Quectel reference
    design, USIM chapter). USIM_DET 51k to 1V8_LTE; holder switch opens with a card -> high = present (AT+QSIMDET=1,1).
  - Camera: CSI pairs go straight from J3 to the module pads (no series parts: D-PHY is terminated at the receiver and
    0R placeholders only add stubs). CAM_IO0 (sensor board regulator enable) 10k up to CAM_3V3.
  - Display: VBAT, VCI, VDDIO from DISP_3V3 (switched); PWR_EN 10k up to DISP_3V3 (DESIGN.md: host gives 3.3 V + PWR_EN).
    TP_VCC on always-on 3V3 so the touch chip never back-feeds from the shared I2C bus and can wake the phone.
    IM0/IM1 mode straps: each has a fitted 10k to DISP_3V3 and a DNP 10k to GND. MUST-verify the levels with a meter on
    the donor Waveshare board before ordering, and swap fitted/DNP if they read low.
  - USB: J4 D+/D- (USB_DP/USB_DN, ESD in sch_power U19) -> U5 common side. U5 1D = P4 USB Serial/JTAG (GPIO25/24),
    2D = P4 USB HS OTG pads 48/49. S = USB_SEL (100k down = flashing path at reset), OE tied low.
    SBU: U19 system side SBU1_P/SBU2_P -> U6 common; U6 1D = UART0 (U0TXD/U0RXD via 100 ohm), S tied low, OE = SBU_OE_N.
  - Wi-Fi: module pad 2 LNA_OUT -> pi (0R + 2 DNP) -> J6 U.FL. LTE: EG915U 60 -> pi (0R + 2 DNP) -> J5 U.FL.
    Both 50 ohm CPWG, JLC impedance order. ANT_BT/WIFI_SCAN (56) unused.
  - Module CHIP_PU: 10k up + 1 uF (standard ESP32 RC; harmless if the module carries its own).
Nets invented here: M_* (above), M_PWRKEY_N, USIM_VDD, USIM_RST, USIM_CLK, USIM_DATA (modem side), SIM_RST, SIM_CLK,
SIM_DATA (holder side), USIM_DET, CSI_*, USB_HS_DP/DN, SBU_TX/SBU_RX, WIFI_RF/WIFI_ANT, LTE_RF/LTE_ANT, EN, DISP_IM0/1,
CAM_IO0, LTE_USB_VBUS/DP/DM, LTE_USB_BOOT, LTE_DBG_TX/RX, C6_U0RXD/C6_U0TXD/C6_IO9.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_wsp4 import PINS as WSP4
from gen_eg915u import PINS as EG

C0402, C0603, C0805 = "Capacitor_SMD:C_0402_1005Metric", "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric"
R0402 = "Resistor_SMD:R_0402_1005Metric"
TP = "TestPoint:TestPoint_Pad_D1.0mm"
CAPS = {"100nF": ("C1525", C0402, 0.55), "1uF": ("C52923", C0402, 0.55), "10uF": ("C19702", C0603, 0.9),
        "22uF": ("C45783", C0805, 1.35), "33pF": ("C1562", C0402, 0.55)}
RESS = {"0": "C17168", "22": "C25092", "100": "C25076", "2.2k": "C25879", "10k": "C25744", "15k": "C25756", "51k": "C25794",
        "100k": "C25741"}   # 15k = 0402WGF1502TCE basic (2,093,811 on 2026-11-14)
PARTS = []
_n = {"C": 0, "R": 0, "TP": 0}

def _next(k):
    _n[k] += 1
    return f"{k}{_n[k]}"

def cap(val, a, b="GND", near=None, side="F", note="", dnp=False):
    lcsc, fp, h = CAPS.get(val, ("", C0402, 0.55))
    PARTS.append({"ref": _next("C"), "fp": fp, "value": ("DNP " if dnp else "") + val, "lcsc": "" if dnp else lcsc,
                  "pins": {"1": a, "2": b}, "group": "core", "near": near, "side": side, "h": h, "note": note,
                  "dnp": dnp})

def res(val, a, b, near=None, side="F", note="", dnp=False):
    PARTS.append({"ref": _next("R"), "fp": R0402, "value": ("DNP " if dnp else "") + val,
                  "lcsc": "" if dnp else RESS[val], "pins": {"1": a, "2": b}, "group": "core", "near": near,
                  "side": side, "h": 0.4, "note": note, "dnp": dnp})

def tp(net, near=None, side="B"):
    PARTS.append({"ref": _next("TP"), "fp": TP, "value": f"TP {net}", "lcsc": "", "pins": {"1": net}, "group": "core",
                  "near": near, "side": side, "h": 0.05, "note": "bare pad, not placed by JLC"})

# ---------------------------------------------------------------- U1 ESP32-P4 module
GPIO_NET = {0: "TALK_SW", 1: "SIDE_KEY", 2: "EXP_INT", 3: "FP_TX", 4: "FP_RX", 5: "LORA_DIO1", 7: "I2C_SDA",
            8: "I2C_SCL", 9: "AMP_BCLK", 10: "AMP_WS", 11: "MIC_CLK", 12: "AMP_DIN", 13: "MIC_DATA", 20: "IR_RX",
            21: "LTE_TXD_3V", 22: "LTE_RXD_3V", 23: "LTE_RTS_3V", 24: "USB_JTAG_DN", 25: "USB_JTAG_DP",
            26: "LF_DATA", 27: "LCD_TE", 28: "LCD_CS", 29: "QSPI_D0", 30: "QSPI_CLK", 31: "QSPI_D1", 32: "QSPI_D3",
            33: "QSPI_D2", 35: "BOOT", 37: "U0TXD", 38: "U0RXD", 39: "SD_D0", 40: "LF_CARRIER", 41: "LF_PULL",
            42: "IR_TX", 43: "SD_CLK", 44: "SD_CMD", 45: "SPI_SCK", 46: "SPI_MOSI", 47: "SPI_MISO", 48: "LORA_CS",
            49: "LTE_CTS_3V", 50: "NFC_CS", 51: "CC_CS", 52: "NFC_IRQ", 53: "CC_GDO0"}
GPIO_NC = {6: "reserved: C6 -> P4 host wake inside esp-hosted", 34: "strap, left open (default)",
           36: "strap, left open (default)", 54: "reserved: drives the C6 reset inside the module"}
u1p, u1nc = {}, {}
for pad, name in WSP4.items():
    p = str(pad)
    if name == "GND": u1p[p] = "GND"
    elif name.startswith("GPIO"):
        g = int(name[4:])
        if g in GPIO_NET: u1p[p] = GPIO_NET[g]
        else: u1nc[p] = GPIO_NC[g]
    elif name.startswith("DSI"): u1nc[p] = "MIPI DSI unused (display is QSPI)"
    elif name.startswith("CSI"): u1p[p] = name
    elif name == "LNA_OUT": u1p[p] = "WIFI_RF"
    elif name in ("C6_U0RXD", "C6_U0TXD", "C6_IO9"): u1p[p] = name
    elif name.startswith("C6_IO"): u1nc[p] = "C6 GPIO unused (only IO9 boot strap goes to a test pad)"
    elif name == "USB_HS_DM": u1p[p] = "USB_HS_DN"
    elif name == "USB_HS_DP": u1p[p] = "USB_HS_DP"
    elif name in ("ESP_3V3", "VBAT"): u1p[p] = "3V3"
    elif name == "CHIP_PU": u1p[p] = "EN"
    elif name == "VFB_VO4": u1nc[p] = "LDO VO4 feedback, used inside the module only"
    else: raise SystemExit(f"U1 pad {pad} {name} not handled")
PARTS.append({"ref": "U1", "fp": "phone:Waveshare_ESP32-P4-Module", "value": "Waveshare ESP32-P4-Module (28101)",
              "lcsc": "", "pins": u1p, "nc": u1nc, "group": "core", "near": None, "side": "F", "h": 3.3,   # Waveshare drawing: 3.30 total (PCB 0.80 + shield)
             
              "note": "consigned to JLC or hand-soldered (no LCSC stock); pads per gen_wsp4.py; VBAT pad 84 to 3V3 "
                      "(module RTC domain, Waveshare schematic V1.1)"})
cap("22uF", "3V3", near="U1", note="module bulk at pads 85/86"); cap("10uF", "3V3", near="U1"); cap("100nF", "3V3", near="U1")
res("10k", "3V3", "EN", near="U1", note="CHIP_PU pull-up (ESP32 HW design guide RC)")
cap("1uF", "EN", near="U1", note="CHIP_PU delay, with the 10k = ~10 ms")
res("2.2k", "I2C_SDA", "3V3", near="U1", note="I2C pull-up (CONTRACT.md), 400 kHz with ~19 devices")
res("2.2k", "I2C_SCL", "3V3", near="U1")
res("10k", "EXP_INT", "3V3", near="U1", note="wire-OR interrupt pull-up (CONTRACT.md)")
# Wi-Fi feed: pad 2 -> pi -> U.FL
cap("33pF", "WIFI_RF", near="J6", dnp=True, note="pi match shunt 1 (tune with NanoVNA)")
res("0", "WIFI_RF", "WIFI_ANT", near="J6", note="pi match series")
cap("33pF", "WIFI_ANT", near="J6", dnp=True, note="pi match shunt 2")
PARTS.append({"ref": "J6", "fp": "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", "value": "U.FL-R-SMT-1(10) Wi-Fi",
              "lcsc": "C88373", "pins": {"1": "WIFI_ANT", "2": "GND"}, "group": "core", "near": "U1", "side": "F",
              "h": 1.25, "note": "Molex 1461530050 flex antenna under the top insert"})

# ---------------------------------------------------------------- U2 EG915U-EU
u2p, u2nc = {}, {}
USE = {32: "3V8_LTE", 33: "3V8_LTE", 52: "3V8_LTE", 53: "3V8_LTE", 15: "M_PWRKEY_N", 20: "M_STATUS", 29: "1V8_LTE",
       30: "M_DTR", 34: "M_RXD", 35: "M_TXD", 36: "M_CTS", 37: "M_RTS", 39: "M_RI", 42: "USIM_DET", 43: "USIM_VDD",
       44: "USIM_RST", 45: "USIM_DATA", 46: "USIM_CLK", 47: "GND", 60: "LTE_RF", 8: "LTE_USB_VBUS", 9: "LTE_USB_DP",
       10: "LTE_USB_DM", 75: "LTE_USB_BOOT", 22: "LTE_DBG_RX", 23: "LTE_DBG_TX"}
for pad, name in EG.items():
    p = str(pad)
    if pad in USE: u2p[p] = USE[pad]
    elif name == "GND": u2p[p] = "GND"
    elif name == "RESERVED": u2nc[p] = "RESERVED: keep open (Quectel)"
    elif pad == 17: u2nc[p] = "RESET_N open: LTE_EN rail cut is the hard reset (DESIGN.md)"
    elif pad == 18: u2nc[p] = "W_DISABLE# internal pull-up = RF on"
    else: u2nc[p] = f"{name} unused, open per Quectel unused-pin rule"
PARTS.append({"ref": "U2", "fp": "phone:Quectel_EG915U", "value": "EG915UEUAC-N05-SNNSA", "lcsc": "C7471302",
              "pins": u2p, "nc": u2nc, "group": "core", "near": None, "side": "F", "h": 2.4,
              "note": "pads per gen_eg915u.py; GND 55/59/61 solid (no relief) next to RF"})
cap("1uF", "1V8_LTE", near="U2", note="VDD_EXT decoupling (Quectel: 1-4.7 uF)"); cap("100nF", "1V8_LTE", near="U2")
PARTS.append({"ref": "Q1", "fp": "Package_TO_SOT_SMD:SOT-23", "value": "2N7002", "lcsc": "C8545",
              "pins": {"1": "LTE_PWRKEY", "2": "GND", "3": "M_PWRKEY_N"}, "group": "core", "near": "U2", "side": "F",
              "h": 1.1, "note": "open drain on PWRKEY (pin 15, internal pull-up to VBAT, never a pull-down resistor); SOT-23 1 G 2 S 3 D"})
# LTE feed
cap("33pF", "LTE_RF", near="J5", dnp=True, note="pi match shunt 1 (tune)")
res("0", "LTE_RF", "LTE_ANT", near="J5", note="pi match series")
cap("33pF", "LTE_ANT", near="J5", dnp=True, note="pi match shunt 2")
PARTS.append({"ref": "J5", "fp": "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", "value": "U.FL-R-SMT-1(10) LTE",
              "lcsc": "C88373", "pins": {"1": "LTE_ANT", "2": "GND"}, "group": "core", "near": "U2", "side": "F",
              "h": 1.25, "note": "Taoglas FXP40 flex antenna in the bottom band"})
# UART shifters
SHIFT = "Package_SO:TSSOP-16_4.4x5mm_P0.65mm"
PARTS.append({"ref": "U3", "fp": SHIFT, "value": "SN74AXC4T774PWR", "lcsc": "C1849453", "group": "core", "near": "U2",
              "side": "F", "h": 1.2, "note": "ch1 TXD, ch2 RTS A->B; ch3 RXD, ch4 CTS B->A",
              "pins": {"1": "3V3", "2": "3V3", "3": "LTE_TXD_3V", "4": "LTE_RTS_3V", "5": "LTE_RXD_3V",
                       "6": "LTE_CTS_3V", "7": "GND", "8": "GND", "9": "LTE_OE_N", "10": "GND", "11": "M_CTS",
                       "12": "M_TXD", "13": "M_RTS", "14": "M_RXD", "15": "1V8_LTE", "16": "3V3"}})
PARTS.append({"ref": "U4", "fp": SHIFT, "value": "SN74AXC4T774PWR", "lcsc": "C1849453", "group": "core", "near": "U2",
              "side": "F", "h": 1.2,
              "note": "ch1 DTR A->B; ch2 unused (B->A, B2 and A2 both tied to GND); ch3 RI, ch4 STATUS B->A. A2 (pin 4) to GND "
                      "(review 2026-11-14): TI SCES898C Table 7-1 p.21-22 note 2 'pins configured as inputs should not be left "
                      "floating' and with OE high (boot) A2 is an input. A2 only ever outputs B2 = low, so the GND tie never "
                      "contends; the 71k internal pull-down (7.3.9 p.21) already covered it, this just makes it explicit.",
              "pins": {"1": "3V3", "2": "GND", "3": "LTE_DTR_3V", "4": "GND", "5": "LTE_RI_3V", "6": "LTE_STATUS_3V",
                       "7": "GND", "8": "GND", "9": "LTE_OE_N", "10": "GND", "11": "M_STATUS", "12": "M_RI",
                       "13": "GND", "14": "M_DTR", "15": "1V8_LTE", "16": "3V3"}})
for u in ("U3", "U4"):
    cap("100nF", "3V3", near=u, note="VCCA"); cap("100nF", "1V8_LTE", near=u, note="VCCB")

# ---------------------------------------------------------------- nano-SIM (push-push, side slot)
PARTS.append({"ref": "J2", "fp": "phone:SIM_Nano_SHOUHAN_7P_H1.37", "value": "NANO SIM 7P H1.37", "lcsc": "C7529384",
              "pins": {"C1": "USIM_VDD", "C2": "SIM_RST", "C3": "SIM_CLK", "C5": "GND", "C7": "SIM_DATA",
                       "CD": "USIM_DET", "8": "GND", "9": "GND", "10": "GND", "11": "GND"},
              "nc": {"C6": "VPP unused (Quectel)"}, "group": "core", "near": "U2", "side": "F", "h": 1.37,
              "note": "card enters from the board edge behind the side-wall slot; CD normally closed to shell"})
res("22", "USIM_RST", "SIM_RST", near="J2", note="Quectel USIM reference: 22R series")
res("22", "USIM_CLK", "SIM_CLK", near="J2"); res("22", "USIM_DATA", "SIM_DATA", near="J2")
for n in ("SIM_RST", "SIM_CLK", "SIM_DATA"): cap("33pF", n, near="J2", note="Quectel USIM reference: 33 pF at the holder")
cap("100nF", "USIM_VDD", near="J2"); cap("33pF", "USIM_VDD", near="J2")
res("51k", "USIM_DET", "1V8_LTE", near="J2", note="Quectel: 51k pull-up to VDD_EXT on USIM_DET")
PARTS.append({"ref": "U7", "fp": "Package_SON:USON-10_2.5x1.0mm_P0.5mm", "value": "TPD4E05U06DQAR", "lcsc": "C2827646",
              "pins": {"1": "SIM_DATA", "2": "SIM_CLK", "4": "SIM_RST", "5": "USIM_VDD", "3": "GND", "8": "GND"},
              "nc": {"6": "flow-through NC", "7": "flow-through NC", "9": "flow-through NC", "10": "flow-through NC"},
              "group": "core", "near": "J2", "side": "F", "h": 0.55, "note": "SIM ESD, next to the holder"})

# ---------------------------------------------------------------- J1 display (Panasonic A4S, panel FPC)
PARTS.append({"ref": "J1", "fp": "phone:Panasonic_AXE534127_A4S_34P", "value": "AXE534127", "lcsc": "C6863072",
              "group": "core", "near": "U1", "side": "F", "h": 0.8, "note": "pins per gen_a4s.py PINS",
              "pins": {"1": "LCD_RST", "2": "LCD_TE", "3": "GND", "4": "GND", "5": "QSPI_D0", "7": "QSPI_D1",
                       "8": "I2C_SCL", "9": "QSPI_CLK", "10": "I2C_SDA", "11": "LCD_CS", "12": "TP_INT",
                       "13": "QSPI_D2", "14": "LCD_RST", "15": "QSPI_D3", "16": "3V3", "17": "DISP_IM1",
                       "18": "DISP_3V3", "19": "DISP_IM0", "20": "DISP_3V3", "21": "GND", "22": "DISP_PWR_EN",
                       "23": "GND", "24": "DISP_3V3", "25": "GND", "26": "DISP_3V3", "27": "GND", "28": "GND",
                       "29": "GND", "31": "GND", "33": "GND", "MP": "GND"},
              "nc": {"6": "NC on panel", "30": "NC on panel", "32": "NC on panel", "34": "VPP factory test"}})
cap("10uF", "DISP_3V3", near="J1", note="panel VBAT bulk"); cap("1uF", "DISP_3V3", near="J1", note="VCI")
cap("100nF", "DISP_3V3", near="J1", note="VDDIO"); cap("100nF", "3V3", near="J1", note="TP_VCC")
res("10k", "DISP_PWR_EN", "DISP_3V3", near="J1", note="panel PWR_EN high whenever DISP_3V3 is on")
res("10k", "DISP_IM0", "DISP_3V3", near="J1", note="IM0 strap high (MUST-verify on the donor board)")
res("10k", "DISP_IM0", "GND", near="J1", dnp=True, note="IM0 strap low option")
res("10k", "DISP_IM1", "DISP_3V3", near="J1", note="IM1 strap high (MUST-verify on the donor board)")
res("10k", "DISP_IM1", "GND", near="J1", dnp=True, note="IM1 strap low option")

# ---------------------------------------------------------------- J3 camera (RPi 15-pin, back side)
PARTS.append({"ref": "J3", "fp": "Connector_FFC-FPC:JUSHUO_AFA07-S15FCA-00_1x15-1MP_P1.0mm_Horizontal",
              "value": "AFA07-S15FCA-00", "lcsc": "C262721", "group": "core", "near": None, "side": "B", "h": 2.5,
              "note": "OV5647 RPi pinout (Espressif P4 EV board J9)",
              "pins": {"1": "GND", "2": "CSI_D0N", "3": "CSI_D0P", "4": "GND", "5": "CSI_D1N", "6": "CSI_D1P",
                       "7": "GND", "8": "CSI_CLKN", "9": "CSI_CLKP", "10": "GND", "11": "CAM_IO0", "13": "I2C_SCL",
                       "14": "I2C_SDA", "15": "CAM_3V3", "MP": "GND"},
              "nc": {"12": "CAM_GPIO1 (LED on RPi boards) unused"}})
cap("10uF", "CAM_3V3", near="J3", side="B"); cap("100nF", "CAM_3V3", near="J3", side="B")
res("10k", "CAM_IO0", "CAM_3V3", near="J3", side="B", note="camera board regulators on whenever CAM_3V3 is on")

# ---------------------------------------------------------------- J4 USB-C + data switches
PARTS.append({"ref": "J4", "fp": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "value": "TYPE-C-31-M-12",
              "lcsc": "C165948", "group": "core", "near": None, "side": "F", "h": 3.26,
              "note": "HRO drawing: top-mount, 3.26 above the PCB. bottom edge; protection in sch_power (U19 TPD6S300A, F100, D100)",
              "pins": {"A1": "GND", "B1": "GND", "A12": "GND", "B12": "GND", "A4": "VBUS_CONN", "A9": "VBUS_CONN",
                       "B4": "VBUS_CONN", "B9": "VBUS_CONN", "A5": "USB_CC1", "B5": "USB_CC2", "A6": "USB_DP",
                       "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN", "A8": "SBU1", "B8": "SBU2", "SH": "GND"}})
USW = "Package_DFN_QFN:Texas_UQFN-10_1.5x2mm_P0.5mm"
PARTS.append({"ref": "U5", "fp": USW, "value": "TS3USB221ARSER", "lcsc": "C128396", "group": "core", "near": "J4",
              "side": "F", "h": 0.55, "note": "S low = 1D = USB Serial/JTAG (flashing), S high = 2D = USB HS OTG",
              "pins": {"1": "USB_JTAG_DP", "2": "USB_JTAG_DN", "3": "USB_HS_DP", "4": "USB_HS_DN", "5": "GND",
                       "6": "GND", "7": "USB_DN", "8": "USB_DP", "9": "USB_SEL", "10": "3V3"}})
cap("100nF", "3V3", near="U5")
PARTS.append({"ref": "U6", "fp": USW, "value": "TS3USB221ARSER", "lcsc": "C128396", "group": "core", "near": "J4",
              "side": "F", "h": 0.55, "note": "SBU expansion port <-> UART0, off (OE high) at boot",
              "pins": {"1": "SBU_TX", "2": "SBU_RX", "5": "GND", "6": "SBU_OE_N", "7": "SBU2_P", "8": "SBU1_P",
                       "9": "GND", "10": "3V3"},
              "nc": {"3": "2D+ unused (S tied low)", "4": "2D- unused"}})
cap("100nF", "3V3", near="U6")
res("100", "U0TXD", "SBU_TX", near="U6", note="series protection toward the expansion port")
res("100", "U0RXD", "SBU_RX", near="U6")

# ---------------------------------------------------------------- test pads (back side, pogo-reachable)
for n in ("BOOT", "EN", "U0TXD", "U0RXD", "GND"): tp(n, near="U1")
for n in ("C6_U0RXD", "C6_U0TXD", "C6_IO9"): tp(n, near="U1")
for n in ("LTE_USB_VBUS", "LTE_USB_DP", "LTE_USB_DM", "LTE_USB_BOOT", "LTE_DBG_TX", "LTE_DBG_RX", "1V8_LTE"): tp(n, near="U2")

# ---------------------------------------------------------------- added after review (kept last so earlier refs keep their numbers)
res("15k", "USIM_VDD", "SIM_DATA", near="J2",
    note="USIM_DATA pull-up 15k to USIM_VDD on the holder side of the 22R: Quectel EG915U QuecOpen HW design V1.0 "
         "(datasheets/) Figure 23 + Figure 24 p.52-53 and the 4.8 rule 'pull-up resistor on USIM_DATA ... near the (U)SIM "
         "card connector'. Added 2026-11-14 (R19).")
