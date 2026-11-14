# Concierge Phone (candybar)

Successor to ../voice-device (ESP32-S3 slab). Louis, 2026-11-13: "older handheld phone, candybar, camera on the back to
capture things while walking, at least 2-3 h active and 3 days standby, super compact and smooth, futuristic, many
features, fairly strong processor". Louis picked Candybar + ESP32-P4/C6. LTE built in (my call, Louis: "follow best practices").
No onboard LLM: the concierge runs in the cloud; the phone does wake word, voice detection, echo + noise cleanup (ESP-SR).

## Decisions so far
| Block | Choice | Why / source |
|---|---|---|
| Brain | Waveshare ESP32-P4-Module (SKU 28101: ESP32-P4NRW32X v3.x, 32 MB PSRAM in package, 16 MB flash, ESP32-C6FH8 over SDIO), 25x25 mm, 88 castellated pads | No P4 module or chip is stocked at LCSC/JLC (P4NRW32X C54540373: 0). Waveshare ~$10. JLC places it by consignment, or hand-solder. Reflow it only once. |
| Footprint | pcb/gen_wsp4.py -> phone.pretty/Waveshare_ESP32-P4-Module | Pads read exactly from Waveshare's DXF; numbers from the V1.1 schematic symbol |
| 3.3 V | TPS63802 buck-boost (C2845237), 2 A | Module alone needs >= 1 A budget (P4 0.5 A + C6 0.5 A per Espressif); TPS63001 (800 mA) is too small |
| Charger | BQ24074, 500 mA mode, as verified on the S3 board | carried over |
| Wi-Fi antenna | Module pad 2 LNA_OUT -> 50 ohm line -> pi match -> U.FL -> flex antenna | C6 has no antenna on the module |
| Flashing | USB-C -> P4 USB Serial/JTAG (GPIO24 D-, GPIO25 D+, pads 50/51), auto download mode | BOOT = GPIO35 (pad 62), EN = CHIP_PU (pad 87) |
| C6 recovery | test pads: C6_U0RXD/TXD (4/5), C6_IO9 (9, hold low), C6 reset = P4 GPIO54 (pad 82) | esp-hosted updates the C6 over SDIO normally (host_performs_slave_ota) |
| Speaker amp | MAX98357A from the battery, not 3.3 V | |
| Bluetooth | ESP32-C6: Bluetooth 5 LE only (no Classic: no A2DP headphones), shares the Wi-Fi antenna. Louis asked 2026-11-13 | add a classic BT audio module only if he wants headphones |
| Firmware | ESP-IDF >= 5.5.3 (v3.x chip), FreeRTOS, LVGL, esp-video, ESP-SR, Opus over WebSocket to a gateway on a home server, esp_modem for LTE, A/B OTA | |

## Module pin rules (from Waveshare schematic V1.1)
- GPIO14-19 are used inside the module (SDIO to the C6). Not on pads.
- GPIO54 (pad 82) drives the C6 reset: reserve. GPIO6 (pad 21) is the C6 -> P4 wake line in esp-hosted power save: reserve.
- GPIO39-48 (pads 67-76) are 1.8 V by default (VDD_IO_4 from pad 66 VFB_VO4): only for 1.8 V parts, or set the LDO.
- Deep-sleep wake only on GPIO0-15: keys / keypad interrupt / power key there.
- ADC1 on GPIO20-23 (pads 29-32): battery sense.
- DSI pads 34-39, CSI pads 41-46, USB HS pads 48/49 (ESD <= 1 pF if used).

## Camera + display (research back 2026-11-13)
| Block | Choice | Parts |
|---|---|---|
| Camera | OV5647 5 MP on the Raspberry Pi 15-pin 1.0 mm pinout, wired exactly like Espressif's ESP32-P4-Function-EV-Board J9. Start with Olimex CAMERA-OV5647-5MPIX-3.6mm (75 deg, EUR 12, says it works with P4). Host gives only 3.3 V. P4 ISP max 1920x1080, so photos are 1080p. | JUSHUO AFA07-S15FCA-00 C262721 (KiCad `Connector_FFC-FPC:JUSHUO_AFA07-S15FCA-00_1x15-1MP_P1.0mm_Horizontal`) |
| Camera pins | 1,4,7,10 GND; 2/3 D0N/D0P; 5/6 D1N/D1P; 8/9 CLKN/CLKP; 11 CAM_IO0 (10k pull-up to the switched camera 3V3); 12 NC; 13 SCL; 14 SDA; 15 3V3 (10 uF + 100 nF). 100 ohm series on every CSI line as on the EV board (R78-R90); 100 ohm diff pairs. | |
| Alt camera | SC2336 (Espressif kit, 10x10 mm head, needs 1.8/2.8 V LDOs + 24 MHz osc + I2C shifter): only if modules can be bought | |
| Display | 1.78-1.8" 368x448 AMOLED, CO5300 + CST820 touch (Waveshare V2) or SH8601 + FT3168 (Makerfabs), QSPI, official esp_lcd drivers. Host gives 3.3 V + PWR_EN only. Panels come off Waveshare ESP32-S3-Touch-AMOLED-1.8 boards (buy all from one vendor = one controller version). | Panasonic AXE534127 C6863072 (JLC 336), footprint pcb/gen_a4s.py |
| Alt display | Crystalfontz CFAL368448A0-0193DW 1.93" (bare panel $17.49, public datasheet, Hirose FH35C-19S C2889269) but no esp_lcd driver (CH13620) | |

## GPIO map (Waveshare module pads in brackets)
Supply domains read from the module schematic: GPIO0-38 and GPIO49-54 are ESP_3V3 (VDDPST_6 = ESP_3V3);
GPIO39-48 are on VDDPST_5 = ESP_LDO_VO4 (1.8 V by default, firmware-adjustable). So the 39-48 bank only gets
voltage-agnostic jobs: open-drain inputs with internal pull-ups and enable pins with VIH <= 1.2 V.
Deep-sleep wake is only on GPIO0-15 (LP IO, SOC_GPIO_VALID_DIGITAL_IO_PAD_MASK). SPI2 IO_MUX set 2 = GPIO28-33 (full speed QSPI).

