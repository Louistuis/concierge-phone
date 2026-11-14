# Board contract (the netlist rules every subsystem file must follow)

Board: 50 x 102 mm, 6 layers, in a 54 x 108 x 13.5 mm body (Louis 2026-11-13). sch_core.py holds the core parts.
The board has no schematic file. Each subsystem is a Python file `pcb/sch_<group>.py` that defines
`PARTS = [ {...}, ... ]`. `make_board.py` imports them, places them and assigns nets. A part dict:

```python
{"ref": "U10", "fp": "Package_SON:Texas_..." ,   # stock KiCad "Lib:Footprint" or "phone:Name" (pcb/phone.pretty)
 "value": "TPS63802DLAR", "lcsc": "C2845237",     # LCSC number = what JLC places ("" = not placed by JLC, say why in note)
 "pins": {"1": "VSYS", "2": "GND", ...},          # pad number (string, exactly as in the footprint) -> net name
 "nc": {"7": "reason"},                           # electrical pads deliberately left open, with the datasheet reason
 "group": "power", "near": "U10",                 # placement hint: keep near this ref (decoupling, matching)
 "side": "F",                                     # F (front, under the display/front plate) or B (back, battery side)
 "h": 1.0,                                        # max height above the board in mm
 "note": "datasheet URL + page for the pin table"}
```
Every electrical pad of a footprint must appear in `pins` or `nc`. Check each file with
`KPY pcb/lib_check.py pcb/sch_<group>.py` (KPY = KiCad's python) until it prints OK.
Passives: 0402 by default (`Capacitor_SMD:C_0402_1005Metric`, `Resistor_SMD:R_0402_1005Metric`), 0603/0805 only where
voltage or capacitance needs it. Use JLC basic parts where possible (100 nF C1525, 1 uF C52923, 10 uF 0603 C19702,
10k C25744, 100k C25741, 4.7k C25900, 0 ohm C17168, 22 uF 0805 C45783).

## Reference ranges (no clashes)
| Group file | ICs | Passives | Other |
|---|---|---|---|
| core (make_board.py itself) | U1 P4 module, U2 EG915U, U3 SN74AXC4T774 x2 (U3,U4), U5 TS3USB221 (USB), J1 A4S display, J2 nano-SIM, J3 camera FPC, J4 USB-C | C1-99, R1-99 | Q1-9, D1-9, AE1-9, TP1-49 |
| sch_power.py | U10-U20 | C100-199, R100-199, L100-109 | D100-109, Q100-109, J10-19, F100 |
| sch_rf.py | U30-U39 | C300-399, R300-399, L300-399 | Y30-39, D300-309, Q300-309, J30-39, AE30-39 |
| sch_sense.py | U50-U69 | C500-599, R500-599 | D500-509 |
| sch_ui.py | U70-U89 | C700-799, R700-799 | J70-79, SW70-79, D700-719, LS70, M70 |

## Power rails (net names)
| Net | What |
|---|---|
| VBUS | USB-C VBUS after TPD6S300 / TVS (5 V, up to 9-12 V tolerated by BQ24074 OVP) |
| VBAT | battery + (protected cell, 3.0-4.2 V) via JST-PH 3-pin (pin roles per research/support-parts.md polarity note) |
| BAT_NTC | battery 10k NTC wire -> BQ24074 TS |
| VSYS | BQ24074 OUT (power path, 3.5-4.5 V) |
| 3V3 | TPS63802 output, always on: P4 module, expanders, sensors, GNSS, fuel gauge, secure element |
| 3V8_LTE | TPS63020 output from VBAT (3.8 V) -> EG915U VBAT_BB/VBAT_RF |
| 1V8_LTE | EG915U VDD_EXT (1.8 V, 50 mA max): shifter B side, SIM-detect pull-up |
| DISP_3V3 | load switch (AP22653, 400 mA) from 3V3, EN = DISP_EN |
| CAM_3V3 | load switch (AP22653, 300 mA) from 3V3, EN = CAM_EN AND privacy switch |
| RF_3V3 | load switch from 3V3, EN = RF_EN: NFC, 125 kHz, CC1101, SX1262, IR RX |
| SD_3V3 | load switch from 3V3, EN = SD_EN |
| MIC_3V3 | 3V3 through the privacy slide switch (hard cut) |
| GND | one ground (In1 solid plane) |

## P4 GPIO nets (fixed; see DESIGN.md GPIO map)
GPIO0 TALK_SW, GPIO1 SIDE_KEY, GPIO2 EXP_INT (open-drain, wire-OR of all expander INT pins, 10k to 3V3), GPIO3 FP_TX,
GPIO4 FP_RX, GPIO5 LORA_DIO1, GPIO7 I2C_SDA, GPIO8 I2C_SCL (2.2k pull-ups to 3V3 in core), GPIO9 AMP_BCLK,
GPIO10 AMP_WS, GPIO12 AMP_DIN, GPIO11 MIC_CLK, GPIO13 MIC_DATA, GPIO20 IR_RX, GPIO21 LTE_TXD_3V, GPIO22 LTE_RXD_3V,
GPIO23 LTE_RTS_3V, GPIO49 LTE_CTS_3V, GPIO24/25 USB_JTAG_DN/DP, GPIO26 LF_DATA, GPIO27 LCD_TE, GPIO28 LCD_CS,
GPIO29 QSPI_D0, GPIO30 QSPI_CLK, GPIO31 QSPI_D1, GPIO32 QSPI_D3, GPIO33 QSPI_D2, GPIO35 BOOT, GPIO37 U0TXD,
GPIO38 U0RXD, GPIO39 SD_D0, GPIO43 SD_CLK, GPIO44 SD_CMD, GPIO40 LF_CARRIER, GPIO41 LF_PULL, GPIO42 IR_TX,
GPIO45 SPI_SCK, GPIO46 SPI_MOSI, GPIO47 SPI_MISO, GPIO48 LORA_CS, GPIO50 NFC_CS, GPIO51 CC_CS, GPIO52 NFC_IRQ,
GPIO53 CC_GDO0. GPIO39-48 boot at 1.8 V (LDO VO4) until firmware sets 3.3 V: parts on those pins sit on a switched
rail (RF_3V3 / SD_3V3) that is off at boot.

## Expander lines (net names = function)
U50 PCAL6524 (I2C 0x22), INT -> EXP_INT:
P0_0 LTE_EN, P0_1 LTE_PWRKEY, P0_2 LTE_DTR_3V, P0_3 LTE_OE_N (10k pull-up), P0_4 LTE_STATUS_3V, P0_5 LTE_RI_3V,
P0_6 CAM_EN, P0_7 DISP_EN, P1_0 RF_EN, P1_1 SD_EN, P1_2 SD_CD, P1_3 AMP_SD, P1_4 LCD_RST, P1_5 TP_INT, P1_6 IMU_INT,
P1_7 USB_SEL, P2_0 SBU_OE_N, P2_1 RF_BAND (433/868 path), P2_2 RF_RADIO (CC1101 / SX1262), P2_3 LORA_BUSY,
P2_4 LORA_RST, P2_5 VOL_UP, P2_6 VOL_DN, P2_7 FP_EN.
U51 8-bit expander (I2C 0x43), INT -> EXP_INT: 0 CHG_N, 1 PGOOD_N, 2 GNSS_RST, 3 TOF_XSHUT, 4 TOF_INT, 5 FUEL_ALRT,
6 PRIV_STATE, 7 FP_TOUCH.

## I2C address map (one bus, I2C_SDA/I2C_SCL, 3.3 V)
0x15 CST820 touch (panel), 0x22 PCAL6524, 0x29 VL53L1CX, 0x30 MMC5603, 0x36 camera OV5647 SCCB (so NO 0x36 fuel
gauge: use TI BQ27441-G1 at 0x55), 0x39 AS7341, 0x42 MAX-M10S, 0x43 U51 expander, 0x44 SHT40, 0x45 OPT3004
(ADDR strap), 0x46 BMP581, 0x59 SGP41, 0x5A DRV2605L, 0x60 ATECC608B, 0x64 LM36011, 0x69 ICM-42670-P (AD0 high),
0x68 LED driver (if that address, IMU stays at 0x69). Report any clash you find.
