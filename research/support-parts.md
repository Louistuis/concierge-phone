# Concierge phone: support-part research (pin tables, footprints, JLC stock)

Researched 2026-11-13. Every pin table and design value below was read from the manufacturer datasheet named in that
section (PDF downloaded and read, revision noted). Stock numbers come from the JLCPCB parts-search API
(`POST https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`) on 2026-11-13 and will
drift. "ext" = JLC extended part (feeder fee), "basic" = JLC basic part. Footprints were checked against the `.kicad_mod`
files in `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/` (KiCad 10).

Nothing was ordered. No other files were changed.

## Summary table

| # | Function | Orderable part | Package | LCSC (JLC stock 2026-11-13) | Stock KiCad footprint |
|---|---|---|---|---|---|
| 1 | 3.3 V main buck-boost | TI **TPS63802DLAR** | VSON-HR-10 (DLA), 2.0 x 3.0 mm, no exposed pad | **C2845237** (21,071, ext) | **none**, draw it (pad table in 1.4) |
| 1L | its inductor 0.47 uH | Murata DFE201612E-R47M=P2 (TI-listed) | 2016 | C668312 (13,233) | Inductor_SMD:L_Murata_DFE201610P |
| 1L alt | 0.47 uH, lower loss | Coilcraft XFL4015-471MEC (TI-listed) | 4 x 4 mm | C18221164 (1,407) | Inductor_SMD:L_Coilcraft_XxL4020 |
| 2 | 3.8 V LTE buck-boost | TI **TPS63020DSJR** | VSON-14 (DSJ) 4 x 3 mm, 0.5 mm pitch, EP | **C15483** (20,815, ext) | closest: Package_DFN_QFN:DFN-14-1EP_3x4mm_P0.5mm_EP1.7x3.3mm (EP = pad 15); not an exact TI land |
| 2L | its inductor 1.5 uH | Coilcraft XFL4020-152MEC (TI-listed) | 4 x 4 x 2.1 mm | C3033018 (19,266) | Inductor_SMD:L_Coilcraft_XxL4020 |
| 3 | Keypad scanner | TI **TCA8418RTWR** | WQFN-24 (RTW0024B) 4 x 4, EP 2.45 | **C138713** (30,451, ext) | Package_DFN_QFN:WQFN-24-1EP_4x4mm_P0.5mm_EP2.45x2.45mm (EP = pad 25). NOT Texas_RTW_..._EP2.7x2.7mm |
| 4 | Load switch, current-limited (camera, panel) | Diodes **AP22653AW6-7** (latch-off) or **AP22653W6-7** (constant-current) | SOT-26 | **C1511768** (3,922) / **C2158037** (7,088) | Package_TO_SOT_SMD:SOT-23-6 |
| 4 alt | same job, no QOD | TI TPS2553DBVR | SOT-23-6 | C55266 (48,696) | Package_TO_SOT_SMD:SOT-23-6 |
| 5 | UART level shifter | TI **SN74AXC4T774PWR** | TSSOP-16 | **C1849453** (1,991, ext) | Package_SO:TSSOP-16_4.4x5mm_P0.65mm |
| 6a | SIM ESD | TI **TPD4E05U06DQAR** | USON-10 (DQA) 2.5 x 1.0 | **C138714** (only 171) ; TECH PUBLIC clone C2827646 (38,496) | Package_SON:USON-10_2.5x1.0mm_P0.5mm |
| 6b | RF ESD | Murata **LXES15AAA1-153** | 0402 (1.0 x 0.5 x 0.33 max) | Murata C86141 (**0**) ; Leiditech C5210978 (17,828) ; GOODWORK C53283248 (7,719) | Diode_SMD:D_0402_1005Metric (or custom Murata land, 6b) |
| 7a | LTE VBAT TVS, 4.5 V standoff | Prisemi **PTVSHC3D4V5U** | SOD-323 | **C319211** (13,030) | Diode_SMD:D_SOD-323 |
| 7b | 100 uF 6.3 V X5R 1210 | Samsung **CL32A107MQVNNNE** | 1210 | **C49066 confirmed** (161,556) | Capacitor_SMD:C_1210_3225Metric |
| 8 | Battery connector 2-pin | JST **S2B-PH-SM4-TB(LF)(SN)** | PH, SMD right-angle | **C295747** (743) ; XYECONN clone C54582899 (3,225) | Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal |
| 9a | Front key, top-actuated | Omron **B3U-1000P** | 3.0 x 2.5 x 1.6 mm | **C231329** (72,285) | Button_Switch_SMD:SW_SPST_B3U-1000P |
| 9b | Side key | Panasonic **EVQPUB02K** | 4.7 x 3.5 (4.5 incl. plate) x 1.65 mm | **C2915192 confirmed** (1,249) | Button_Switch_SMD:Panasonic_EVQPUK_EVQPUB **confirmed** |
| B1 | VBUS TVS | SMF15A (Littelfuse / MDD) | SOD-123FL | C151294 (10,460) / C123802 (91,464) | Diode_SMD:D_SOD-123F |
| B2 | VBUS PTC | LUTE 1206L150/24NR (1.5 A hold, 24 V) | 1206 | C20627120 (28,702) | Fuse:Fuse_1206_3216Metric |
| C1 | Battery 3-pin (with NTC) | JST **S3B-PH-SM4-TB(LF)(SN)** | PH, SMD right-angle | **C265101** (22,388) | Connector_JST:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal |
| C2 | On-board 10k NTC | Murata **NCP15XH103F03RC** | 0402 | **C77131** (299,832) | Resistor_SMD:R_0402_1005Metric |

Common passives that are JLC basic parts (no feeder fee), checked via the same API: 22 uF 6.3 V X5R 0603 Samsung
CL10A226MQ8NRNC **C59461**; 10 uF 10 V X5R 0603 CL10A106KP8NNNC **C19702**; 22 uF 25 V X5R 0805 CL21A226MAQNNNE
**C45783**; 100 nF 16 V X7R 0402 CL05B104KO5NNNC **C1525**; 1 uF 25 V X5R 0402 CL05A105KA5NQNC **C52923**. TI's own
listed output cap GRM188R60J226MEA0D is C77042 (496,130, ext).

---

## 1. TI TPS63802DLAR, 3.3 V main rail