| GPIO | Pad | Net | Notes |
|---|---|---|---|
| 0 | 88 | TALK_KEY | side key, wake |
| 1 | 16 | CAM_KEY | side shutter key, wake |
| 2 | 17 | KP_INT | TCA8418 keypad interrupt (open drain), wake |
| 3 | 18 | LTE_RI | modem ring/data indicator via shifter, wake |
| 4 | 19 | TP_INT | touch, tap to wake |
| 5 | 20 | ACC_INT | LIS3DH INT1, raise to wake |
| 6 | 21 | (reserved) | C6 -> P4 host wake inside esp-hosted |
| 7 / 8 | 22 / 23 | I2C_SDA / I2C_SCL | touch, camera SCCB, DRV2605L, LIS3DH, TCA8418 (same pins as the EV board) |
| 9 / 10 | 24 / 25 | I2S_BCLK / I2S_WS | shared by mics + amp (one full-duplex I2S, same rate, good for echo cancel) |
| 11 / 12 | 26 / 27 | I2S_DIN / I2S_DOUT | mics -> P4 / P4 -> amp |
| 13 | 28 | AMP_SD | MAX98357A SD_MODE (high = on, left channel) |
| 20 | 29 | VBAT_SENSE | ADC1, 1M/1M divider |
| 21 / 22 | 30 / 31 | LTE_TXD / LTE_RXD | via SN74AXC4T774 to the 1.8 V modem UART |
| 23 | 32 | LTE_RTS | via shifter |
| 24 / 25 | 50 / 51 | USB_DN / USB_DP | USB Serial/JTAG to USB-C, 0 ohm + ESD |
| 26 | 53 | LCD_RST | panel RESET and TP_RESET together |
| 27 | 54 | LCD_TE | tearing effect |
| 28-33 | 55-60 | LCD_CS, QSPI_D0, QSPI_CLK, QSPI_D1, QSPI_D3, QSPI_D2 | SPI2 IO_MUX |
| 35 | 62 | BOOT | test pad (strap) |
| 37 / 38 | 64 / 65 | U0TXD / U0RXD | test pads (logs) |
| 49 | 77 | LTE_CTS | via shifter |
| 50 | 78 | LTE_DTR | via shifter (sleep control) |
| 51 | 79 | LTE_PWRKEY | 2N7002 gate, open drain to PWRKEY |
| 52 | 80 | LTE_STATUS | via shifter |
| 53 | 81 | LTE_OE_N | both SN74AXC4T774 OE (10k pull-up = off at reset). Keep off until >= 3.5 s after LTE power-on: EG915U pins 18/19/30/38/39 (incl. DTR, RI) output 3.0 V for 2 s then 0 V for 1.2 s at boot, so nothing may drive them then |
| 54 | 82 | (reserved) | C6 reset inside the module |
| 39 | 67 | LTE_EN | TPS63020 EN (3.8 V modem rail) |
| 40 | 68 | CAM_EN | camera load switch |
| 41 | 69 | DISP_EN | panel load switch (panel PWR_EN pulled up to the switched rail) |
| 42 | 70 | CHG_N | BQ24074 open drain, internal pull-up |
| 43 | 71 | PGOOD_N | BQ24074 open drain, internal pull-up |
| 34, 36, 44-48 | | spare | 34/36 are straps: leave |

Keys (concept v2, 2026-11-13): only 4 keys, all direct GPIO, no TCA8418: TALK (front round button, GPIO0), side key
(GPIO1, camera / power), VOL_UP + VOL_DN (GPIO2 + one more LP pin; KP_INT freed). Touch does all navigation.
Outside (concept v2, enclosure/render_v2.py): 48 x 94 x 12 mm natural bead-blasted clear-anodized 6061 unibody,
fully rounded sides, one black glass front (display upper half, antennas under the glass top/bottom bands), camera top-left
on the back, USB-C + speaker + mic on the bottom end. Louis rejected v1 (gold + black caps + keypad): "chunky, colours not good".
DRV2605L EN tied high (standby by register). Modem RESET_N left open (power-cut via LTE_EN is the hard reset).

## LTE (research back 2026-11-13)
| Part | Choice | LCSC/JLC | Notes |
|---|---|---|---|
| Modem | Quectel EG915U-EU (EG915UEUAC-N05-SNNSA), Cat-1bis, LGA-126 23.6x19.9 | C7471302 (JLC 320, $12.02) | All Norwegian bands B1/3/7/8/20/28, CE. Sleep registered ~1.6 mA, LTE TX 0.5-0.8 A, plan 1 A peak. Lock LTE-only (`AT+QCFG="nwscanmode",3`): no 2G bursts (Telia 2G gone, Telenor end 2027) |
| Modem supply | TPS63020DSJR buck-boost set to 3.8 V | C15483 (20,815) | BQ24074 OUT is 4.4 V typ / 4.5 V max: above the modem's 4.3 V max, so never feed it directly. Feed the TPS63020 from BAT (protected cell), not through the BQ24074 path, so 1 A bursts can't trip its 250 mV/250 us short detect. |
| Bulk | 2-3 x 100 uF 1210 (CL32A107MQVNNNE) + 100 nF/33 pF/10 pF per rail, TVS 4.7 V | C49066 | VBAT_BB pins 32/33, VBAT_RF 52/53; wide copper |
| Control | PWRKEY (pin 15, >= 2 s low on), RESET_N (17, >= 100 ms): 2N7002 open-drain | C8545 | |
| Levels | UART is 1.8 V: TXS0104EPWR or SN74AXC4T774PWR powered from module VDD_EXT | C44955 / C1849453 | UART 921600 + RTS/CTS, CMUX + PPP via esp_modem GENERIC |
| SIM | Nano-SIM push-push with card detect, SHOU HAN NANO SIM 7P H1.37 | C7529384 (76k) | ESD TPD4E05U06DQAR (C22390021), 33 pF + 0 ohm per line |
| Antenna | Taoglas FXUB63.07.0150C flex (96x21 mm, U.FL, 698-3000 MHz) on Hirose U.FL-R-SMT-1(10) | C88373 | Buy antenna at DigiKey/Mouser. Pi match (0 ohm + 2 DNP) + DNP ESD pad near the feed, 50 ohm controlled-impedance trace (JLC impedance order) |
| Test pads | module USB D+/D-, USB_BOOT | | Quectel firmware updates |
| Plan | any data SIM | | ~0.9-1.5 GB/month at 1 h voice/day |

Footprints done (pcb/gen_eg915u.py, pcb/gen_nanosim.py; PDFs in datasheets/). EG915U pins used: VBAT_BB 32/33,
VBAT_RF 52/53, PWRKEY 15, RESET_N 17 (open), STATUS 20, VDD_EXT 29 (1.8 V, 50 mA: shifter B side), MAIN_RXD 34 / TXD 35 /
CTS 36 / RTS 37, MAIN_RI 39, MAIN_DTR 30, USIM1 VDD/RST/DATA/CLK 43-46, USIM1_DET 42 (51k pull-up to VDD_EXT; card in =
high, `AT+QSIMDET=1,1`), USIM1_GND 47, ANT_MAIN 60, USB_VBUS/DP/DM 8/9/10 + USB_BOOT 75 + DBG 22/23 to test pads
(never pull USB_BOOT at power-up). GND pads 55/59/61 solid (no relief). RESERVED pins open.
Layout: LTE flex antenna at one short end, C6 Wi-Fi antenna at the other, >= 10 mm from battery/display.
Risks: no esp_modem driver for EG915U (GENERIC + CMUX to be proven on a dev kit), radio in a hand/plastic case unmeasured,
JLC stock 320. Selling the device would need full CE/RED + SAR testing; personal prototypes only.

