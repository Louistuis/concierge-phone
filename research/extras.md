# Concierge phone: extras research (fingerprint Talk key, privacy switch, light ring, spectral, VOC, ultrasonic mics, LoRa)

Researched 2026-11-13. Pin tables and electrical values were read from the datasheets named in each section (PDF
downloaded and read, revision noted). Stock numbers come from the JLCPCB parts-search API
(`POST https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`) on 2026-11-13 and will
drift; all parts below are JLC "extended" unless marked basic. Product pages: `https://jlcpcb.com/partdetail/<LCSC>`.
Footprints were checked against `/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/` (KiCad 10).
Anything marked **(reseller data)** or **(not verified)** did not come from a manufacturer document.
Nothing was ordered; no other file was changed.

## Summary: recommended part per function

| # | Function | Pick | LCSC (JLC stock 2026-11-13) | Package | KiCad footprint |
|---|---|---|---|---|---|
| 1 | Fingerprint Talk key | **Waveshare UART Fingerprint Sensor (D)** (same mech as (C), SKU 16606): Ø14.2 mm sensing glass, Ø16.5 body, Ø19.2 steel rim, 2.0 mm stack, RST + WAKE pins, sleep < 16 uA | not at JLC (Waveshare (C) C431957 = 0). Buy Waveshare / RobotShop (CAD 24.27, backorder) | module | none: hand-solder 6 wires / FPC after assembly |
| 1b | Fallback if the button may grow to Ø19-21 x 5 mm | **Hi-Link HLK-ZW101** (V_SENSOR + TOUCH_OUT, 10 uA, EF01 protocol, MIT ESP32 lib) | not at JLC; AliExpress Hi-Link store | module, MX1.0-6P | none |
| 1c | Click under the sensor | **Omron B3U-1000P** (already in BOM) | **C231329** (72,285) | 3.0 x 2.5 x 1.6 mm | `Button_Switch_SMD:SW_SPST_B3U-1000P` |
| 2 | Privacy slide switch (SPDT, side) | **Alps SSSS811101** | **C109335** (41,967, $0.149) | 6.7 x 2.6 x **1.4 mm**, actuator out the side | `Button_Switch_SMD:SW_SPDT_PCM12` (same outline; check vs Alps land) |
| 2b | alt | C&K PCM12SMTR | C221841 (8,748, $1.27) | 6.7 x 2.6 x 1.4 mm | `Button_Switch_SMD:SW_SPDT_PCM12` |
| 2c | Hardware gate for mic CLK + camera EN | **TI SN74LVC2G34DCKR** (dual buffer, Ioff) powered from the switched rail | **C14461** (23,639) | SC-70-6 | `Package_TO_SOT_SMD:SOT-363_SC-70-6` |
| 3 | Light-ring driver | **TI LP5815DRLR** (3-ch, autonomous animation, shutdown 0.1 uA) | **C47262831** (only **160**) ; drop-in no-engine fallback LP5817DRLR **C47262829** (1,541) | SOT-583-8, 2.1 x 1.6 | `Package_TO_SOT_SMD:SOT-583-8` |
| 3b | Ring LEDs (4x) | **XINGLIGHT XL-B1010RGBT-HF**, common anode | **C22464515** (141,615, $0.0056) | 1.0 x 1.0 x 0.85 | none: 4 pads 0.45 x 0.45, 0.4 gap (sec. 3) |
| 4 | Spectral sensor | **ams AS7341-DLGM** (+ 1.8 V LDO XC6206P182MR C21659, 32,386) | **C2649486** (5,240, $7.51) | OLGA-8 3.1 x 2.0 x 1.0 | `Package_LGA:AMS_OLGA-8_2x3.1mm_P0.8mm` |
| 5 | VOC / NOx | **Sensirion SGP41-D-R4** | **C3659325** (2,264, $9.02) | DFN-6 2.44 x 2.44 x 0.85 | none: draw from DS Fig. 18 (sec. 5) |
| 6 | Mics x2 (PDM, ultrasonic mode) | **Infineon IM73D122V01XTMA1** | **C5563886** (2,820, $2.69) | PG-LLGA-5-3 4 x 3 x 1.2, bottom port | `Sensor_Audio:Infineon_PG-LLGA-5-2` geometry matches; renumber pads (sec. 6) |
| 7 | LoRa | **Semtech SX1262IMLTRT** chip-down | **C191341** (38,995, $3.21) | QFN-24 4 x 4, EP 2.7 | `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm` |
| 7b | 32 MHz TCXO | **Epson X1G0054410305** (TG2016SMN, ±0.5 ppm, 2.66-3.465 V, clipped sine) | **C3007493** (4,324, $0.51) | 2.0 x 1.6 x 0.73 | `Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm` (check pads) |
| 7c | 868 match | **Johanson 0900FM15K0039001E** IPD (replaces Semtech's 15-part network) | C7434807 (**0**): consign from DigiKey/Mouser; else Semtech discrete design | 0805 (2.0 x 1.25 x 0.8) | none: Johanson land on request |
| 7d | RF switches (TX/RX + antenna share) | **pSemi PE4259-63** x2 (same part as the CC1101 433/868 switch) | **C470892** (14,711) | SC-70-6 | `Package_TO_SOT_SMD:SOT-363_SC-70-6` |

## Top risks

1. **Fingerprint fit + supply.** No matcher module was found whose whole outline is <= 14 mm: the smallest is the
   Waveshare (C)/(D) class (Ø14.2 sensing, Ø19.2 steel rim). Waveshare lists (C) out of stock and (D) is on backorder;
   VIN is specified 2.7-3.3 V and our rail is 3.308 V (0.3 % over the stated max); protocol and matcher are vendor
   firmware (documented, not open source); FAR figures are vendor claims. The click needs a moving flex.
2. **GPIO budget.** New lines needing real GPIOs: fingerprint UART (2), SX1262 NSS + DIO1 (2), PDM CLK + DATA (2, of
   which DATA replaces the old I2S DIN) = **+5 GPIOs** on a P4 whose DESIGN.md table already has 15-16 of 16 free pins
   assigned. LoRa wake-on-packet also needs DIO1 on an LP GPIO (0-15). Everything else here goes on I2C or the
   PCAL6524 expander.
3. **Ultrasonic capture is unproven on the P4.** The hardware PDM-to-PCM filter is documented for 16-48 kHz PCM; 96 kHz
   PCM would need a 6.144 MHz PDM clock, above every candidate mic's max (IM73D122 5.04 MHz). Plan on raw PDM at
   4.8 MHz + software decimation (or test the hardware filter at 75 kHz). Mic response above 19 kHz is a typical curve,
   not a spec.

Also watch: LP5815 stock is only 160 (LP5817 fallback is pin- and address-compatible); SGP41 draws 3.0 mA while
measuring (not affordable in standby) and wants its own sealed pocket away from the SHT40; the IPD is not at JLC.

---

## 1. Fingerprint sensor in the round Talk button

### 1.1 Candidates (all integrated sensor + matcher MCU + UART)

| Module | Sensing face / outline | Thickness | Connector + pins | Touch/wake while matcher off | Standby | Matching | Templates | FAR / FRR | Protocol / library | Buy 1-5 pcs | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Waveshare UART Fingerprint Sensor (C)** SKU 16606 | window **Ø14.2**, body **Ø16.5** (+0/-0.1), steel rim **Ø19.2 ±0.1** | **2.0 mm** overall per drawing (sensor+rim 1.2, board 0.7, 0.6 parts); back connector height not dimensioned | 8-pin 1.0 mm unlatched socket on back (6 used): VIN 3.3 V, GND, RX, TX, **RST** (H = powered, L = sleep), **WAKE** (H when finger touches while asleep) | yes: RST low + WAKE | **< 16 uA** sleep | < 50 mA | 500 | < 0.001 % / < 0.1 % | 19200 8N1, 8-byte frames `F5 CMD P1 P2 P3 0 CHK F5` (XOR of bytes 2-6), fully listed in user manual V1.0; STM32 / RPi / Arduino demos | Waveshare $19.99, **out of stock** | [manual](https://files.waveshare.com/upload/4/45/UART_Fingerprint_Sensor_%28C%29_User_Manual_en.pdf) p.2-6 |
| **Waveshare (D)** (successor, "Cortex processor", 360°) | "R15.5" sensor (same text as (C)); drawing `UART-Fingerprint-Sensor-D-details-size.jpg` not read | not stated | VIN, GND, RX, TX, RST (H powered / L sleep), WAKE | yes | < 16 uA | < 50 mA | not stated | FRR < 0.1 % | 19200, uses the (C) command set | RobotShop CAD 24.27 (backorder); The Pi Hut | [wiki](https://www.waveshare.com/wiki/UART_Fingerprint_Sensor_(D)) |
| **Hi-Link HLK-ZW101** | sensor chip **Ø11.6 x 0.6**; module flange Ø21, body Ø19, top Ø17.05 | **5.0 mm** (2.1 front part) | MX1.0-6P vertical: 1 V_SENSOR (3.3 V touch supply, always on), 2 TOUCH_OUT (H = finger), 3 VCC (2.6-3.6 V), 4 TX, 5 RX, 6 GND | yes: VCC = 0, V_SENSOR on | **8 / 10 / 12 uA** (min/typ/max) | 35 / 40 / 45 mA | 50 | < 0.0001 % / < 3 % | 57600, EF01 packet protocol (AS608/R307 family); MIT lib [GavinnnTann/HLK-ZW-Fingerprint-Sensor](https://github.com/GavinnnTann/HLK-ZW-Fingerprint-Sensor) (ESP32 tested, Adafruit-style framing); RGB ring built in | AliExpress Hi-Link store (price not verified) | [datasheet V1.1](https://ask.hlktech.com/uploads/20241008/22b605e7d0488792499d5cd721869f0d.pdf) |
| Hi-Link HLK-ZW3020 / ZW3021 | sensor package **Ø13.6**, module Ø21 | not published | per lib README: VCC-S, INT, VCC-D, TX, RX, GND; no LED | yes (INT) | not published | not published | 100 | < 0.001 % (lvl 3) / < 3 % | 57600, EF01, auto-search | AliExpress | [hlktech ZW3020](https://hlktech.net/index.php?id=1338) |
| Grow R502-A | Ø22 outer, Ø19.3-19.5 inner, 15 mm sensing **(reseller data)** | ~5 mm excl. connector **(reseller data)** | MX1.0-6P: 1 3.3 V, 2 GND, 3 TXD, 4 RXD, 5 WAKEUP, 6 3.3VT (touch supply) (R503 family pinout) | yes (3.3VT + WAKEUP) | R503 manual: **2 uA** avg touch standby | R503: 20 mA | R503: 200 | R503: < 0.001 % / < 1 % | 57600 EF01; Adafruit_Fingerprint (Arduino) | AliExpress Grow store | [R503 manual v1.1](https://cdn-shop.adafruit.com/product-files/4651/4651_R503%20fingerprint%20module%20user%20manual.pdf) |
| Hi-Link HLK-FPM383C / FPM383F | ~21 mm **(reseller data)**; F = "mini", size not published | not published | F: 6-pin 1.0 mm | not confirmed | C: < 25 uA; F: 25 uA max **(reseller data)** | C ~45 mA; F 40 mA max | C 60; F 50 | C: < 1e-6 / < 1.5 % | 57600 | AliExpress; LCSC ML-FPM383C C5328918 (no specs) | listings only |
| Grow R503 | Ø28 / Ø23.5, 19 mm tall (panel mount thread) | too big | as R502 | yes | 2 uA | 20 mA | 200 | < 0.001 % / < 1 % | Adafruit lib | Adafruit $39.95 | R503 manual |

Square modules (Waveshare (F)/(G), 9.6 x 9.6 sensor, 20.4 x 33.4 board) and bare sensors (Microarray, Chipsailing,
FPC) were not shortlisted: bare sensors need a matcher library that is not open, and no vendor sells a Ø<14 mm
sensor + matcher combo in small quantities that I could find.

### 1.2 Recommendation

**Waveshare (D)/(C)-class module**: it is the only one whose sensing glass fits the 12-14 mm target (Ø14.2) and whose
stack is ~2 mm, and it has exactly the low-power split asked for (RST holds the matcher asleep, WAKE reports a finger,
< 16 uA). The visible part is the Ø19.2 steel rim around the Ø14.2 glass; whether the rim must touch the finger (it is
part of the "large touching area" in Waveshare's text) is not stated, so test before hiding it under the plate.
Buy 3 of (C)/(D) and 1 HLK-ZW101 as the fallback (better-documented touch rail and an MIT ESP32 library, but Ø17 face,
Ø19-21 body, 5 mm deep).

Wiring (keeps it to 2 GPIOs): UART TX/RX to a P4 UART; RST and WAKE to the PCAL6524 expander. Deep-sleep wake comes
from the tact switch on TALK_KEY (GPIO0), so WAKE does not need an LP GPIO: the press wakes the P4, firmware raises RST,
the finger is still on the glass (hold-to-talk) and the match runs (< 500 ms per Waveshare) while recording starts.
Feed VIN from 3.3 V; note the 3.3 V max.

### 1.3 Mechanics: module on a tact switch (Touch ID style)

- How others do it: Apple's iPhone 5s-8 Home button put the sensor under the cover on a flex above a dome switch;
  Android side-key sensors sit in the key cap and press a dome/tact switch. Same idea here.
- Stack (from the front): 1.5 mm plate with a hole for the rim (or Ø14.4 for the glass if the rim proves optional) ->
  module (2.0 mm) bonded into a carrier (aluminium or PC/ABS ring with a flange under the plate, 0.1-0.15 mm radial gap)
  -> 0.2-0.3 mm gap -> stiff disc (0.3 mm FR4 or steel) glued across the module's component zone with a ~1 mm nub
  -> **Omron B3U-1000P** on the main PCB under the nub. Return spring is the switch itself; add a 0.2 mm PORON ring
  under the flange against rattle (matches the "nothing jiggles" rule).
- B3U-1000P (C231329, 72,285): 3.0 x 2.5 x 1.6 mm, **1.50 ± 0.49 N**, pretravel **0.15 mm**, **200,000** operations
  min (Omron B3U datasheet). Design a hard stop at ~0.25 mm total travel so the module never crushes the switch (30 N
  max on the switch).
  Alternatives: Panasonic EVP-AKE31A C569760 (20,502), 3.9 x 2.9 mm, 1.6 N, IP67 (height not verified);
  Alps SKRPACE010 C139797 (155,360), 4.2 x 3.2 mm.
- Flex: remove the back socket and solder 6 wires or a single-sided rolled-annealed copper FPC with a service loop
  (bend radius >= 10x thickness) so it survives 100k+ presses.

## 2. Privacy kill switch

### 2.1 Part

**Alps SSSS811101** (C109335, 41,967 stock, $0.149). From the Alps sheet (SSSS8 series): SPDT, **1.4 mm tall**,
horizontal actuator **1.1 mm thick**, **1.5 mm travel**, 1.5 N operating force, rating 0.3 A 5 V DC max / 50 uA 3 V DC
min, 10,000 cycles, -40 to +85 °C, 6.7 mm body, two Ø0.8 bosses 3.0 mm apart (0.5 mm below the board face), ground
tabs. Actuator protrudes 1.3 mm (pos. 1) / 1.5 mm past the body edge.
Alternative **C&K PCM12SMTR** (C221841, 8,748, $1.27): same 6.7 mm body and 1.4 mm (0.055") height, 0.3 A 6 V DC,
-10 to +85 °C, Ø0.8 pegs on 3.0 mm, KiCad `Button_Switch_SMD:SW_SPDT_PCM12` (pads 1/2/3 at x = -2.25 / +0.75 / +2.25,
NPTH Ø0.9 at ±1.5). Shou Han MSK12C02 (C431540, 172,615) is the cheap one but rated only 50 mA.
Mechanics: PCB edge within ~0.3 mm of the inner wall; a small anodized slider in a 2.8 x 1.5 mm side slot captures the
actuator stub (travel 1.5 mm).

### 2.2 Circuit (hardware-enforced, firmware cannot override)

```
3V3 ──► SW pin 2 (common)
        pos "mics on"  (1-2) ──► 3V3_SENS
        pos "privacy"  (2-3) ──► PRIV_ON (100k to GND)

3V3_SENS ─┬─ IM73D122 VDD x2 (100 nF + 1 uF at each, per Infineon)
          ├─ SN74LVC2G34 VCC (pin 5), 100 nF
          ├─ 100k bleed to GND (rail drops fast when switched off)
          └─ 100k ─► expander input SENS_OK

SN74LVC2G34DCKR (C14461), pins (TI DS): 1 1A, 2 GND, 3 2A, 4 2Y, 5 VCC, 6 1Y
  1A ◄─ P4 PDM_CLK          1Y ─► both mic CLOCK pins (100k pull-down on 1Y)
  2A ◄─ expander CAM_EN_REQ  2Y ─► camera load switch EN (AP22653 EN), 100k pull-down on 2Y
```

- Privacy position: mics unpowered, the buffer is unpowered, so no clock reaches the mics and the camera EN is held low
  by its pull-down. TI specifies the '2G34 for partial power-down (Ioff), so neither the P4 clock nor the expander can
  back-power 3V3_SENS through the buffer inputs. Without the buffer, a running PDM clock would phantom-power an
  unpowered mic through its input ESD diode.
- Readback: two expander inputs, SENS_OK (rail present) and PRIV_ON. Valid states are 1/0 (mics allowed) and 0/1
  (privacy); 0/0 is mid-travel, 1/1 is a fault. The PCAL6524 interrupt reports changes.
- Switch current is ~2 mA (2 mics ~0.9-1.1 mA each + buffer), above the 50 uA minimum rating.
- Optional: a 0402 green LED + 10k from 3V3_SENS gives a firmware-independent "mic live" light.

## 3. Light ring around the Talk button

### 3.1 Driver comparison (JLC stock 2026-11-13)

| Part | LCSC (stock) | Ch | Autonomous breathing | Off current | On current | I2C addr | Package | Verdict |
|---|---|---|---|---|---|---|---|---|
| **TI LP5815DRLR** | **C47262831 (160)** | 3 (51 mA max) | **yes**, animation engine + STAT blink | **0.1 uA** typ / 0.3 max shutdown (I2C command); 22 uA standby | 0.15 mA (outputs off) / 0.23 mA at 25.5 mA | 0x2D | SOT-583-8 2.1 x 1.6 | **pick** |
| TI LP5817DRLR | C47262829 (1,541) | 3 | no (host animates) | same family | 0.15 / 0.23 mA | 0x2D | SOT-583-8 | stock fallback, same pins |
| TI LP5012RUKR | C1849481 (969) | 12 (4 RGB individually), 25.5 mA (35 mA at VCC >= 3.3) | no | 1 uA (EN low); 10 uA auto power-save | n/a | 2 addr pins (4 devices) | WQFN-20 3 x 3 | pick this instead if you want a per-LED "thinking" spinner; `Package_DFN_QFN:Texas_RUK0020B_WQFN-20-1EP_3x3mm_P0.4mm_EP1.7x1.7mm` |
| ISSI IS31FL3193-DLS2-TR | C2653363 (5,820) | 3 (42 mA) | yes | 2.5 uA max (SDB low), 3.5 uA software | 0.8 mA | 0x68-0x6B (AD pin), write-only; 0x68 clashes with ICM-42670 | DFN-10 3 x 3 | ok, needs an SDB line |
| Awinic AW2013DNR | C252440 (5,521) | 3 (15 mA) | yes | **90 uA** sleep, no shutdown pin | 450 uA | 0x45 | DFN-10 2 x 2 | rejected (standby) |
| TI LP5562TMX/NOPB | C544465 (1,080) | 4 | yes (3 engines) | n/a | n/a | n/a | DSBGA-12 | ok, BGA |
| ISSI IS31FL3195 | C3188252 (51) / C3188421 (5) | 4 | yes | | | | QFN-16 / WLCSP | no stock |
| SK6805-EC15 addressable | C2890035 (120,518) | per LED | n/a | draws current while dark (needs a load switch) | | needs a GPIO + RMT | 1.5 x 1.5 | rejected: no GPIO |

### 3.2 Pick: LP5815 + 4 x 1010 RGB under a frosted ring

- LP5815 (TI SNVSCP2B, Sept 2026): VCC 2.5-5.5 V (from 3.3 V, 1 uF at VCC), logic 1.8/3.3/5 V, I2C up to 1 MHz,
  outputs up to 5.5 V. DRL pins: **1 SCL, 2 SDA, 3 GND, 4 VCC, 5 STAT, 6 OUT2, 7 OUT1, 8 OUT0**. STAT must be low for
  the device to enter shutdown: tie it to GND (or an expander line if you want the hardware blink on OUT0).
- 4 x **XL-B1010RGBT-HF** (C22464515): 1.0 x 1.0 x 0.85 mm, **pin 1 common anode, 2 R, 3 G, 4 B**; IF max 20 mA per
  colour; Vf R 1.9-2.3 V, G/B 2.6-3.2 V (at 20 mA). Land (XINGLIGHT p.8): four 0.45 x 0.45 mm pads with 0.4 mm gaps
  (pad centres ±0.425 mm). All R cathodes to OUT0, G to OUT1, B to OUT2 (one colour for the whole ring, ~5 mA per LED
  -> 20 mA per channel with MC = 25.5 mA).
- Anodes go to the system rail (BQ24074 OUT / battery), not 3.3 V: blue Vf up to 3.2 V + 135 mV headroom does not fit
  under 3.3 V.
- Ring: 4 LEDs at 90° under a frosted PC light-guide ring of ~1.5 mm radial width around the button carrier; the
  carrier blocks light leaking into the sensor gap.
- Per-LED animation alternative: LP5012 drives the same 4 LEDs individually (12 channels), 1 uA with EN low.

## 4. Spectral colour sensor

**ams AS7341-DLGM**, **C2649486 (5,240, $7.51)**; AS7341-DLGT C2655145 (283). AS7343-DLGM C19085986 has only 50 at
$24.67, so AS7341 it is. From ams DS000504 v2-00:
- Package OLGA-8 **3.1 x 2.0 x 1.0 mm**, built-in aperture. Pins: **1 VDD, 2 SCL, 3 GND, 4 LDR (LED current sink),
  5 PGND, 6 GPIO, 7 INT (open drain), 8 SDA**. I2C address **0x39** (fixed). KiCad
  `Package_LGA:AMS_OLGA-8_2x3.1mm_P0.8mm` (its descr cites this datasheet).
- **VDD 1.7-2.0 V** (abs max 2.2 V): needs a 1.8 V LDO, e.g. Torex XC6206P182MR **C21659** (32,386). Digital pins
  (SCL/SDA/INT) abs max 3.6 V, VIH 1.26 V, so it can sit on the 3.3 V I2C bus with 3.3 V pull-ups. LDR pin up to 3.6 V.
- Current: active 210 uA typ, idle 35 uA, **sleep 0.7 uA** typ.
- Window: half-cone field of view **40°**; ams tests with a diffuser on top (ED1-C50). Needs a clear (unprinted) window
  plus a diffuser film; a black IR ink window will kill the visible channels. Geometry: to avoid clipping the 40° cone,
  window Ø ≈ (aperture) + 2 x gap x tan 40°, i.e. roughly Ø2 mm at a 0.5 mm air gap (my estimate; check with ams
  AN on optical design). Best spot: the back next to the camera and torch, so the torch (LM36011) is the light source
  for object colour; ambient light is already covered by the OPT3004 on the front.

## 5. VOC / air quality

**Sensirion SGP41-D-R4**, **C3659325 (2,264, $9.02)**. SGP40-D-R4 C2874215 (1,793, VOC only). Sciosense ENS160
C3659288 / C3659333: **0 stock**. From Sensirion SGP41 datasheet v1.0 (Dec 2021):
- DFN-6 **2.44 x 2.44 x 0.85 mm**, pitch 0.8, sensor opening Ø0.8 offset to one corner. Pins: **1 VDD, 2 VSS, 3 SDA,
  4 n/a (to GND), 5 VDDH, 6 SCL**, die pad = GND (solder it). VDD and VDDH on one supply, 1.7-3.6 V; RC filter on VDD,
  1 uF on VDDH. I2C **0x59**, 400 kHz.
- Land (Fig. 18, NSMD): 6 pads 0.55 x 0.40 mm, 0.8 pitch, outer span 2.3 mm; die pad 1.25 x 1.7 mm (stencil 1.05 x 1.5);
  stencil 125-150 um. No stock KiCad footprint (Sensirion libs cover SHT4x only): draw it.
- Current: idle 34 uA typ (105 max); **VOC+NOx measuring 3.0 mA avg at 3.3 V** (4.3 mA at 1.8 V); conditioning 4.2 mA,
  max 10 s after every power-up. Run it on demand only: continuous would cost ~216 mAh over 72 h.
- Assembly: put it in the last reflow, no board wash (DS 5.4).
- Vent (Sensirion SGP4x Design-In Guide v1.0, Aug 2020): the SGP4x already has a dust membrane, so no extra membrane
  (if one is added, large pore size); seal the pocket to the PCB with silicone/rubber; keep POM, PA and PMMA away
  (outgassing); coldest, lowest part of the device. **SGP41 heats the SHT40**: Sensirion recommends separate pockets,
  or ~2 cm apart with PCB slits around the SHT, and the SHT below the SGP. So: two small sealed pockets each with its own
  hole at the bottom end (SGP41 alone; SHT40 + BMP581 together), not one shared chamber.

## 6. Ultrasonic-capable PDM mics

### 6.1 Pick: 2 x Infineon IM73D122V01XTMA1 (C5563886, 2,820, $2.69)

From the Infineon datasheet rev 1.00 (2022-08-12; Chinese edition read in full, English 5-page preview):
- PG-LLGA-5-3 **4 x 3 x 1.2 mm**, bottom port, IP57. Pins: **1 DATA, 2 VDD, 3 CLOCK, 4 LR, 5 GND**.
- VDD 1.62-3.6 V. Clock modes: standby <= 350 kHz, low power 450-850 kHz, normal 1.2-1.65 MHz, high performance
  2.0-2.6 / 2.9-3.3 MHz, **ultrasonic 4.56-5.04 MHz (4.8 typ)**; duty 48-52 % above 3 MHz.
- IDD **900 uA typ / 1000 max at 4.8 MHz**; standby 25 uA. SNR 73 dB(A) at 3.072 MHz, 72 dB(A) at 4.8 MHz;
  sensitivity -26 dBFS ±1 dB; AOP 122 dBSPL; LFRO 20 Hz.
- Ultrasound: flat within +3 dB to **19 kHz**, resonance peak **37 kHz** (lab characterised, not production tested);
  the datasheet shows a typical ultrasonic response curve to ~80 kHz, but Infineon support says the mic is not fully
  characterised beyond the stated range
  ([community](https://community.infineon.com/t5/MEMS-microphones/IM73D122V01-ultrasonic-frequency-range-does-aliasing-occur-in-Low-Power-Mode/td-p/407003)).
- Stereo on one DATA line: mic A LR = GND (drives on falling clock edge), mic B LR = VDD (rising edge). 100 nF + 1 uF
  at VDD; optional ~100 Ω series on DATA.
- Footprint (DS Fig. 13): 4 SMD pads 0.75 x 0.45 mm, rows 0.7 mm apart, columns 1.7 mm apart, PCB sound hole Ø0.8,
  GND ring R0.58-R1.04 around the port. KiCad `Sensor_Audio:Infineon_PG-LLGA-5-2` (made for IM73A135) has the same
  geometry (pads at x -1.5/-0.8, y ±0.85, NPTH Ø0.8 at x +0.68): copy it and renumber pads to the IM73D122 table, check
  the pin-1 corner.

Alternates: Knowles SPH0641LU4H-1 C2879853 (**0** at JLC; ultrasonic mode 3.072-4.8 MHz, 845 uA typ, 10-80,000 Hz
range, "do not power up into ultrasonic mode"; KiCad `Sensor_Audio:Knowles_LGA-5_3.5x2.65mm`; buy DigiKey);
TDK T5838 MMICT5838-00-012 C7230692 (50 stock; ultrasonic mode 4.2-4.8 MHz, 500 uA, 68 dB SNR per TDK EVB guide);
Infineon IM69D130V01 C536262 (216; no ultrasonic mode); Vesper VM3011 C7149370 (0).

### 6.2 ESP32-P4 PDM RX (ESP-IDF master, `soc_caps.h` + `i2s_pdm.h` + I2S docs)

- `SOC_I2S_SUPPORTS_PDM_RX`, `SOC_I2S_SUPPORTS_PDM2PCM`, `SOC_I2S_SUPPORTS_PDM_RX_HP_FILTER` (23.3-185 Hz HPF),
  `SOC_I2S_PDM_MAX_RX_LINES = 4` on I2S0. PDM-to-PCM exists **only on I2S0 RX**; raw PDM works on all ports.
- PCM mode: CLK = fs x 64 (`I2S_PDM_DSR_8S`) or fs x 128 (`DSR_16S`); docs: "typically 16 kHz to 48 kHz".
  Raw mode: `sample_rate_hz` = PDM clock, 1.024-6.144 MHz, data read as raw bits (`I2S_PDM_RX_SLOT_RAW_FMT_DEFAULT_CONFIG`).
- **Can it give 96 kHz PCM?** Not through the hardware filter within mic specs: 96 kHz x 64 = 6.144 MHz CLK, above the
  IM73D122 max (5.04 MHz) and SPH0641/T5838 (4.8 MHz). Two paths, both to bench-test on a P4 dev kit:
  (a) hardware PDM2PCM at CLK 4.8 MHz, DSR_8S -> **75 kHz PCM** (Nyquist 37.5 kHz, matches the 37 kHz resonance;
  outside the documented 16-48 kHz range);
  (b) **raw PDM at 4.8 MHz** (stereo = 9.6 Mbit/s, 1.2 MB/s DMA) + software CIC/FIR decimation by 50 -> 96 kHz.
  Voice path for ESP-SR is then decimated to 16 kHz.
- "PDM full-duplex is not supported" on the P4: the MAX98357A moves to its own standard-mode I2S port (BCLK/WS/DOUT);
  AEC uses the playback buffer as reference. Pin cost vs the old shared I2S: PDM CLK + DATA (DATA reuses the old DIN)
  = +1 GPIO.

## 7. LoRa on the shared sub-GHz antenna

### 7.1 Chip-down SX1262 (recommended)

**SX1262IMLTRT C191341 (38,995, $3.21).** From Semtech DS.SX1261-2.W.APP Rev 1.1 (Dec 2017, LCSC copy):
- Pins: **0 EP GND, 1 VDD_IN (SX1262: tie to pin 10), 2 GND, 3 XTA, 4 XTB, 5 GND, 6 DIO3 (TCXO supply), 7 VREG,
  8 GND, 9 DCC_SW, 10 VBAT, 11 VBAT_IO, 12 DIO2 (RF switch control), 13 DIO1, 14 BUSY, 15 NRESET, 16 MISO, 17 MOSI,
  18 SCK, 19 NSS, 20 GND, 21 RFI_P, 22 RFI_N, 23 RFO, 24 VR_PA**.
- Land (Fig. 15-3): pads 0.30 x 0.80, pitch 0.5, C = 4.00, Z = 4.80, **EP 2.70 x 2.70** with GND vias ->
  `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm` (EP = pad 25).
- Supply VBAT/VBAT_IO 1.8-3.7 V (3.3 V rail). DC-DC: 15 uH on DCC_SW, 470 nF + 100 nF (ref schematic Fig. 14-2).
- Currents: sleep 600 nA (warm) / 160 nA (cold); RX LoRa 125 kHz 4.6 mA (DC-DC), boosted 5.3 mA; TX with the
  +22 dBm match: 90 mA at +14 dBm, 118 mA at +22 dBm. Continuous listening costs ~330 mAh per 72 h: use RX duty
  cycle / CAD if it must listen in standby.
- **TCXO**: Epson X1G0054410305 (TG2016SMN 32 MHz, ±0.5 ppm -40..85 °C, Vcc 2.66-3.465 V, 1.8 mA max, clipped sine;
  pins 1 NC, 2 GND, 3 OUT, 4 VCC). Per Semtech 4.1.4: OUT -> **220 Ω + 10 pF DC-cut** -> XTA, XTB open, VCC from
  **DIO3** set to **3.0 V** (`SetDIO3AsTCXOCtrl`; VBAT must be >= VTCXO + 200 mV, so 3.0 V works from 3.3 V). The
  1.8 V variant X1G0054410205 (C3007492) has 0 stock.
- **868 match**: Johanson **0900FM15K0039001E** IPD (0805, 862-928 MHz, TX IL 1.1 dB typ / 1.4 max, RX IL 1.5 / 2.0,
  pins 1 RFO, 3 RFI_N, 4 RFI_P, 6 SW_RFI, 8 SW_RFO, 2/5/7/9/10 GND). Per Johanson AN101 Fig. 4 it leaves only the VR_PA
  feed (L1 + C1/C2) and the SPDT. JLC has 0 (C7434807): consign it (DigiKey/Mouser) or copy Semtech's 15-part discrete
  network from the SX1262 868 MHz reference design files (values not reproduced here: take them from Semtech's BOM).
- **TX/RX switch**: PE4259 (C470892): RFC to the antenna-share switch, RF1/RF2 to SW_RFO/SW_RFI, CTRL (pin 4) from
  **DIO2** via 100 Ω/1 nF (`SetDio2AsRfSwitchCtrl`), pin 6 = VDD 3 V (single-pin mode). PE4259: 0.35 dB IL and 30 dB
  isolation at 1 GHz, P1dB 33.5 dBm, IDD 9 uA, all RF pins DC-blocked, tuning cap per pSemi Fig. 13 (pSemi DS
  DOC-03694-5.01).
- **Antenna share**: a second PE4259 at the antenna feed: RF1 = CC1101 path (its existing 433/868 PE4259), RF2 = SX1262
  path, CTRL from the expander line RF_SW. Each path then sees 2 switches (~0.7 dB at 868). Alternative low-loss part:
  Infineon BGS12SN6 C114953 (34,095; 0.25 dB at 1 GHz, P0.1dB 34 dBm, IDD 100 uA, but 0.25 mm pads on 0.4 mm pitch)
  or SKY13351-378LF C129189 (12,162; KiCad `RF:Skyworks_SKY13351_378LF`).
- EU868: firmware caps +14 dBm (25 mW) except 869.4-869.65 MHz (27 dBm, 10 % duty), in line with the existing TX
  region lock. Decide whether LoRa messaging needs the Talk-key confirmation rule.

### 7.2 Only NSS + DIO1 on GPIOs: workable

- RadioLib `Module::SPItransferStream` (master, `src/Module.cpp` l.364-421) polls BUSY via the HAL's `digitalRead()`
  before and after every command; if BUSY is `RADIOLIB_NC` it **delays 50 ms before and 1 ms after each command**
  (works, but a TX becomes ~0.5 s of overhead). Better: write a custom `RadioLibHal` (RadioLib ships an ESP-IDF example
  in `examples/NonArduino/ESP-IDF`) that maps virtual pin numbers to PCAL6524 pins, so BUSY and NRESET are read/driven
  over I2C (~0.1 ms per read at 400 kHz). NRESET via the expander is only used at init.
- DIO1 on a real GPIO (IRQ); put it on an **LP GPIO (0-15)** if the P4 must wake from deep sleep on a packet.
- SPI is shared with the ST25R3916 (mode 1) and CC1101 on SPI3: fine, each ESP-IDF `spi_device` keeps its own mode/clock.
- Meshtastic: the firmware now has a `variants/esp32p4/esp32p4.ini` base (Arduino via pioarduino, esp_hosted for the C6,
  Wi-Fi excluded "TODO"), but it is a whole firmware and its SX126x code expects BUSY on a GPIO. For interop inside the
  concierge firmware you would implement Meshtastic's over-the-air format (header, channel encryption, protobufs) on top
  of RadioLib yourself.

### 7.3 Module alternatives

| Module | Size | JLC | Notes |
|---|---|---|---|
| Seeed Wio-SX1262 | 11.6 x 11 mm (LCSC listing) | C55348741: 0 | TCXO on board, +22 dBm, 868-915/960 MHz; -N variant has RF pads; Seeed store |
| Vollgo SX1262S915N0S1 | 11.5 x 11.5 | C22380762: 92 | 915 MHz version only in the listing |
| Ebyte E22-900M22S | 14 x 20 | C411293: 1,448 ($7.36) | too big |
| Ai-Thinker Ra-01S / Ra-01SH | 17 x 16 (Ra-01S) | C724871: 355 / C2764087: 1,651 | too big |

Chip-down (QFN 4 x 4 + TCXO 2.0 x 1.6 + IPD 2.0 x 1.25 + PE4259 + inductor + ~8 caps) lands at roughly a Wio-sized
area (my estimate) and everything except the IPD is JLC-stocked, so chip-down wins.

## 8. I2C and pin notes for the new parts

- I2C addresses read in this pass: AS7341 0x39, SGP41 0x59, LP5815/LP5817 0x2D, IS31FL3193 0x68-0x6B (not chosen).
  Not checked here: re-verify the existing map (SHT40-AD1B, OPT3004 ADDR strap, BMP581 SDO strap, ICM-42670) when the
  schematic is drawn, the 0x44-0x47 region is crowded.
- Expander lines added: FP_RST, FP_WAKE, SENS_OK, PRIV_ON, CAM_EN_REQ (replaces CAM_EN), SX_BUSY, SX_NRESET, RF_SW
  (already listed), optional LED STAT.
- New P4 GPIOs: FP_TX, FP_RX, SX_NSS, SX_DIO1 (LP pin if wake wanted), PDM_CLK (+ PDM_DATA reusing I2S_DIN).

## Sources (read 2026-11-13)

- Hi-Link ZW101 datasheet V1.1: https://ask.hlktech.com/uploads/20241008/22b605e7d0488792499d5cd721869f0d.pdf
- Hi-Link ZW3020 page: https://hlktech.net/index.php?id=1338
- HLK-ZW library: https://github.com/GavinnnTann/HLK-ZW-Fingerprint-Sensor
- Waveshare (C) user manual: https://files.waveshare.com/upload/4/45/UART_Fingerprint_Sensor_%28C%29_User_Manual_en.pdf ; (D) wiki https://www.waveshare.com/wiki/UART_Fingerprint_Sensor_(D) ; RobotShop (D) https://ca.robotshop.com/products/round-all-in-one-capacitive-fingerprint-sensor-d-cortex-processor
- Grow R503 manual v1.1: https://cdn-shop.adafruit.com/product-files/4651/4651_R503%20fingerprint%20module%20user%20manual.pdf ; Adafruit https://www.adafruit.com/product/4651
- Omron B3U (via search of Omron datasheet copies), Alps SSSS811101 sheet (LCSC C109335), C&K PCM series sheet (LCSC C221841)
- TI SN74LVC2G34: https://www.ti.com/lit/ds/symlink/sn74lvc2g34.pdf
- TI LP5815 SNVSCP2B: https://www.ti.com/lit/ds/symlink/lp5815.pdf ; LP5012 https://www.ti.com/lit/ds/symlink/lp5012.pdf ; LP5817 https://www.ti.com/product/LP5817
- ISSI IS31FL3193 Rev. C (LCSC C2653363); Awinic AW2013 V1.5 (LCSC C252440); XINGLIGHT XL-B1010RGBT-HF (LCSC C22464515)
- ams AS7341 DS000504 v2-00 (LCSC C2649486)
- Sensirion SGP41 datasheet v1.0: https://sensirion.com/media/documents/5FE8673C/61E96F50/Sensirion_Gas_Sensors_Datasheet_SGP41.pdf ; SGP4x Design-In Guide: https://cdn.sparkfun.com/assets/6/c/d/d/7/GAS_SGP4x_Design-In_Guide_D1.pdf
- Infineon IM73D122V01 datasheet: https://www.infineon.com/assets/row/public/documents/30/49/infineon-im73d122-datasheet-cn.pdf
- Knowles SPH0641LU4H-1: https://akizukidenshi.com/goodsaffix/SPH0641LU4H-1.PDF ; TDK T5838 DS-000383 / AN-000278
- ESP-IDF: https://raw.githubusercontent.com/espressif/esp-idf/master/components/soc/esp32p4/include/soc/soc_caps.h , .../components/esp_driver_i2s/include/driver/i2s_pdm.h , https://docs.espressif.com/projects/esp-idf/en/latest/esp32p4/api-reference/peripherals/i2s.html
- Semtech SX1261/2 DS Rev 1.1 (LCSC C191341); Epson TG2016SMN spec (LCSC C3007493)
- Johanson 0900FM15K0039001E: https://www.johansontechnology.com/docs/4916/IPD-0900FM15K0039001E_7S2pKx8.pdf ; AN101 https://johansontechnology.com/docs/4476/Johanson_AN101.pdf
- pSemi PE4259: https://www.psemi.com/pdf/datasheets/pe4259ds.pdf ; Infineon BGS12SN6 rev 2.3 (LCSC C114953)
- RadioLib Module.cpp: https://github.com/jgromes/RadioLib/blob/master/src/Module.cpp ; Meshtastic P4 variant: https://github.com/meshtastic/firmware/blob/develop/variants/esp32p4/esp32p4.ini