Source: TI datasheet SLVSEU9D (Nov 2018, rev. Jan 2021), https://www.ti.com/lit/ds/symlink/tps63802.pdf

* Orderable: **TPS63802DLAR** (3000/reel, marking 63802). TPS63802DLAT = 250 reel.
* Package: **10-pin VSON-HR (DLA0010A)**, body 2.0 x 3.0 mm (1.9-2.1 x 2.9-3.1), 1.0 mm max height, 0.5 mm pitch.
  **There is no exposed thermal pad.** Pin 8 (GND) is a long finger (1.0-1.2 mm) that reaches under the body.
* VIN 1.3-5.5 V (>1.8 V to start), VOUT 1.8-5.2 V, 2 A out for VIN >= 2.3 V at 3.3 V out, IQ 11 uA,
  shutdown 45 nA typ. EN/MODE VIH 1.2 V min, VIL 0.4 V max. Peak current limit (boost) 4 / 5 / 5.75 A min/typ/max.
* JLC: **C2845237**, 21,071 in stock, extended. (A second JLC entry C9900330615 has 0 stock, ignore.)

### 1.1 Pin table (Table 7-1, top view)

| Pad | Pin | Connect to |
|---|---|---|
| 1 | EN | Enable, must not float. Tie to VIN for always-on, or drive from the power-latch / PMIC logic (VIH >= 1.2 V). |
| 2 | MODE | LOW = power-save (best for a battery device), HIGH = forced PWM. Must not float. Recommended: tie to GND. |
| 3 | AGND | Analog ground: bottom of R2 and the quiet ground. Join to GND (pad 8) close to the IC (layout rule 2). |
| 4 | FB | Divider midpoint (R1 to VOUT, R2 to AGND). Keep away from L1/L2. |
| 5 | PG | Open-drain power-good. Pull up (100 k in TI design) to any rail < 5.5 V, or leave open if unused. |
| 6 | VOUT | 3.3 V output, 22 uF to GND right at the pin. |
| 7 | L2 | Inductor, output side. |
| 8 | GND | Power ground, input and output cap returns. |
| 9 | L1 | Inductor, input side. |
| 10 | VIN | Battery (3.0-4.4 V), 10 uF to GND right at the pin. |

### 1.2 External parts for 3.0-4.4 V in, 3.3 V / 1.5 A out

* **Feedback** (eq. 3, R1 = R2 x (VOUT / VFB - 1), VFB = 500 mV, R2 must be <= 100 k): TI's own 3.3 V row of Table 10-5:
  **R1 = 511 k 1 %, R2 = 91 k 1 %** -> 0.5 x (1 + 511/91) = **3.308 V**.