## Power (first pass, P4/C6 datasheets; display/camera/amp guessed)
- Active whole device ~433 mA from the battery -> 3 h ~1300 mAh (before LTE).
- Standby 72 h, C6 holding Wi-Fi + P4 deep sleep: ~250 mAh budget.
- => ~2000 mAh cell before LTE is added.
- LTE adds ~1.6 mA registered sleep (~115 mAh / 3 days) and roughly 150-250 mA average while streaming (Wi-Fi off then).
  First guess: ~2000 mAh for 3 h active + ~350 mAh standby -> 2500 mAh cell. Redo when the panel numbers are in.

## Antennas + battery (research back 2026-11-13)
- LTE: Taoglas FXP40.07.0085A flex 42.6 x 12.1 mm, U.FL, DigiKey 931-1327-ND (kr 47). B3/B1 good, B8 ok, B20 marginal,
  B28 weak, B7 11%. U.FL at the PCB edge next to it, short cable. Upgrade path: AVX 1004795 on-board chip + NanoVNA tuning.
- Wi-Fi: Molex 1461530050 (34.9 x 9 mm, balanced, 50 mm cable), DigiKey WM17084-ND (kr 21).
- A CLOSED aluminium unibody with antennas only under the front glass kills LTE low band (B20/B28 ~2-5 %). Needs an opening:
  best = non-metal bottom end band 8-12 mm (+6-10 dB low band), top end small dark insert for Wi-Fi. Body must be GROUNDED to
  PCB (masked/laser-cleared anodize pads + gold spring fingers every 10-15 mm near antennas). >= 5 mm antenna to metal (LTE).
- Battery at 12 mm body: VARTA 56427 201 018 (LPP 503759, 60.5 x 37.5 x 5.4, 1400 mAh, PCM + 10k NTC B3380, 2 A cont.,
  Farnell 2531265, MOQ to confirm). ~2 h talk + 3 days. 3 h talk needs ~1800-2000 mAh = ~7 mm cell = ~13.5-14 mm body.
- Modem bulk: >= 470 uF low-ESR at VBAT, LTE-only mode (PCM trip 2-4.5 A after 8-16 ms).

## Swiss-army-knife tools for the cloud agent (Louis 2026-11-13)
Hardware wanted: NFC (read/write/emulate), 125 kHz RFID, sub-GHz (CC1101-class, EU-legal TX lock), IR TX/RX/learn,
BadUSB/USB host via a USB-C data switch, microSD, camera, 2 mics, speaker, haptics, 6-axis IMU (gyro), magnetometer,
barometer, temp/humidity, light sensor, fuel gauge, GPS-less location via LTE cell/Wi-Fi, torch LED beside the camera,
laser ToF distance sensor through the back, Flipper-style expansion via USB-C SBU (UART/1-Wire/iButton dongle),
U2F/FIDO2 key (secure element), GPS/GNSS receiver (antenna at the top end, A-GNSS over LTE/Wi-Fi), Zigbee/Thread + BLE tools on the C6 (firmware), maybe nRF24 2.4 GHz.
Firmware: the phone exposes every capability as a typed tool over the WebSocket to the home-server gateway (MCP-style list:
take_photo, read_nfc, write_nfc, emulate_card, rfid_read, subghz_scan, subghz_replay, ir_send, ir_learn, usb_hid_type,
read_sensors, heading, altitude, record_audio, vibrate, ...), so the concierge can call them while Louis talks.
Safety: anything that transmits or emulates (sub-GHz TX, card emulation, IR blast, BadUSB) needs a physical Talk-button
press on the phone to confirm; the cloud can never fire it on its own. TX is region-locked to Norway/EU bands.

### Tool parts picked (research 2026-11-13, JLC stock that day)
| Function | Part (LCSC) | Notes |
|---|---|---|
| NFC | ST25R3916B-AQET (C17315217) + 27.12 MHz xtal (C70591) | SPI mode 1; ST RFAL / Flipper lib/nfc (GPL). Card emulation ok |
| NFC antenna | Molex 1462360111 23 x 27.3 mm ferrite-backed (C17350773) | beside the Talk button (not around it), under the front plate; tune with NanoVNA in the enclosure |
| 125 kHz | discrete Flipper-style: LEDC 125 kHz -> 74LVC2G34 -> series LC; BAT54 envelope -> TLV7011 (C193688) -> RMT; DMG1012T load-mod | coil ~50 turns 0.1 mm wound around the NFC antenna on its ferrite; EM4095 out of stock. Read 2-4 cm |
| Sub-GHz | CC1101RGPR (C29953) + 26 MHz (C15192); PE4259 (C470892) 433/868 path switch; Ignion NN03-320 chip (consign) or 0868AT43 (C3284550) | antenna at the TOP end (far from LTE B20 832-862 MHz). Range ~10-30 m. TX region-locked to ERC 70-03 table, alarm sub-bands + 315 MHz blocked |
| IR | 2-3 x Everlight IR12-21C (C53672) + DMG1012T; RX Everlight IRM-H638T (C91447) | top edge, through the dark insert; RMT 38 kHz |
| USB switch | TS3USB221ARSER (C128396); S,OE pulled low = flashing path at reset | 1D -> Serial/JTAG GPIO24/25, 2D -> HS OTG pads 48/49. Host mode would need 5 V boost + FUSB302B |
| USB-C SBU port | TPD6S300ARUKR (C2876380) + 2nd TS3USB221A (OE high at boot) -> UART GPIO37/38 | dongle with its own small MCU does iButton/1-Wire/GPIO |
| microSD | Molex 104031-0811 (C585350), 1.42 mm | SDMMC slot 0 (slot 1 = C6), 1-bit: D0 39, CLK 43, CMD 44. Firmware sets LDO VO4 = 3.3 V, UHS off |
| GNSS | u-blox MAX-M10S (C4153167) on I2C, V_BCKP from always-on rail; Pulse W3011 chip ant (C6604735) + SAW footprint | A-GNSS via AssistNow / LTE position inject. No GNSS in EG915U |
| Fuel gauge | MAX17048G+T10 (C2682616) | frees the VBAT ADC pin |
| IMU | ICM-42670-P (C3288646) replaces LIS3DH | |
| Magnetometer | MMC5603NJ (C404328) | far from speaker/LRA/battery leads |
| Barometer | BMP581 (C5362283) | shares the vented chamber |
| Temp/RH | SHT40-AD1B (C2848306) | vent + membrane, thermal slots |
| Light | OPT3004DNPR (C2655153) | IR-ink window in the front plate |
| Expander | PCAL6524HEAZ 24-bit (C3000497) | ~24 slow lines: LTE_EN/PWRKEY/DTR/STATUS/OE_N, CAM_EN, DISP_EN, CHG_N, PGOOD_N, AMP_SD, LCD_RST, USB_SEL, SBU_EN, SD_PWR/CD, RF_SW, RF_3V3_EN, IR_RX_PWR, TOF_XSHUT/INT, GNSS_RST, FUEL_ALRT, keys |
| Secure element | ATECC608B-MAHDA (C1518773) | FIDO2/U2F over USB HID |
| Torch | LM36011YKBR (C213547) + XL-3030UWC-1W (C2843891) | torch ~350 mA, not a 1 A flash |
| ToF | VL53L1CX (C190004), 4 m | on a spacer under a <1.5 mm 940 nm window, crosstalk cal after assembly |
| Skipped | nRF24L01P (no pins, MouseJack mostly patched), 4-bit SD, UV sensors (0 stock), hall (magnetometer covers it) | |
Pins after moving slow lines to the expander: 15-16 of 16 free GPIOs used (SD 1-bit 3, SPI3 3, CS NFC 50 + CC1101 51,
NFC IRQ 52, GDO0 53, 125 kHz carrier 40 / pull 41 / data 26, IR TX 42 / RX 20). GPIO39-48 boot at 1.8 V: keep 3.3 V
radio parts on an expander-switched rail until VO4 = 3.3 V. Space (+600-900 mm2) is the top risk; top end antennas crowded.

