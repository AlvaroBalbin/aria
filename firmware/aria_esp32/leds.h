#pragma once
#include <FastLED.h>

#define LED_PIN     5
#define NUM_LEDS    12
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB

CRGB leds[NUM_LEDS];

unsigned long lastLedUpdate = 0;
int breathStep = 0;

void initLEDs() {
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(80);
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
}

// Breathing animation for IDLE (blue)
void breatheBlue() {
  if (millis() - lastLedUpdate < 30) return;
  lastLedUpdate = millis();
  breathStep = (breathStep + 1) % 128;
  uint8_t brightness = (uint8_t)(sin(breathStep * 0.049) * 80 + 90);
  fill_solid(leds, NUM_LEDS, CHSV(160, 220, brightness)); // blue-purple
  FastLED.show();
}

// Spinning purple for LISTENING
void spinPurple() {
  if (millis() - lastLedUpdate < 40) return;
  lastLedUpdate = millis();
  static int pos = 0;
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  for (int i = 0; i < 4; i++) {
    leds[(pos + i * 3) % NUM_LEDS] = CHSV(200, 255, 200 - i * 40);
  }
  pos = (pos + 1) % NUM_LEDS;
  FastLED.show();
}

// Fast spin white for PROCESSING
void spinWhite() {
  if (millis() - lastLedUpdate < 20) return;
  lastLedUpdate = millis();
  static int pos = 0;
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  for (int i = 0; i < 3; i++) {
    leds[(pos + i * 4) % NUM_LEDS] = CHSV(0, 0, 220 - i * 60);
  }
  pos = (pos + 1) % NUM_LEDS;
  FastLED.show();
}

// Pulsing green for SPEAKING
void pulseGreen() {
  if (millis() - lastLedUpdate < 20) return;
  lastLedUpdate = millis();
  breathStep = (breathStep + 3) % 128;
  uint8_t brightness = (uint8_t)(sin(breathStep * 0.049) * 100 + 120);
  fill_solid(leds, NUM_LEDS, CHSV(96, 230, brightness)); // green
  FastLED.show();
}

void updateLEDs(int state) {
  // 0=IDLE, 1=LISTENING, 2=PROCESSING, 3=SPEAKING
  switch (state) {
    case 0: breatheBlue();  break;
    case 1: spinPurple();   break;
    case 2: spinWhite();    break;
    case 3: pulseGreen();   break;
  }
}

void ledOff() {
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
}