* **Inductor**: 0.47 uH (effective range 0.37-0.57 uH, rec. op. cond.). Eq. 2 at the worst case (VIN 3.0 V, 1.5 A,
  fsw about 2.1 MHz, eta 0.9) gives IPEAK about 1.97 A, so Isat >= 2.4 A with the 20 % margin TI asks for. TI's Table 10-2 lists
  only parts with Isat >= 5.4 A (the IC's boost current limit is 4-5.75 A), which is the safer choice:
  * **Murata DFE201612E-R47M=P2**, 2.0 x 1.6 x 1.2 mm, 26 mOhm (TI list: Isat 5.5 A). **LCSC C668312, 13,233 in stock.**
    KiCad: `Inductor_SMD:L_Murata_DFE201610P` (same 2016 land).
  * **Coilcraft XFL4015-471MEC**, 4 x 4 x 1.5 mm, 7.6 mOhm, Isat 5.4 A (the part TI measured with). LCSC C18221164,
    1,407 in stock. KiCad: `Inductor_SMD:L_Coilcraft_XxL4020`. Better efficiency at 1.5 A, bigger.
  * TDK TFM201610ALM-R47MTAA (C501954, 4,489) is a 2016 alternative not on TI's list.
* **Output cap**: 1 x 22 uF for VOUT <= 3.6 V (section 10.2.2.3); effective >= 7 uF after DC bias. TI: GRM188R60J226MEA0
  (0603 6.3 V). JLC basic equivalent: Samsung CL10A226MQ8NRNC C59461. I would fit 2 x 22 uF because a camera and an AMOLED
  panel hang off this rail (no upper limit on COUT per datasheet).
* **Input cap**: 10 uF X5R/X7R at VIN-GND (section 10.2.2.4). TI: GRM188R60J106ME84. JLC basic: CL10A106KP8NNNC C19702.
* PG pull-up: 100 k (R3 in Figure 10-1) if used.

### 1.3 KiCad land pattern

The stock library has **no** DLA footprint. The only VSON-HR is `Package_SON:Texas_VSON-HR-8_1.5x2mm_P0.5mm` (8 pins, for
TPS62823), which does not fit. `WSON-10-1EP_2x3mm_P0.5mm_EP0.84x2.4mm` has the right outline but an exposed pad and equal pads,
so it does not match. Draw a custom footprint from the TI "EXAMPLE BOARD LAYOUT" (drawing 4223750/D, page 36 of the PDF).

### 1.4 Pad table for the custom footprint (top view, origin = package centre, KiCad +y down, pin 1 top-left)

| Pad | Centre x (mm) | Centre y (mm) | Size x by y (mm) |
|---|---|---|---|
| 1 | -0.90 | -1.00 | 0.60 x 0.25 |
| 2 | -0.90 | -0.50 | 0.60 x 0.25 |
| 3 | -0.90 | 0.00 | 0.60 x 0.25 |
| 4 | -0.90 | +0.50 | 0.60 x 0.25 |
| 5 | -0.90 | +1.00 | 0.60 x 0.25 |
| 6 | +0.75 | +1.00 | 0.90 x 0.25 |
| 7 | +0.75 | +0.50 | 0.90 x 0.25 |
| 8 | +0.55 | 0.00 | 1.30 x 0.25 (spans x -0.10 to +1.20) |
| 9 | +0.75 | -0.50 | 0.90 x 0.25 |
| 10 | +0.75 | -1.00 | 0.90 x 0.25 |

* Rounded corners R0.05, non-solder-mask-defined pads, mask expansion 0.07 mm max all round (TI preferred).
* Body outline 2.0 (x) by 3.0 (y). Pad pitch 0.5, row spacing 2.0 between pads 1 and 5, pin 10 to 6 = 2.0 (TI "(2)").
* Stencil (page 37, 0.1 mm stencil): signal pads 1:1; pad 8 printed as two 0.55 x 0.25 apertures with about 0.175 gap (83 % coverage).
* These are the TI "example" values (parenthesised = reference). They were read off the drawing, so run a DRC overlay
  against the PDF page before ordering.

---

## 2. TI TPS63020DSJR, 3.8 V LTE rail

Source: TI datasheet SLVS916I (rev. Oct 2019; package addendum dated 11-Apr-2026), https://www.ti.com/lit/ds/symlink/tps63020.pdf

* Orderable: **TPS63020DSJR** (3000/reel, marking PS63020). Adjustable version (TPS63021 = fixed 3.3 V, not wanted).
* Package: **VSON-14 (DSJ, R-PVSON-N14)**, body 4.0 x 3.0 mm (3.85-4.15 x 2.85-3.15), **0.5 mm pitch**, exposed thermal pad
  **2.85 x 1.58 mm** connected to PGND, max height 1.0 mm.
* VIN/VINA 1.8-5.5 V, VOUT 1.2-5.5 V, 2 A out at VIN > 2.5 V (3.3 V out), average switch current limit 3.5 / 4.0 / 4.5 A,
  fsw 2.4 MHz, IQ 25 uA, shutdown 0.1 uA. EN and PS/SYNC: VIH 1.2 V min, VIL 0.4 V max. Note TA max 85 C.
* JLC: **C15483**, 20,815 in stock, extended.

### 2.1 Pin table (top view)

| Pad | Pin | Connect to |
|---|---|---|
| 1 | VINA | Control-stage supply. Connect to the battery (VIN) node; 100 nF to GND (pin 2) close to the pin, **must not exceed 0.22 uF** (section 8.2.2.5). |
| 2 | GND | Control/logic ground. Bottom of R2. Join PGND to GND at one point, ideally close to this pin (section 7.1). |
| 3 | FB | Divider midpoint. |
| 4, 5 | VOUT | 3.8 V output to the modem VBAT. Output caps here. |
| 6, 7 | L2 | Inductor, output side. |
| 8, 9 | L1 | Inductor, input side. |
| 10, 11 | VIN | Battery, power stage. Input caps here. |
| 12 | EN | 1 = on, 0 = off, must not be left open. Drive from an MCU GPIO with a 100 k pull-down so the modem rail is off by default. |
| 13 | PS/SYNC | 1 = forced PWM (power save off), 0 = power save. Must not be left open. TI's Figure 7 ties it high with VINA/EN. For an LTE modem, high (PWM) gives lower ripple during TX bursts; low saves current in idle. Either tie high, or give it its own GPIO. |
| 14 | PG | Open-drain power good; 1 M pull-up (R3) to VOUT in the TI circuit. Can be left open. |
| EP (15) | Thermal pad | PGND. Solder it, stitch with vias to the ground plane. |

Note: TI's revision history says "removed the connection from VINA to VIN" in the drawings, and Figure 7 shows VINA tied to EN
and PS/SYNC only. VINA must still be supplied (it is the UVLO-sensed control supply, 1.8-5.5 V), so feed it from the battery
node (optionally through 10-100 Ohm so the 100 nF forms a small RC filter). Worth a look at the TPS63020EVM schematic if you
want TI's exact wiring.

### 2.2 External parts for 3.0-4.4 V in, 3.8 V / 1 A bursts out

* **Feedback** (eq. 3, R1 = R2 x (VOUT/VFB - 1), VFB 500 mV, "R2 must be kept in the range of 200 k"): VOUT/VFB - 1 = 6.6.
  * **R2 = 180 k, R1 = 1.2 M (1 %)** -> 0.5 x (1 + 1200/180) = **3.833 V**. Keeps TI's own R2 = 180 k from Table 3.
  * Alternative: R2 = 182 k, R1 = 1.21 M (both E96) -> 3.824 V. (R1 = 1.18 M gives 3.778 V.)
  * 3.8 V is below the buck-boost transition at high battery, so expect buck-boost/boost operation for most of the discharge curve.
* **Inductor**: 1.0 or 1.5 uH for 1.5-2 A loads (section 8.2.2), never below 1 uH. Eq. 2 at VIN 3.0 V, 3.8 V out, eta 0.9,
  f 2.4 MHz, L 1.5 uH: 1 A -> 1.50 A peak, 2 A -> 2.90 A peak, so Isat >= 3.5 A with TI's 20 % margin. The switch current
  limit is 4.5 A max, so a 5 A part is the robust choice:
  * **Coilcraft XFL4020-152MEC**, 1.5 uH, 4 x 4 x 2.1 mm, Isat 5.1 A, DCR 15 mOhm (TI Table 2 lists XFL4020-152ME).
    **LCSC C3033018, 19,266 in stock.** KiCad: `Inductor_SMD:L_Coilcraft_XxL4020`.
  * Sunlord MWSA0412S-1R5MT (C17700153, 2,237; 3.25/4 A, 75 mOhm) is a cheaper but weaker alternative; not on TI's list.
* **Output caps**: TI recommends **3 x 22 uF** (Table 1: 1.5 uH works with 2x22 to >=100 uF). TI uses 0603 6.3 V; at 3.8 V
  bias an 0603 6.3 V part keeps maybe a third of its value, so I would use **3 x 22 uF 0805 (CL21A226MAQNNNE, C45783 basic)**
  at the IC, plus the 100 uF 1210 (item 7b) at the modem VBAT pin. There is no upper limit on COUT.
* **Input caps**: TI typical application uses **2 x 10 uF** (C1) at VIN, X5R/X7R 0603 6.3 V; I would use 2 x 10 uF 10 V 0603
  (C19702). Add bulk (TI suggests 47 uF electrolytic/tantalum if the source is "more than a few inches" away; on a phone
  board with the cell next to it, extra 22 uF ceramic is enough).
* VINA cap: **100 nF**, <= 220 nF (C1525).
* PG pull-up 1 M if used.

### 2.3 Footprint

* No stock KiCad footprint matches the TI DSJ land pattern exactly (page 33, drawing 4210895-2/E: pads about 0.24 x 0.6 at 0.5
  pitch, row spacing 2.8, centre pad 2.85 x 1.58 with PGND tie-bars running out to 4.4 mm overall).
* **Closest stock part: `Package_DFN_QFN:DFN-14-1EP_3x4mm_P0.5mm_EP1.7x3.3mm`** (Linear "DE" DFN): 14 pads, 0.5 pitch,
  pads 0.7 x 0.25 at x = +/-1.45 (row spacing 2.9), EP pad **"15"** 1.7 x 3.3 with four separate paste pads. Pin numbering
  (1-7 down the left, 8-14 up the right) matches the TI top view. The EP is 0.12 mm wider and 0.45 mm longer than the TI EP,
  which still clears the signal pads by 0.25 mm and only overlaps the PGND tie-bar area at the ends, so it is solderable and
  safe. If you want the TI land exactly, copy that footprint and edit the EP to 2.85 x 1.58 (long axis along the pin rows).
* The other stock 14-pin SONs (`VSON-14-1EP_3x4.45mm_P0.65mm...`, `DFN-14-1EP_3x4.5mm_P0.65mm...`) are 0.65 mm pitch, wrong.

---

## 3. TI TCA8418RTWR, keypad scanner

Source: TI datasheet SCPS215G (rev. Jun 2018), https://www.ti.com/lit/ds/symlink/tca8418.pdf

* Orderable: **TCA8418RTWR** (3000/reel, marking PZ418, MSL 2, -40 to 85 C).
* Package: **WQFN-24 (RTW0024B)**, 4 x 4 mm, 0.5 mm pitch, 0.8 mm max height, **exposed pad 2.45 +/- 0.1 mm**.
* VCC 1.65-3.6 V, I2C up to 1 MHz (FM+), 3 uA standby, 50 us debounce, 10-event FIFO, ROW/COL internal pull-ups 105 k typ.
* JLC: **C138713**, 30,451 in stock, extended.

### 3.1 Pin table

| Pad | Pin | Connect to (10-key design, see 3.2) |
|---|---|---|
| 1 | ROW7 | unused -> pull-up to VCC |
| 2 | ROW6 | unused -> pull-up to VCC |
| 3 | ROW5 | unused -> pull-up to VCC |
| 4 | ROW4 | unused -> pull-up to VCC |
| 5 | ROW3 | key matrix row 3 |
| 6 | ROW2 | key matrix row 2 |
| 7 | ROW1 | key matrix row 1 |
| 8 | ROW0 | key matrix row 0 |
| 9 | COL0 | key matrix column 0 |
| 10 | COL1 | key matrix column 1 |
| 11 | COL2 | key matrix column 2 |
| 12 | COL3 | unused -> pull-up to VCC |
| 13 | COL4 | unused -> pull-up to VCC |
| 14 | COL5 | unused -> pull-up to VCC |
| 15 | COL6 | unused -> pull-up to VCC |
| 16 | COL7 | unused -> pull-up to VCC |
| 17 | COL8 | unused -> pull-up to VCC |
| 18 | COL9 | unused -> pull-up to VCC |
| 19 | GND | ground |
| 20 | RESET | active-low reset. Pull-up to VCC "if no active connection is used"; better: MCU GPIO + 10 k pull-up. Reset pulse >= 120 us, recovery 120 us. |
| 21 | VCC | 3.3 V, 100 nF + 1 uF at the pin (section 11.1 suggests a small and a larger cap) |
| 22 | SDA | I2C data, pull-up to VCC (shared bus pull-ups are fine) |
| 23 | SCL | I2C clock, pull-up to VCC |
| 24 | INT | active-low open-drain interrupt -> MCU GPIO, pull-up to VCC (10 k-47 k) |
| 25 (EP) | Thermal pad | GND. The datasheet's layout example (Figure 38) puts GND vias there; connect to GND. |

### 3.2 Matrix choice, address, unused pins

* **Use ROW0-ROW3 x COL0-COL2** (a 4 x 3 matrix, 12 positions, 10 populated). This is exactly TI's worked example
  (section 9.2, Figure 29/30 number pad), 7 pins. Key code in the FIFO = row x 10 + col + 1 (ROW0/COL0 = 1, ROW3/COL2 = 33),
  bit 7 of KEY_EVENT_A = 1 for press, 0 for release.
  A 2 x 5 matrix (ROW0-1, COL0-4) also works with 7 pins; pick whichever routes better.
* No ghosting concern for single presses. If you need any 3-key chords, keep the chord keys on separate rows and columns
  (ghosting discussion around Figure 27) or add diodes.
* **I2C address: 0x34** (7-bit; byte 0110 100x, 0x68 write / 0x69 read). Fixed, no address pins.
* Registers to set: CFG (0x01) bit KE_IEN = 1 (and INT_CFG / OVR_FLOW_IEN as wanted); KP_GPIO1 (0x1D) = 0x0F (ROW0-3),
  KP_GPIO2 (0x1E) = 0x07 (COL0-2), KP_GPIO3 (0x1F) = 0x00. ISR: read INT_STAT (0x02), drain KEY_EVENT_A (0x04) until 0,
  then write 1 to clear the K_INT bit.
* **Unused ROW/COL pins**: datasheet Pin Functions table: "If unused, connect to VCC through a pull-up resistor";
  section 9.2.1 gives the value: **10 k**. That is 11 resistors here (ROW4-7, COL3-9); a 4 x 10 k 0402 array cuts the count.
  (The internal 105 k pull-ups exist, but the datasheet still asks for external ones, so follow it.)

### 3.3 Footprint

* **Use `Package_DFN_QFN:WQFN-24-1EP_4x4mm_P0.5mm_EP2.45x2.45mm`** (EP = pad **25**, 4 separate paste pads, pads 0.875 x 0.3).
  TI RTW0024B land: pads 0.6 x 0.24 on a 3.8 mm span, EP 2.45. Matches.
* Do **not** use `Texas_RTW_WQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm`: that one is drawn for the bq25601 RTW package with a 2.7 mm EP.
  It would still solder, but the EP is larger than the TCA8418's 2.45 mm pad.

---

## 4. Load switch for camera and AMOLED panel (current-limited, fault-isolating)

Requirement (coordinator update): current limit / short-circuit protection with auto-retry or latch-off, thermal shutdown,
SOT-23-5/6, JLC-stocked, EN from 1.8 V logic, low IQ, quick output discharge, limits about 300 mA (camera) and 400 mA (panel).

Candidates checked against datasheets:

| Part | Limit range | Fault mode | QOD | EN VIH min | IQ on / off | SOT pkg | JLC |
|---|---|---|---|---|---|---|---|
| **Diodes AP22653AW6-7** | 125 mA-2.67 A (RLIM 10-210 k) | **latch-off** after 6 ms, reset by EN toggle | **yes, 600 Ohm** | 1.5 V | 120-140 / 0.1 uA | SOT-26 | C1511768, 3,922 |
| Diodes AP22653W6-7 | same | constant current, then thermal cycling | yes, 600 Ohm | 1.5 V | 120-140 / 0.1 uA | SOT-26 | C2158037, 7,088 |
| TI TPS2553DBVR | 75 mA-1.7 A (RILIM 15-232 k) | auto-retry (constant current + thermal cycling) | **no** (only TPS25530-1 in WSON) | 1.1 V | 100-150 / 0.1 uA | SOT-23-6 | C55266, 48,696 |
| TI TPS22950CDDCR | **0.5**-3.5 A only for the C (SOT) version | auto-retry | yes, 150 Ohm | 1.0 V | 44 / 0.2 uA | SOT-23-6 (DDC) | C7587833, 3,889 |
| TI TPS22917DBVR | **no current limit** | none | yes | 1.0 V | 0.5 / 0.01 uA | SOT-23-6 | C2681320, 19,749 |
| TI TPS22945DCKR | fixed 100 mA | | | | | SC-70-5 | too low |

**Pick: Diodes AP22653AW6-7 (latch-off, active-high), LCSC C1511768.** It is the only stocked SOT part that has all of:
adjustable limit down to the 300/400 mA range, thermal shutdown (145 C), output discharge, active-high EN, and a fault flag.
Latch-off means a shorted camera or panel is cut off after the 6 ms deglitch and stays off, so it cannot keep loading the
3.3 V rail; firmware sees FAULT low, logs it, and may retry by toggling EN. If you prefer automatic recovery, the
pin-compatible **AP22653W6-7 (C2158037)** holds the current at the limit until thermal shutdown cycles it (TSD hysteresis 40 C);
that still caps the draw at the limit but keeps loading the rail during a hard short.
TPS22917 (my first pick before the new requirement) is out because it has no current limit.

Source: Diodes DS41186 Rev. 5-2 (March 2026), https://diodes.com/datasheet/download/AP22652_AP22653_AP22652A_AP22653A.pdf

### 4.1 AP22653A / AP22653 SOT-26 pin table

| Pad | Pin | Connect to |
|---|---|---|
| 1 | IN | 3.3 V main rail. 0.1 uF (0.01-0.1 uF) ceramic to GND right at the pin. |
| 2 | GND | ground |
| 3 | EN | active high, from MCU GPIO. VIH 1.5 V min, VIL 0.4 V max, leakage +/-2 uA. Add 100 k pull-down so the load is off during MCU reset. |
| 4 | FAULT | open-drain, active low, 6 ms deglitch. 10 k pull-up to 3.3 V (RFAULT used in the datasheet tests), to an MCU input. Can be wired-OR between the two switches if you only need one fault line. |
| 5 | ILIM | RLIM to GND, 1 %, keep the trace short. 10 k <= RLIM <= 210 k. |
| 6 | OUT | to the load; 0.1-4.7 uF ceramic at the pin (improves short-circuit transient immunity), plus whatever the camera/panel needs. |

### 4.2 Current-limit resistors (datasheet best-fit equations, R in kOhm, result in mA)

ILIM_min = 28955 / R^1.075, ILIM_typ = 30321 / R^1.055, ILIM_max = 31033 / R^1.031.

| Load | RLIM (E96, 1 %) | ILIM min / typ / max |
|---|---|---|
| Camera (about 150 mA load, 300 mA limit) | **78.7 k** | 265 / 303 / 344 mA |
| AMOLED panel (about 200 mA peak, 400 mA limit) | **60.4 k** | 352 / 401 / 452 mA |

Notes: VIN operating range 3.0-5.5 V, UVLO rising 2.65 V typ / 2.95 V max, so it is fine on the 3.3 V rail but not on a
1.8 V rail. RDS(on) 65 mOhm typ / 135 mOhm max. Soft-start rise 0.3 ms typ at 3 V with 1 uF. The 1.5 V VIH works from 1.8 V
logic (the ESP32-P4 GPIO is lightly loaded here, so VOH sits near the rail), but margin is only about 0.3 V; if EN comes from
a 1.8 V domain, TPS2553 (VIH 1.1 V) has more margin.

### 4.3 Alternative: TI TPS2553DBVR (C55266), if stock or EN margin matters more than QOD

Source: SLVS841G (rev. Oct 2026), https://www.ti.com/lit/ds/symlink/tps2553.pdf

| Pad | Pin | Connect to |
|---|---|---|
| 1 | IN | 3.3 V, >= 0.1 uF at the pin |
| 2 | GND | ground |
| 3 | EN | active high, VIH 1.1 V, VIL 0.66 V |
| 4 | FAULT | open-drain, 7.5 ms deglitch, 10 k pull-up |
| 5 | ILIM | RILIM to GND, 15-232 k |
| 6 | OUT | load |

IOS_nom = 23950 / R^0.977, min 25230 / R^1.016, max 22980 / R^0.94: **88.7 k -> 265/299/339 mA**, **66.5 k -> 355/397/445 mA**.
No output discharge in the DBV part; UVLO 2.35-2.45 V; thermal shutdown 155 C; TPS2553DBVR-1 (latch-off) has only 5 in stock.

---

## 5. TI SN74AXC4T774PWR, 1.8 V modem UART <-> 3.3 V MCU

Source: TI datasheet SCES898C (Jul 2019, rev. May 2022), https://www.ti.com/lit/ds/symlink/sn74axc4t774.pdf

* Orderable **SN74AXC4T774PWR**, TSSOP-16, 0.65 mm pitch. **LCSC C1849453, 1,991 in stock** (extended). Each side 0.65-3.6 V,
  up to 310 Mbps 1.8 <-> 3.3 V. **DIRx and OE are referenced to VCCA.** All data I/Os have **71 k internal pull-downs**.
* KiCad: `Package_SO:TSSOP-16_4.4x5mm_P0.65mm`.

### 5.1 Pin table (PW package) and suggested wiring (A side = MCU at 3.3 V, B side = modem at 1.8 V)

| Pad | Pin | Connect to |
|---|---|---|
| 1 | DIR1 | tie to VCCA (A -> B) |
| 2 | DIR2 | tie to VCCA (A -> B) |
| 3 | A1 | MCU UART TX |
| 4 | A2 | MCU RTS (host request-to-send) |
| 5 | A3 | MCU UART RX |
| 6 | A4 | MCU CTS |
| 7 | DIR3 | tie to GND (B -> A) |
| 8 | DIR4 | tie to GND (B -> A) |
| 9 | OE | active low. GND = always enabled; or MCU GPIO with a pull-up to VCCA (high = all outputs Hi-Z). TI: to keep I/Os Hi-Z during power up/down, tie OE to VCCA through a pull-up. |
| 10 | GND | ground |
| 11 | B4 | modem CTS output (module -> host) |
| 12 | B3 | modem TXD (module -> host) |
| 13 | B2 | modem RTS input (host -> module) |
| 14 | B1 | modem RXD (host -> module) |
| 15 | VCCB | modem 1.8 V I/O rail (Quectel VDD_EXT), 0.1 uF (+1 uF) |
| 16 | VCCA | 3.3 V, 0.1 uF (+1 uF) |

### 5.2 Direction logic (Table 7-1, per channel)

| OE | DIRx | Result |
|---|---|---|
| L | L | **B data to A bus** (A output, B input) |
| L | H | **A data to B bus** (A input, B output) |
| H | X | both ports Hi-Z (isolation) |

So DIR = HIGH means A -> B. Extra points from the datasheet:
* VCC isolation: if either VCCA or VCCB < 100 mV, all I/Os go Hi-Z. Useful: when the modem is off (VDD_EXT = 0), the MCU side floats instead of back-driving the modem.
* The 71 k pull-downs mean an idle UART line goes LOW when its driver is off or Hi-Z, which a receiver sees as a break. If you need lines to idle high while a side is off, an external pull-up must be **<= 7 k** (section 7.3.9).
* Unused inputs must be held at VCC or GND (the pull-downs handle unused data pins; control pins must be tied).

---

## 6. SIM ESD and RF ESD

### 6a. TI TPD4E05U06DQAR (4-channel, 0.5 pF)

Source: SLVSBO7O (Dec 2012, rev. Aug 2024), https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf

* Orderable **TPD4E05U06DQAR**, USON-10 (DQA0010A), 2.5 x 1.0 mm, 0.5 mm pitch, 0.55 mm max height. VRWM 5.5 V.
* JLC: genuine TI **C138714 has only 171** in stock. Pin-compatible "TPD4E05U06DQAR" from TECH PUBLIC **C2827646 (38,496)**,
  BORN C920310 (20,159), MSKSEMI C2836386 (10,252). Clones have different capacitance/clamp specs; check before using one on RF.

| Pad | Pin | Connect to (SIM) |
|---|---|---|
| 1 | D1+ | SIM_DATA (IO) |
| 2 | D1- | SIM_CLK |
| 3 | GND | ground (wide pad) |
| 4 | D2+ | SIM_RST |
| 5 | D2- | SIM_VDD (1.8/3.0 V, below VRWM 5.5 V), or SIM_DET if VDD gets its own protection |
| 6 | NC | not connected; flow-through partner of pad 5, may be left floating or grounded |
| 7 | NC | flow-through partner of pad 4 |
| 8 | GND | ground (wide pad) |
| 9 | NC | flow-through partner of pad 2 |
| 10 | NC | flow-through partner of pad 1 |

Datasheet: place "as close to the connector as possible", route protected traces straight. Quectel modules usually also want
22 Ohm series resistors and 33 pF caps on SIM lines (module design guide, not checked here).

Footprint: **`Package_SON:USON-10_2.5x1.0mm_P0.5mm`** (made from the TI DQA package for TPD4E02B04; pads 0.3 x 0.55 at
x = +/-0.385). TI's own DQA0010A land (page 29): signal pads 0.565 x 0.2, GND pads 3/8 0.565 x 0.4, pad centres +/-0.4175.
`Package_DFN_QFN:Diodes_UDFN-10_1x2.5mm_P0.5mm` has the wide GND pads 3/8 (0.45) and is the closer copy of TI's land if you prefer.

### 6b. Murata LXES15AAA1-153 (RF line ESD)

Source: Murata specification LX-1-1111 Rev1.3, "Ceramic ESD Protection Device LXES**A series" (mirror:
https://static.chipdip.ru/lib/008/DOC032008949.pdf).

* Size code 15 = **1.0 x 0.5 mm (EIA 0402 / JIS 1005)**: L 1.00 +/- 0.05, W 0.50 +/- 0.05, T 0.33 max, terminal a = 0.20 +/- 0.10.
* Bidirectional, 0.05 pF typ, +/-15 kV air/contact (IEC 61000-4-2). **Rated voltage 4 V DC for the -153** (the -133 is the 15 V version).
  Fine on a DC-blocked antenna feed; do not put it on a line with DC bias above 4 V.
* Murata reference land (1005): a = 0.4 (gap), b = 1.2 (overall), c = 0.5 (width), i.e. two 0.4 x 0.5 mm pads, centres +/-0.4 mm.
* KiCad: `Diode_SMD:D_0402_1005Metric` works (pads 0.59 x 0.64 at +/-0.485, overall 1.56). On a 50 Ohm line I would make a
  custom pad pair at Murata's 0.4 x 0.5 / 0.4 gap to keep the stub small.
* JLC: genuine Murata **C86141 = 0 stock**. Stocked same-name parts: Leiditech **C5210978** (0402, 17,828), GOODWORK C53283248
  (0402, 7,719), TECH PUBLIC C7472903 (DFN1006-2, 23,147). These are clones; their datasheets were not checked.

---

## 7. LTE VBAT TVS and bulk cap

### 7a. TVS, about 4.5-4.7 V standoff, SOD-323

* **Prisemi PTVSHC3D4V5U**, SOD-323, unidirectional, **VRWM 4.5 V**, 1.4 kW (8/20 us), VC 15 V class, 850 pF.
  **LCSC C319211, 13,030 in stock.** Bidirectional sibling PTVSHC3D4V5B C110752 (4,590).
  Specs here are from the JLC/LCSC listings (https://jlcpcb.com/partdetail/C319211); the Prisemi PDF is only served through a
  signed link, so I could not read it. Check its VBR(min) against your VBAT maximum before release.
* KiCad: `Diode_SMD:D_SOD-323` (pad 1 = cathode -> VBAT, pad 2 = anode -> GND).
* With the rail regulated at 3.83 V a 4.5 V standoff has margin. If you ever feed the modem directly from the cell (up to
  4.4 V) the margin shrinks to 0.1 V; prefer the 3.8 V rail.
* Higher-stock 4.5 V alternative, but DFN1006-2 instead of SOD: Nexperia PTVS4V5D1BLYL **C478159 (338,373)**.

### 7b. Samsung CL32A107MQVNNNE

* **C49066 confirmed**: Samsung Electro-Mechanics CL32A107MQVNNNE, 100 uF, 6.3 V, X5R, +/-20 %, 1210. **161,556 in stock**
  (extended). (C521741 is an "old batch" entry with 0 stock.) KiCad `Capacitor_SMD:C_1210_3225Metric`.
* Expect well under 100 uF effective at 3.8 V DC bias; that is normal for X5R 6.3 V. Place at the module VBAT pins.

---

## 8. Battery connector (2-pin JST-PH) and polarity

* **JST S2B-PH-SM4-TB(LF)(SN)**: **LCSC C295747**, 743 in stock (genuine JST, 2 A, 100 V). Clone XYECONN XY-S2B-PH-SM4-TB
  C54582899 (3,225). PH is rated 2 A per contact, enough for a 2500 mAh cell with about 3 A LTE peaks at low battery only if
  peaks are short; keep the wires short.
* KiCad: **`Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal`**: pad 1 at x = -1.0, pad 2 at x = +1.0
  (y = -2.85, rear), two "MP" mounting pads at x = +/-3.35, y = +2.9. The plug opening faces **+y** (the body runs y -1.6 to +4.4).

### 8.1 The Adafruit / SparkFun convention

* There is no official JST standard for LiPo polarity. Adafruit, SparkFun and Particle use the same one: looking at the
  **battery plug's** mating face with the latch bump on top, **red (+) is on the right**
  (DigiKey forum: https://forum.digikey.com/t/polarity-standard-for-jst-ph-connectors-on-lipo-batteries/64548). Many RC
  packs are the opposite.
* Checked against Adafruit's own board files (adafruit/Adafruit-MicroLipo-PCB, "Adafruit USB C microlipo charger"): their
  `JSTPH2` footprint has pad 1 at x = -1, pad 2 at x = +1, contacts at the rear, opening toward +y (Eagle y points up), and the
  schematic nets are **CN2 pin 1 = GND, pin 2 = VBAT**. So, looking into the board header's opening with the PCB below,
  **GND is on the right and + on the left**. That matches the plug rule above (the header face is the mirror of the plug face).

### 8.2 What that means for the KiCad footprint (important)

KiCad's footprint has its opening toward +y (screen down), Adafruit's Eagle footprint has it toward screen up. The two pad 1s
are therefore on **physically opposite sides**. If you keep "pin 1 = GND" on the KiCad footprint, an Adafruit-convention
battery plugs in **reversed**.

* For Adafruit/SparkFun packs on `JST_PH_S2B-PH-SM4-TB...`: **pad 2 (x = +1.0) = GND, pad 1 (x = -1.0) = VBAT+**.
  In the KiCad editor with the opening pointing down the screen, GND is the right-hand pad.
* If you want pin 1 = GND in your schematic symbol, map symbol pin 1 to footprint pad 2 (or swap the pin numbers in a local
  copy of the footprint) and say so on the silkscreen ("+" and "-" marks next to the pads).
* Whatever you choose, measure the actual pack with a multimeter before first connection. BQ24074 BAT has no reverse-polarity
  protection.

---

## 9. Key switches

### 9a. Front keys under a membrane/keycap (top-actuated)

* **Omron B3U-1000P**: 3.0 x 2.5 mm, **1.6 mm** high (+0.15/-0.10), top-actuated, no boss, 2 SMT tabs, 12 V 50 mA.
  **LCSC C231329, 72,285 in stock** (extended). KiCad: **`Button_Switch_SMD:SW_SPST_B3U-1000P`** (pads 0.9 x 1.7 at x = +/-1.7).
  Product page: https://components.omron.com/us-en/products/switches/B3U (series is listed at 1.2 x 3 x 2.5 mm there, the
  1000P model is 1.6 mm per the datasheet tables and distributor data; get the Omron PDF before freezing the keycap stack).
  Clone hanxia HX-B3U-1000P-1.6N C49234121 (123,395, 1.5 mm listed).
* If 1.6 mm is too tall and you can afford 5 x 5 mm: XKB **TS-1187A-B-A-B**, 5.1 x 5.1 x **1.5 mm**, 1.6 N, **JLC basic part
  C318884 (815,259)**, KiCad `Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A`.
* XUNPU TS-1088-AR02016 (3.9 x 3 mm, basic C720477) is 2.0 mm high, too tall for this brief.

### 9b. Side keys: Panasonic EVQPUB02K

* **C2915192 confirmed: Panasonic EVQPUB02K, 1,249 in stock** (extended). JLC lists it as "SMD, 4.7 x 4.5 mm", 1.65 mm, 2.2 N.
* Panasonic product page (https://industry.panasonic.com/ap/en/products/control/switch/light-touch/number/evqpub02k):
  side push, 4.7 x 3.5 mm body (4.5 mm including the push plate), 1.65 mm mounting height, **J-bent** terminals, **without
  boss**, 2.2 N, 0.3 mm travel, 100,000 cycles, 10 uA 2 V to 50 mA 12 V.
* In the EVQPU part-number scheme, 6th character B = J-bent / 2.2 N / no boss, K = J-bent / 1.6 N / no boss, so **PUK and PUB share
  one land**: **`Button_Switch_SMD:Panasonic_EVQPUK_EVQPUB` is the right stock footprint** (pads "1","1","2","2" at
  x = +/-2.575, y = +/-0.85; descr points to Panasonic ATV0000CE5). Only 1,249 at JLC: order the quantity you need for all
  boards up front, or pre-book.

---

## B. USB-C VBUS input protection in front of the BQ24074

Source: TI BQ2407x datasheet SLUS810N (rev. Oct 2021), https://www.ti.com/lit/ds/symlink/bq24074.pdf

* **Confirmed**: IN absolute max **28 V** (section 8.1); "28-V input rating with overvoltage protection" (features).
  **BQ24074 VOVP = 10.2 / 10.5 / 10.8 V** (min/typ/max, VIN 5 -> 11 V), 175 mV hysteresis, 50 us deglitch. (The 6.6 V OVP
  belongs to the '72/'73/'75/'79, not the '74.) JLC: BQ24074RGTR **C54313** (4,426).
* So the charger itself survives anything up to 28 V, and stops charging above about 10.5 V. The protection only has to deal
  with ESD/surge spikes.

Recommendation:

1. **TVS on VBUS: SMF15A** (Littelfuse C151294 / MDD C123802), SOD-123FL, VRWM 15 V, VBR 16.7-18.5 V, VC 24.4 V at 8.2 A
   (10/1000 us), 200 W. Clamp stays below the 28 V abs max at full rated surge, and it does not conduct for any legal USB
   voltage (or a 9-12 V adapter by mistake). KiCad `Diode_SMD:D_SOD-123F`, cathode to VBUS.
   **Do not use a 5-5.5 V TVS (TPD1E10B06, SMF5.0A) on VBUS of this design**: a 9-12 V source would drive it into breakdown
   and burn it (or trip the PTC every time), throwing away the BQ24074's 28 V rating. TPD1E10B06 (C48260, VRWM 5.5 V) is
   still a good part for the CC1/CC2 and D+/D- lines.
   A flat-clamp option is TI TVS2200 (22 V), but genuine TI stock at JLC is 4 (C523793), only clones are stocked.
2. **PTC: optional, cheap insurance against a short in the connector/charger area.** If fitted: LUTE **1206L150/24NR**
   C20627120 (1.5 A hold, 3 A trip, 24 V, 130 mOhm max), `Fuse:Fuse_1206_3216Metric`. Choose a 16-24 V rated PTC, not a 6 V
   one, so it survives a mis-applied 9-20 V source. Hold current >= your BQ24074 ILIM setting (<= 1.5 A).
3. **eFuse (TPS2595): not advisable here.** TPS2595xx is 2.7-18 V with **20 V absolute maximum** (SLVSE57C,
   https://www.ti.com/lit/ds/symlink/tps2595.pdf), i.e. weaker than the BQ24074 it would protect (28 V), and adds cost
   and IQ. Only consider an eFuse if you later accept USB-PD higher voltages; then a 23 V part (TPS25947xx, C2864845) would be the
   family to look at.

Order on VBUS: USB-C VBUS pin -> (optional PTC) -> TVS to GND -> BQ24074 IN with its input cap.

---

## C. Battery NTC for the BQ24074 TS pin

From SLUS810N:

* TS sources **ITS = 75 uA** (72-78 uA) into the NTC (TS to VSS). Charging is suspended when VTS rises above
  **VCOLD = 2.1 V** (2.0-2.2 V) or falls below **VHOT = 0.30 V** (0.27-0.33 V), 50 ms deglitch.
* Footnote to the TS table: "These numbers set trip points of 0 C and 50 C while charging, with 3 C hysteresis ... with a Vishay
  Type 2 curve NTC with an R25 of 10 kOhm". Section 9.3.6: "The allowed temperature range for **103AT-2** type thermistor is
  **0 C to 50 C**". Section 10.2.2.3: use a 10 kOhm NTC (103AT-2) in the pack; if TS is not used, put a fixed 10 k from TS to VSS.
* Check: cold trip 2.1 V / 75 uA = 28.0 k, hot trip 0.3 V / 75 uA = 4.0 k. A B = 3435 K, 10 k NTC is 28.7 k at 0 C and 4.10 k at 50 C,
  so the window is about 0.5 C to 51 C. **Confirmed: a 10 k 103AT gives the 0-50 C charge window.** To widen it, the datasheet
  gives Rs/Rp equations (eq. 8, 9).

Two ways to wire it:

1. **Pack NTC (preferred, measures the cell itself)**: buy a 3-wire 2500 mAh pack with a 10 k NTC and use **JST
   S3B-PH-SM4-TB(LF)(SN), LCSC C265101 (22,388)**, KiCad `Connector_JST:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal`.
   There is no common pin order for 3-wire packs; get the vendor's drawing and map pins physically (same mirror trap as 8.2).
2. **Board NTC under the cell**: **Murata NCP15XH103F03RC**, 0402, 10 k +/-1 %, B25/50 = 3380 K (B25/85 3434 K),
   **LCSC C77131 (299,832)**, `Resistor_SMD:R_0402_1005Metric`. With B 3380 it is 28.2 k at 0 C and 4.16 k at 50 C, i.e. trips at
   about 0 C and 51 C. Place it under or touching the cell (thermal pad / kapton contact), TS to the NTC to VSS, with a 2-pin
   battery connector. Less accurate than a pack NTC because it sees board heat (charger, buck-boosts).

---

## Things not verified / follow-ups

* TPS63802 custom land pattern values were read from the TI drawing image; overlay-check the footprint against page 36 of the PDF.
* TPS63020 VINA wiring: datasheet figure shows VINA tied to EN/PS-SYNC; check the TPS63020EVM schematic for TI's exact VINA feed.
* Prisemi PTVSHC3D4V5U and the LXES15AAA1-153 / TPD4E05U06 clones: specs from JLC/LCSC listings only.
* Omron B3U-1000P: height 1.6 mm from datasheet excerpts and distributor data; the Omron PDF (A124-E1) refused automated download.
* Stock counts drift daily. TPD4E05U06 (genuine, 171), EVQPUB02K (1,249), JST S2B (743) and SN74AXC4T774 (1,991) are the
  thin ones; pre-order or allow the listed alternatives in the BOM.