## Solid + drop-proof (Louis 2026-11-13: "nothing jiggles when I shake it, shock resistant if I drop it, smooth")
- Nothing loose: battery on stretch-release adhesive strips (tesa 70415-style pull tabs, replaceable) + 0.5 mm PORON foam
  pad pre-loading it against the PCB back; PCB screwed at 6 points (M1.6 into tapped bosses); every cable latched
  (A4S click, FPC latch, U.FL) and taped down with Kapton; antenna flexes on their own adhesive; keys pre-loaded (no play).
- Drops: aluminium rim stands 0.3 mm proud of the front plate (glass never lands first); 0.5 mm PORON / TPU bumpers at the
  four inner corners between PCB, battery and body; display bonded on a full frame of tesa 61395 (spreads impact);
  heavy modules soldered (no sockets except the screen + camera, both latched); no tall unsupported parts; bulk caps are MLCC
  not electrolytics. Glass: chemically hardened (Gorilla-type) cover for the panel if the panel's own glass breaks in tests.
- Smooth: no visible screws on the front or sides (screws only under the back), flush keys, 0.1-0.15 mm part gaps.

## Fail-safes (Louis 2026-11-13: "if components fail, other parts take over")
Built in by design (no extra board cost):
| If this fails | What takes over |
|---|---|
| Wi-Fi (C6) | LTE modem, automatic switch in firmware (and the reverse) |
| C6 hangs | P4 hard-resets it via GPIO54 and reloads it (esp-hosted) |
| LTE modem hangs | P4 cuts its 3.8 V rail (LTE_EN) and powers it back up |
| One microphone | the other mic alone (lose noise cancelling, keep voice) |
| Speaker / amp | reply shown as text on screen + haptic tap |
| Screen | voice-only mode: Talk key + haptics + speaker still work |
| Touch | 5-way keys do everything |
| Keypad chip (TCA8418) | TALK + CAMERA keys are wired direct to the P4, plus touch |
| Camera or panel shorts | each sits behind a current-limited load switch, so the 3.3 V rail and the rest survive |
| Bad firmware update | A/B slots: boots the last good one automatically; USB-C reflash always possible |
| Firmware hang | P4 hardware watchdogs (RTC + task WDT) reset it; brownout detector catches sagging supply |
| Battery dead or unplugged | BQ24074 power path runs the phone straight from USB-C |
| Over-discharge / short | protected cell (PCM) + firmware cutoff at 3.3 V |
| Hot or cold battery | BQ24074 TS pin on a 10k NTC (no charging outside ~0-50 C) |
| Boot self-test | every I2C part is probed at start; anything missing is reported and its feature switched off, the rest carries on |

Not duplicated: the P4 itself, its flash, the 3.3 V regulator and the charger. Doubling a main processor or power stage
needs a second full set plus switch-over logic that adds its own failure points; phones don't do it either.
Instead: parts run well inside their ratings, and all of them are recoverable over USB-C.

## MUST-verify before ordering
1. Waveshare to confirm the NRW32X build fits pin 54 -> VDD_HP and the 499k/499k + 22 pF feedback (public schematic shows the v1.3 build).
2. Module pad numbering with a meter on a real module (pad 2 LNA_OUT, 85/86 3V3, 83 GND).
3. Real standby current measured on a dev kit (Waveshare gives no module sleep number).
4. P4 waking from deep sleep must not reset the C6 (Wi-Fi link kept): test on the dev kit.

## Packaging v3 (enclosure/render_inside3.py, 2026-11-13)
Body grows to 48 x 100 x 13.5 mm: the 23 x 27.3 mm NFC ferrite antenna and the 19.2 mm fingerprint button can't both sit
below the display in 94 mm. Front, top to bottom: Wi-Fi/IR/sub-GHz + GNSS antennas at the top end, display (centre y +23.4),
NFC + 125 kHz coil (y -10, ferrite over the LTE module), fingerprint Talk button + light ring (y -31), LTE flex in the
bottom band. Back: battery 42 x 62 x 6, camera + torch + ToF + microSD above it. PCB 44 x 88.

## Area check (pcb/area.py, 2026-11-13, before sch_ui)
Courtyards only: front 3300 mm2 (core 1842, rf 868, power 416, sense 174) vs 3830 mm2 per side at 44 x 88; back 434 used
of ~1166 free beside the battery. UI section (+300-400) still to come. Packing ~95 % on the front is not buildable.
Levers: 0201 passives (~-250 mm2), move power/sensor parts to the back (~-600), grow the board, 6 layers for routing,
or cut LoRa (~-300 incl. its 2 switches + match). sch_rf asks: U40-U42 outside its range (accept), SX1262 TX match is
calculated not Semtech's, 433 MHz on the 868 Johanson chip loses 15-20 dB (Ignion NN03-320 consigned fixes it),
RF_3V3 switch must be >= 500 mA (raise AP22653 limit; done 2026-11-14: R118 39k = 564/636/710 mA). SIM: put the push-push holder at the right board edge behind a slot
in the side wall (the body is a front-loaded tub, so a SIM under the front plate would be unreachable).

