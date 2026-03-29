#pragma once
#include <Arduino.h>

// 4 regular LEDs — one per state
#define LED_IDLE       D2   // blue LED
#define LED_LISTENING  D3   // green LED
#define LED_PROCESSING D4   // yellow LED
#define LED_SPEAKING   D5   // red/magenta LED

// ESP32 LEDC PWM channels
#define CH_IDLE       0
#define CH_LISTENING  1
#define CH_PROCESSING 2
#define CH_SPEAKING   3

void initLEDs() {
  // Setup LEDC PWM on each pin (ESP32-native, 8-bit, 5kHz)
  ledcAttach(LED_IDLE,       5000, 8);
  ledcAttach(LED_LISTENING,  5000, 8);
  ledcAttach(LED_PROCESSING, 5000, 8);
  ledcAttach(LED_SPEAKING,   5000, 8);
  ledcWrite(LED_IDLE, 0);
  ledcWrite(LED_LISTENING, 0);
  ledcWrite(LED_PROCESSING, 0);
  ledcWrite(LED_SPEAKING, 0);
}

void updateLEDs(int state) {
  // All off first
  ledcWrite(LED_IDLE, 0);
  ledcWrite(LED_LISTENING, 0);
  ledcWrite(LED_PROCESSING, 0);
  ledcWrite(LED_SPEAKING, 0);

  float t = millis() / 1000.0;

  switch (state) {
    case 0: { // IDLE — slow breathing on blue
      float breath = (sin(t * 2.0) + 1.0) / 2.0;
      ledcWrite(LED_IDLE, (int)(breath * 200));
      break;
    }

    case 1: { // LISTENING — green pulsing
      float pulse = (sin(t * 5.0) + 1.0) / 2.0;
      ledcWrite(LED_LISTENING, 128 + (int)(pulse * 127));
      break;
    }

    case 2: { // PROCESSING — yellow rapid blink + idle flicker
      float blink = (sin(t * 12.0) + 1.0) / 2.0;
      ledcWrite(LED_PROCESSING, (int)(blink * 255));
      ledcWrite(LED_IDLE, (int)((1.0 - blink) * 80));
      break;
    }

    case 3: { // SPEAKING — magenta breathing + green accent
      float speak = (sin(t * 6.0) + 1.0) / 2.0;
      ledcWrite(LED_SPEAKING, 100 + (int)(speak * 155));
      ledcWrite(LED_LISTENING, (int)(speak * 40));
      break;
    }
  }
}
