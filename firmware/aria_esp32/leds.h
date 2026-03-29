#pragma once
#include <Arduino.h>

// 4 regular LEDs — one per state
#define LED_IDLE       D2   // blue LED
#define LED_LISTENING  D3   // green LED
#define LED_PROCESSING D4   // yellow LED
#define LED_SPEAKING   D5   // red/magenta LED

void initLEDs() {
  // Use analogWrite — works on ESP32 Arduino core 3.x
  pinMode(LED_IDLE,       OUTPUT);
  pinMode(LED_LISTENING,  OUTPUT);
  pinMode(LED_PROCESSING, OUTPUT);
  pinMode(LED_SPEAKING,   OUTPUT);
  analogWrite(LED_IDLE, 0);
  analogWrite(LED_LISTENING, 0);
  analogWrite(LED_PROCESSING, 0);
  analogWrite(LED_SPEAKING, 0);
  Serial.println("LEDs initialised (analogWrite PWM)");
}

void updateLEDs(int state) {
  // All off first
  analogWrite(LED_IDLE, 0);
  analogWrite(LED_LISTENING, 0);
  analogWrite(LED_PROCESSING, 0);
  analogWrite(LED_SPEAKING, 0);

  float t = millis() / 1000.0;

  switch (state) {
    case 0: { // IDLE — slow breathing on blue
      int val = (int)((sin(t * 2.0) + 1.0) * 100.0);
      analogWrite(LED_IDLE, val);
      break;
    }

    case 1: { // LISTENING — green pulsing
      int val = 128 + (int)((sin(t * 5.0) + 1.0) * 63.0);
      analogWrite(LED_LISTENING, val);
      break;
    }

    case 2: { // PROCESSING — yellow rapid blink
      int val = (int)((sin(t * 12.0) + 1.0) * 127.0);
      analogWrite(LED_PROCESSING, val);
      analogWrite(LED_IDLE, (int)((1.0 - sin(t * 12.0)) * 40.0));
      break;
    }

    case 3: { // SPEAKING — magenta breathing + green accent
      float s = (sin(t * 6.0) + 1.0) / 2.0;
      analogWrite(LED_SPEAKING, 100 + (int)(s * 155));
      analogWrite(LED_LISTENING, (int)(s * 40));
      break;
    }
  }
}