## Area check v2 (2026-11-13 evening, all five sections wired: sch_core/power/rf/sense/ui = 439 parts, 280 nets)
Louis picked "grow to 50 x 104" (PCB 46 x 98, 4494 mm2 per side). Real courtyards (sch_core.py replaces area.py's CORE guess):
front 3791 mm2, back 645 mm2. Front usable after the top antenna band (7 mm) and the speaker box: ~3590 -> 105 %.
Back usable beside the 42 x 62 battery: ~1300 (top band y +19..+43 minus camera head, torch, ToF) -> 50 % already.
Levers measured: 0201 passives -206 front; SIM to the back top band -224; back can take only ~100 more at 70-75 %;
low-profile (<= 0.65 mm) parts under the battery on a midframe only helps the region under the battery, and the front
there is dominated by tall parts (front tall-only area is 3033). Best case at 50 x 104: ~3100 front = 86 %: not routable.
My earlier "grow 10 % + move 600 to the back" claim double-counted the back space. What does fit (target <= 70 % per side,
total demand ~4230 mm2 after 0201):
- grow to 54 x 108 x 13.5 (PCB 50 x 102): ~65 %, every feature kept (recommended);
- 54 x 104 (PCB 50 x 98): ~69 %, marginal;
- stay 50 x 104 and drop LoRa + VOC + spectral sensor + one sub-GHz band (~ -350): ~72 %, marginal.
DECIDED 2026-11-13: Louis picked 54 x 108 x 13.5 mm. PCB 50 x 102 (R4), 6 layers (F | In1 GND | In2 | In3 | In4 3V3 | B).
Layout (pcb/make_board.py anchors, front view, y up, origin = board centre): top band y > 44 = AE30 sub-GHz (top-left),
IR LEDs + receiver, top mic, Wi-Fi U.FL, AE31 GNSS + its keep-out (top-right); GNSS module (13, 39.6); P4 module (4.5, 20);
volume keys on the left edge, side key on the right; display socket J1 (0, 3.9); EG915U (-12.4, -10) under the NFC
antenna; SIM (right edge, y -10, card in through the right wall); Talk button + 4 ring LEDs at (0, -32); privacy switch on
the left edge (y -30); bottom: USB-C, main mic, LTE U.FL, speaker box (15.5, -47). Back above the battery: camera FPC J3,
torch D102 + ToF U61 beside the camera head (9..19, 31..41), microSD J71 (slot in the left wall), battery plug J10.
First placement: 439/439 parts, front courtyards 3665 mm2 (72 % of the board incl. the empty antenna band), back 785.
BMP581 (U54) landed on the back (air reaches it through the case seams: check the barometer vent in the case CAD).

## Water + dust (Louis asked 2026-11-13; estimates, not certified)
As drawn (open USB-C, speaker/mic holes, push-push SIM + microSD slots, privacy slider, 3 keys, seams): ~IP52-53.
IP54 for ~$2-4/unit, no layout change: ePTFE acoustic vents (speaker, 2 mics, barometer), silicone key gaskets, bonded
front glass + window tapes. IP67 for ~$8-15/unit + case changes: IPX7 USB-C receptacle, O-ring screw SIM tray with the
microSD behind the same door, magnetic (hall) privacy slider through the wall, sealed keys, pressure-rated vents, leak test
every unit. DECIDED 2026-11-13: Louis picked IP54 for the first build (keeps it openable for rework + antenna tuning);
IP67 = later case revision, no board change needed. Case CAD + order list must carry: ePTFE acoustic vents x4 (speaker,
2 mics, barometer), silicone key gaskets x4, VHB/adhesive frame tape for the front glass, camera/ToF/torch window tapes.

## Cost estimate (first full quote, 2026-11-13, +-25 %, ~10.8 kr/USD, Norwegian 25 % VAT included)
Per-phone parts ~$200-230 (display donor board $28, fingerprint $20, camera $13, EG915U $12, GNSS $11, P4 module $10,
sensors ~$32, antennas ~$18, battery ~$12, rest ~$60). JLC per order ~$400-580 (6-layer PCB $60-120, setup + 2 stencils
~$65, ~100 extended part types x $3 = $250-350, shipping ~$35). Case $150-260 each for 2, $80-170 each for 5.
Totals: 2 phones ~17,000-22,000 kr; 5 phones ~27,000-37,000 kr. Tools ~1,000-1,500 kr + NanoVNA ~1,000 kr once.
Replace with real numbers from the JLC cart + case-shop quotes once BOM/CPL/Gerbers and the case STEP exist.

## Review queue (integration notes, 2026-11-13)
- sch_power: BQ24074 now ILIM-resistor mode (R103 1.1k = 1.36-1.56 A input, R104 887 R = ~1.0 A charge; F100 raised to
  LUTE 1206L200/24NR 2 A hold to match). OPEN (review 2026-11-14, confirmed in SLUS810N p.12 + 9.3.4.1.1 p.22): VIN-DPM only
  works with EN2 = low, so in ILIM mode a 500 mA USB2 port or a Default-current USB-C source is pulled to ~1.46 A and
  collapses. Fix proposed (not applied, Louis decides): TUSB320LAI (C132554) in GPIO mode, UFP; its OUT1 (low = 1.5 A or
  3 A source) drives EN1 directly and EN2 through a DMG1012T inverter + RC, so Default/USB2 ports get USB500 with VIN-DPM
  and only real 1.5/3 A sources get ILIM mode (R103 -> 1.18k so the max stays under 1.5 A). No expander/GPIO/ADC pin is
  free (PCAL6524 24/24, PI4IOE 8/8, P4 ADC pins all used), so the hardware path needs none.
- LM36011 YKB DSBGA has 0.35 mm pitch: confirm JLC can assemble it, else swap to AW3641 (C164096, SOT-23-6) torch driver.
- BQ27441 gauge is high-side: J10 + = VBAT_PACK -> R122 10 mOhm -> VBAT, Kelvin traces to R122.
- Core must tie J4 USB-C D+/D- pairs to USB_DP / USB_DN (connector side of TPD6S300A) and SBU pins to SBU1/SBU2.
- sch_sense (40 parts): EXP_INT also carries OPT3004 + AS7341 INT. AS7341 on its own 1.8 V LDO (U58). MMC5603 0.4 mm
  WLP pads 0.23 mm: confirm JLC can place. VL53L1CX: driver switches it to 2.8 V I/O mode. ATECC608B order MAHDA only
  (TrustFLEX = 0x36 clashes camera, LoRaWAN variant = 0x59 clashes SGP41). Firmware: clear U51 internal pull-downs.
- Fingerprint: Waveshare UART Fingerprint Sensor (D): 14.2 mm glass, 19.2 mm steel rim, 2.0 mm thick, touch output,
  <16 uA sleep; NOT at JLC (Waveshare/RobotShop; (D) on backorder). Talk button grows to ~19 mm. Fallback HLK-ZW101.
  Click: Omron B3U-1000P under it. Supply rated 2.7-3.3 V vs our 3.308 V rail: check.
- Mics: 2x Infineon IM73D122 PDM (ultrasonic mode 4.56-5.04 MHz clk); 96 kHz capture unproven on P4 (raw PDM + SW filter).
- LoRa: SX1262 (C191341) + Epson 32 MHz TCXO (C3007493) on DIO3; RadioLib with BUSY via expander (custom HAL).
- SGP41 3 mA while measuring: on demand only. AS7341 needs a clear window + diffuser (not IR ink).
- sch_ui (68 parts): front +496 mm2, back +198 (microSD). Front courtyards now ~3800 of 3830 mm2 => grow or cut.
  Verify before order: XL-B1010 LED top/bottom-view polarity (diode test), microSD CD pad 9 vs 10, fingerprint (D)
  socket = (C) 8-pos 1.0 mm (assumed), FP rail 3.308 V vs 3.3 V max, speaker pad pitch 4.0 mm guessed.
  DRV2605L now on 3V3 (I/O limited to VDD+0.3). LP5815 at 0x2D (160 stock; LP5817 fallback).

## Board build state (2026-11-13 late)
- pcb/make_board.py: places all 439 parts; 184 small passives swapped to 0201 (not the NanoVNA-tuned or DNP ones, they stay
  0402 for hand rework); 0.3 mm keep-clear around every IC for router vias. pcb/check_nets.py: board == netlists (OK).
- pcb/route.py: In1 GND + In4 3V3 planes reached by via-in-pad (0.3/0.15 mm, JLC POFV: order "via-in-pad, filled+capped"),
  exposed pads get a 0.8 mm via grid; Freerouting routes F/In2/In3/B. First run (no via-in-pad, 0402, packed tight) stalled
  at ~290 unrouted: only 59 % of pins could escape. Second run in progress.
- pcb/jlc_files.py: jlc/BOM.csv, CPL.csv, not_placed.csv (+ --gerbers). 0201 LCSC numbers auto-picked (jlc/lcsc_0201.json):
  all 37 are JLC "extended" = ~+$110 loading fees per order. R116/R120 changed 78.7k -> 75k (78.7k 0201 has ~20 in stock).
- not placed by JLC: U1 P4 module (consign or hand-solder), DNP options, test pads, NFC/125k coil contacts, speaker + LRA pads.
- Routing attempts 2026-11-13: Freerouting 2.5 best = 93 unrouted (0.3 vias, no edge band) -> 47 open after pours;
  with JLC-safe rules (0.4/0.2 router vias, 0.5 mm edge band, RF 0.15 gap, hand-drawn LTE/Wi-Fi feeds) = 147 -> 120 open.
  Pin escape stalls at ~65 %. Freerouting is at its limit here. Options put to Louis: Quilter (free non-commercial tier,
  he signs up), DeepPCB (pay per use, KiCad plugin), or 8 layers + another Freerouting round.
- Louis picked Quilter (2026-11-13). pcb/gen_sch.py now writes a real KiCad schematic from the sch_*.py netlists (one
  symbol per part, pins = pads, nets as global labels; ERC: no electrical errors; its netlist == sch_*.py on all 280 nets).
  pcb/quilter_prep.py writes pcb/quilter/{B-place-and-route,A-route-only}/phone.kicad_{pro,sch,pcb}: vias/pours stripped,
  antenna feeds kept, In1 'gnd' / In4 'pwr', CSI + USB in net class 'differentialpair'. Both: schematic parity 0.
  B keeps 71 case-fixed parts + footprint keep-outs, 368 parts off-board for Quilter to place. Steps: pcb/quilter/README.md.
  Waiting on Louis's Quilter account (free tier: Quilter may train on uploads).
- ORDER GATE (Louis 2026-11-13: "I'm not gonna buy a unfunctional board"): nothing is ordered until
  `KPY pcb/order_check.py <routed board> 5` prints READY TO ORDER (DRC beyond the reviewed footprint-own list = 0,
  unrouted = 0, schematic parity = 0, JLC 6-layer limits, check_nets, BOM/CPL/gerbers, live stock via stock_check.py).
  Stock 2026-11-13: all 151 BOM lines cover 5 boards (lowest LP5815 160, antenna 184, EG915U 320); 131 extended parts.
  JLC Standard PCBA does 0.35 mm BGA pitch (LM36011 OK). Fingerprint (D) sold by Electrokit (SE). Gate run on the
  unrouted board: only 'everything routed' fails (499), as expected.
- Datasheet check 2026-11-13: J70 was WRONG (fingerprint (D) has a 6-pin 1.25 mm MX1.25/PicoBlade socket, not 1.0 mm
  SH) -> Molex 53261-0671 (C17393620); buy a 6P 1.25 mm double-ended lead, meter pin 1 = VIN before plugging. Ring LEDs:
  XL-B1010 datasheet top/bottom views contradict -> swapped to XL-1615RGBC-RF (C965840, pin 2 = anode, gen_xl1615.py).
  microSD detect (pads 9/10, normally open, not on the shell) and LM36011 footprint CONFIRMED. Board re-placed (439/439),
  Quilter files rebuilt, parity 0.
- QUILTER JOB SUBMITTED 2026-11-14 00:18: project "Concierge phone main board", job
  "Concierge phone v1 - place and route" (Quilter job), files = pcb/quilter/B-place-and-route.
  Settings: JLCPCB 6-Layer (with power plane) 3.5/3.5 mil, layer 5 switched Ground -> Signal (F | GND | sig | PWR | sig | B);
  fab 0.089 track/space, via 0.25/0.15, margin 0.3. Diff pairs: CSI + CC1101/LoRa balanced lines 100 ohm, 4 USB pairs 85;
  removed LRA and SPK. Single-ended 50 ohm: 12 RF nets (RF50 class minus the 6 balanced nets). Power nets: removed 10
  signal nets Quilter mis-flagged (LTE_*_3V, VOL_*, FB_3V3); VBAT/VBAT_PACK 3 A, SW*_LTE + SW*_3V3 2.5 A (SW*_3V3 added),
  3V8_LTE 2 A, 3V3/VSYS/VBUS/VBUS_CONN/TORCH 1.5 A, VINA_LTE 0.2 A. Converters: U10/L100 (C105, C106), U12/L101 (C108,
  C111), U32/L313 (C374, C375). Crystals, 241 bypass caps, U18 fanout: Quilter's auto picks. Next: pick best candidate,
  download KiCad, run pcb/order_check.py on it.

## 3D fit check (pcb/fit_check.py, 2026-11-14) - BLOCKS THE ORDER
First run on estimated sizes: 16 clashes. Real sizes (research 2026-11-14, sources in the session; drawings unless noted):
P4 module 3.30 total (was 2.6), MAX-M10S 2.5 typ / 2.7 max, EG915U 2.4, USB-C TYPE-C-31-M-12 3.26 top-mount,
IRM-H638T 4.00 (was 3.0), AMOLED panel + glass 33.6 x 41.2 x ~1.5 with its FPC leaving the bottom edge (11.5 wide) and
folding BEHIND the panel to a header ~12 above the panel centre (Waveshare STEP), so J1 must sit under the panel near
(0, panel_cy + 12), NOT at (0, 3.9). A4S socket AXE534127 is the official replacement of the donor board's AXE534124
(0.8 mated). Fingerprint (D): rim 2.0 + board 1.2 below the top, back parts not dimensioned. No sealed 1511 box speaker
exists: Same Sky CMS-16093-078S (16 x 9 x 3.0, springs, 0.7 W) needs its back volume from the case.
Battery: 42 x 62 x 6 is realistically 1600-2000 mAh, NOT 2500. 2500 mAh needs ~50 x 60 x 7.3 (Adafruit 328 class).
Column budget above the PCB top: J70 PicoBlade 3.4 + glass; P4 3.3 + display FPC + 1.5 screen => ~5.1 mm.
=> body_t ~= back 1.0 + 0.2 + battery + 0.3 foam + PCB + 5.1. With a 1.0 mm 6-layer PCB (phone practice):
   6.0 mm cell (50 x 60, ~2000 mAh) -> 13.6 mm body; 7.3 mm cell (50 x 60, 2500 mAh) -> 14.9 mm body.
Board changes needed either way (=> new Quilter run): J1 to ~(0, 36); 50 mm wide battery zone (moves R305, R122, TP9-11);
speaker spot 17 x 10 for CMS-16093; SW70 tact switch -> 0.35 mm snap dome under the fingerprint (phone practice);
U36 -> Vishay TSOP57238TT1 (3.95 x 3.95 x 0.8, 40 m, +-75 deg, upgrade); antenna flex placement (LTE flat under the
bottom glass band, Wi-Fi off the chip antennas); camera module with a real drawing (Pi-style 25 x 24 boards don't fit).
Louis 2026-11-14: no downgrades, top-tier parts, grow once by a few mm at most, no empty air.

## Fit pass applied (2026-11-14, Louis picked 14.9 mm + 2500 mAh)
Body 54 x 108 x 14.9; PCB 1.0 mm 6-layer; battery 50 x 60 x 7.3 2500 mAh (x -25..25, y -41..19); J1 (0, 35.8) under the
screen (FPC folds behind the panel); NFC antenna centre (0, -9.4); Talk ring (0, -30.65), ring LEDs at 30/150/210/330 deg;
SW70 = 4 mm snap dome; U36 = Vishay TSOP57338TT1 (C3742877, 0.8 mm); LS70 = Same Sky CMS-16093-078S pads (2.4 mm);
LRA bonded under the cover glass at (20, -34.5) over a "low" keep-out; LTE flex Taoglas FXP40 flat under the bottom
glass band, Wi-Fi flex Taoglas FXP74 (14 x 7) under the top band at (-1, 47.6); camera = Arducam OV5647 spy camera
(8.5 mm head, 15-pin flex). Charging raised to ~1.0 A (R104 887 R, R103 1.1k ILIM ~1.46 A).
fit_check.py: FITS (tightest 0.15 mm, LRA over C715/C716). order_check.py gate 6 = fit check. All gates pass on the
unrouted board except routing.
Quilter job 6af797c31a10ff2500b2ac49 (old layout) FAILED after 1 h 51 min: placement OK (6 candidates), then
"An unexpected error occurred during Router" x6 and "The board data could not be validated ... outdated or corrupted
design file" x6. Suspect: KiCad 10 file format (Quilter documents .kicad_pcb but no version range). Ask Quilter support.

## Board 1.2: review fixes (2026-11-14 night, 3 Opus reviews: electrical, fit, ordering)
Picture: pcb/shots/board_compare_1.0_1.1_1.2.png (pcb/board_compare3.py, snapshots shots/board_v1.0/1.1/1.2.json).
- Mounting: H1 (-21,-47), H2/H3 (+-6.9,-49), H4 (22,40), H5 (-9,42.5): M1.4 NPTH 1.6, keep-out D3.0 both sides, board-only
  footprints (MountingHole_M1.4_NPTH). Bosses D3.0 from the back wall set the PCB z (battery swelling can't lift the board).
  H2+H3 hold a 0.2 mm steel bracket over the USB-C shell. No screws in the top corners (AE30/AE31) or under the battery.
- fit_check.py: TOUCH parts must now REACH their object (+-0.2 mm) instead of being skipped; bosses, bracket and a 0.75 mm
  Talk plunger nub (fingerprint back, MEASURE the module) modelled; speaker z 0..3.15 per drawing.
- NFC: J30 + J35 KERUI KTR47003UT01-R pogo pins (C55342463, works 3.65-4.20, gap 3.83), placed by JLC.
- Speaker: LS70 at 7.55 mm from the box centre (Same Sky drawing p.2), box centre x 17.05.
- USB-C J4 1.2 mm further out (mouth ~1.2 mm behind the outer face, was 2.7). U71 mic to x -11.0. U36 IR to (12.8, 48.7),
  out from under the Wi-Fi flex.
- Charger: U20 TUSB320LAI (C132554) GPIO mode sets BQ24074 EN1/EN2 (Q100 inverter, R126/R127/C132): 1.5/3 A USB-C source ->
  ILIM 1.18k (1.27-1.46 A), anything else USB500 with VIN-DPM, dead battery USB100. R100/R101 removed (U20 gives Rd).
  OUT1 table verified in TUSB320 SLLSEN9F Table 7-3; LA pinout verified on its own datasheet p.3.
- Electrical: R118 39k (RF_3V3 limit >= 564 mA), F100 1206L200/24NR 2 A, R19 15k SIM data pull-up, U4 pin 4 to GND.
  R103/R104 stay 0402 (keep0402: no JLC 0201 for 887 R).
- Order tooling: CPL bottom rotation (180 - r), package corrections + ROT CHECK list, gerbers wiped per run, DRC severity-all
  + refill, mask-bridge/mic matchers tightened, fixed not-placed list, order files only on READY, JLC 3.5 mil rules in
  phone.kicad_pro and the Quilter projects. quilter_prep keeps H1-H5 fixed.
Gate on the unrouted 1.2 board: all PASS except "everything routed" and the 3D fit (J1 below).

### Still blocking the order (Louis)
1. J1 screen ribbon: the folded FPC is 2.75 mm above J1's mating face and U1 runs under it to ~2 mm before J1. Needs the
   donor panel's FPC measured (fold-to-header length, stiffener, parts on the tail), then either U1 down ~5 mm or a short
   custom adapter flex (JLC FPC). Also meter J1 pin 1 orientation on the donor Waveshare board.
2. Battery: only sourced 50x60x7.3 2500 mAh cell (Adafruit 328) is 2-pin, no NTC. Need a 705060-class cell with 3 leads +
   10k 103AT NTC, or fit R107 and accept no battery temperature check. Swelling margin is thin (0.2 + 0.3 foam).
3. Impedance: Quilter's stackup is 1.6 mm, the board is 1.0 mm. Get JLC's 1.0 mm 6-layer stackup (or order 1.2/1.6 mm with
   a published stackup), set layer order F|GND|sig|sig|PWR|B, re-run Quilter. The running job (6af7b87f...) is on 1.1 and
   is superseded either way.
Open checks (not blocking a fit): P4 module height 3.3 unverified; camera on the shared I2C bus when CAM_3V3 is off (bench
test); J1 stock shows canPresaleNumber -1068 (consign J1 if JLC can't supply); ROT CHECK parts in JLC's 3D preview.
After the final version: full build + start-up manual (Louis asked 2026-11-14).

## Board 1.3: 15.5 mm body, real screen, click-together parts (2026-11-14 morning)

Louis chose 15.5 mm + the LiPol 2400 mAh cell. Board top sits 6.2 mm under the glass top, the same as Waveshare's own
ESP32-S3-Touch-AMOLED-1.8 (its STEP: glass 0, board -6.2), so the screen FPC loop fits as Waveshare cut it.
- Stack: back wall 0.9, gap 0.2, battery LP665056 6.9 max (50 x 56 + PCM = 58, y -41..17), foam 0.3, PCB 1.04
  (JLC06101H-3313, stackup.py writes it into the .kicad_pcb), 3.6 mm under the screen panel, 5.1 under the cover glass.
- Screen underside (donor STEP sliced every 0.1 mm): panel back at -2.6; driver bump x 2.3..12.07, y 18.28..31.0 to -3.6;
  flex parts x 6.64..13.36, y 3.6..15.35 to -3.4; FPC U-loop x +-4.7, y 31.85..38.85 to -4.45; plug on J1 (0, 35.45).
  These are fit_check objects AND make_board height-limit keep-outs (numeric KEEP rules, MIN_GAP 0.15 taken off).
- U1 (module STEP: 25 x 25 x 0.8 board + 22.2 x 22.2 shield to 3.3) at (-9.0, 19.2) rot 180, shield left of the bump;
  fit_check SHAPES models rim + shield. Wi-Fi feed now east of the module (pad 2 at (3.5, 9.7)), U.FL J6 at (10.1, 9.7).
- U2 modem (-14.4, -11.0): 2 left, 1 down; LTE feed in one row at y 2.08 into J5 (-14.9, 3.6) rot 90.
- All three side keys on the RIGHT edge: SW72 vol up 36.4, SW73 vol down 28.0, SW71 power 19.5. H4 screw to (21.5, 41.8).
- Mic anchors U71/U72 restored (in 1.2 they had slipped into a code comment and were placed mid-board).
- No hand soldering (Louis: "click everything into place and screw"):
  J30/J35 NFC pogo -> BAT Wireless BWCD-L5.5W2.0H3.0 (C2826550, 5.5 free, ~4.8 working, gap 4.83);
  M70 -> G-Switch GT-BTP20002-0170B-020A spring (C55079717, working 2.0) under the tail of a Vybronics VG0832009L
  pressure-contact LRA (DigiKey), motor bonded under the cover glass at (20, -34.5), tail +y, spring at (20, -27.5);
  J31 -> Coilcraft 4308RV-404XJL 0.40 mH rod coil (consigned with U1), series C 3.9 nF + 150 pF (C415537 + C1645),
  copper-free rule areas under the rod and at its ends; U1 consigned (Waveshare ships to JLC), reflowed once, last.
  Talk plunger nub now 1.75 mm.
- Impedance (JLC calculator, 3313 stackup, outer layers): RF50 0.14 / 0.15, USB 90 ohm 0.125 / 0.127, CSI 100 ohm
  0.105 / 0.15 (route.py). Quilter given the stackup from the file (1.04 mm, gnd/sig/sig/pwr).
- Gate on the unrouted board: everything PASS (DRC 39 known, parity 0, JLC limits, nets, BOM 155 lines, stock 5 boards,
  3D fit 0 clashes) except "everything routed". Quilter job "Concierge phone v1.3 - route only" started 2026-11-14 14:13
  (Quilter job): A-route-only, every part pinned (both earlier B jobs could not place).
- Still open: download the Quilter candidate into quilter/result/ and run order_check; MUST-verify on samples: LRA tail
  pad spacing vs the spring, pogo working height, coil read range (~1-2 cm estimated); LiPol quote (Louis's OK to write).

## Parked (2026-11-14 afternoon)

- Quilter route-only job 1.3 FAILED after 11 min, "no candidates": router "unexpected error" (14:23) and DRC "The board data
  could not be validated" (14:24), the same error as job 1. All three Quilter jobs have now failed on Quilter's side; their
  support was asked on 2026-11-14 and is back Monday 2026-11-16. Nothing is routed.
- The build is paused for now (cost for 2 phones: see pcb/QUOTE.md).
  Options on the table when he comes back: lite board (fewer features, 4 layers, one side), off-the-shelf build, PCBWay student
  programme (50 % off making + assembly, max $200, needs "PCBWay" on the silkscreen).
- Public copy: github.com/Louistuis/concierge-phone (MIT), synced from this folder with private bits left out.
