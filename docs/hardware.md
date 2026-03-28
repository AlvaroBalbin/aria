# ARIA Hardware Guide

## Parts List

| Part | Purpose | Notes |
|---|---|---|
| ESP32 (or ESP32-S3) | Pendant MCU | Any 38-pin ESP32 dev board works |
| INMP441 | I2S MEMS microphone | 3.3V, I2S digital output. Better than analog mics. |
| SSD1306 OLED 128x64 | Status display | I2C, 0.96" or 1.3" both work |
| NeoPixel ring (12 LEDs) | Status glow ring | WS2812B, 5V |
| 3.7V LiPo battery | Power | 500-1000mAh recommended |
| TP4056 module | LiPo charger | Micro-USB or USB-C input |
| Tactile button | Push-to-talk | Momentary, any size |
| Circular enclosure | Pendant housing | 3D print ~50mm diameter |

---

## Wiring Diagram

### ESP32 → INMP441 (I2S Microphone)

```
INMP441   →   ESP32
VDD       →   3.3V
GND       →   GND
L/R       →   GND   (selects left channel)
WS        →   GPIO 25
SCK       →   GPIO 26
SD        →   GPIO 34   ← input-only pin, perfect for audio in
```

### ESP32 → SSD1306 OLED (I2C)

```
SSD1306   →   ESP32
VCC       →   3.3V
GND       →   GND
SDA       →   GPIO 21
SCL       →   GPIO 22
```

### ESP32 → NeoPixel Ring

```
NeoPixel  →   ESP32 / Power
DIN       →   GPIO 5
5V        →   5V (from USB or boost converter)
GND       →   GND
```
> Note: NeoPixels need 5V. If powering from LiPo (3.7V), use a small boost converter or power from ESP32 USB pin when connected.

### ESP32 → Push Button

```
Button    →   ESP32
One leg   →   GPIO 0   (boot button — already on board, no extra wiring needed)
Other leg →   GND
```
> GPIO 0 is the boot button on most ESP32 boards — you don't need to add a new button. Just press the BOOT button to activate ARIA.

### Power

```
LiPo+ → TP4056 BAT+ → ESP32 VIN
LiPo- → TP4056 BAT- → ESP32 GND
```
Or simply: USB power bank → ESP32 USB port (easiest for hackathon demo)

---

## 3D Print: Circular Pendant

Target dimensions:
- Outer diameter: 50–55mm
- Depth: 18–22mm (enough for ESP32 + battery)
- Display hole: match your OLED size (28x27mm for 0.96" typical)
- LED ring channel: outer ring, 3mm groove for NeoPixel strip/ring
- Loop at top: 4mm hole for necklace cord

If you don't have time to model from scratch:
- Search Thingiverse for "ESP32 OLED pendant case"
- Or use a powder compact or watch case from a charity shop and hack it

---

## Assembly Tips

1. Solder header pins to INMP441 — it's tiny, work carefully
2. ESP32 + OLED + NeoPixel ring can be held in place with hot glue
3. Run a thin 3-wire cable from ESP32 to INMP441 (keep it under 5cm)
4. LiPo goes behind/under ESP32 board
5. Button wires through the case wall

---

## Raspberry Pi 5 (Base Station)

No extra wiring needed beyond:
- Pi screen connected via DSI or HDMI
- AirPods paired via Bluetooth (see setup.md)
- DAC board for room speaker (connect via 3.5mm to powered speaker)

Suggested Pi 5 setup for demo:
- Pi screen showing fullscreen dashboard
- Bluetooth to AirPods for the wearer
- DAC → small speaker so audience hears responses too
