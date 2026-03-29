#pragma once
#include <Arduino.h>

// 4 regular LEDs — one per state
#define LED_IDLE       D2   // blue LED
#define LED_LISTENING  D3   // green LED
#define LED_PROCESSING D4   // yellow LED
#define LED_SPEAKING   D5   // red/magenta LED

void initLEDs() {
  pinMode(LED_IDLE,       OUTPUT);
  pinMode(LED_LISTENING,  OUTPUT);
  pinMode(LED_PROCESSING, OUTPUT);
  pinMode(LED_SPEAKING,   OUTPUT);
  digitalWrite(LED_IDLE,       LOW);
  digitalWrite(LED_LISTENING,  LOW);
  digitalWrite(LED_PROCESSING, LOW);
  digitalWrite(LED_SPEAKING,   LOW);
}

void updateLEDs(int state) {
  // 0=IDLE, 1=LISTENING, 2=PROCESSING, 3=SPEAKING
  static unsigned long lastBlink = 0;
  static bool blinkOn = false;

  // All off first
  digitalWrite(LED_IDLE,       LOW);
  digitalWrite(LED_LISTENING,  LOW);
  digitalWrite(LED_PROCESSING, LOW);
  digitalWrite(LED_SPEAKING,   LOW);

  switch (state) {
    case 0: { // IDLE — slow breathing on blue LED using PWM
      float breath = (sin(millis() / 1500.0 * PI) + 1.0) / 2.0;
      analogWrite(LED_IDLE, (int)(breath * 255));
      break;
    }

    case 1: { // LISTENING — green pulsing
      float pulse = (sin(millis() / 400.0 * PI) + 1.0) / 2.0;
      analogWrite(LED_LISTENING, 128 + (int)(pulse * 127));
      break;
    }

    case 2: // PROCESSING — yellow rapid chase
      if (millis() - lastBlink > 120) {
        lastBlink = millis();
        blinkOn = !blinkOn;
      }
      digitalWrite(LED_PROCESSING, blinkOn ? HIGH : LOW);
      // Also flicker idle LED for effect
      digitalWrite(LED_IDLE, !blinkOn ? HIGH : LOW);
      break;

    case 3: { // SPEAKING — magenta breathing sync'd to speech
      float speak = (sin(millis() / 300.0 * PI) + 1.0) / 2.0;
      analogWrite(LED_SPEAKING, 100 + (int)(speak * 155));
      // Subtle green accent
      analogWrite(LED_LISTENING, (int)(speak * 40));
      break;
    }
  }
}
