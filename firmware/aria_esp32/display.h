#pragma once
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
#define SCREEN_ADDR   0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

int16_t wavePoints[SCREEN_WIDTH];
int waveOffset = 0;

void initDisplay() {
  Wire.begin(21, 22); // SDA=21, SCL=22
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDR)) {
    Serial.println("SSD1306 not found");
    return;
  }
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(2);
  display.setCursor(28, 24);
  display.print("ARIA");
  display.display();
  delay(1200);
}

void drawIdleScreen() {
  display.clearDisplay();
  // Gentle sine wave
  for (int x = 0; x < SCREEN_WIDTH; x++) {
    wavePoints[x] = (int16_t)(sin((x + waveOffset) * 0.15) * 6 + 32);
  }
  waveOffset = (waveOffset + 1) % 100;
  for (int x = 0; x < SCREEN_WIDTH - 1; x++) {
    display.drawLine(x, wavePoints[x], x + 1, wavePoints[x + 1], SSD1306_WHITE);
  }
  display.setTextSize(1);
  display.setCursor(44, 54);
  display.print("ARIA");
  display.display();
}

void drawListeningScreen() {
  display.clearDisplay();
  // Energetic wave
  for (int x = 0; x < SCREEN_WIDTH; x++) {
    wavePoints[x] = (int16_t)(sin((x + waveOffset) * 0.25) * 14 + 32);
  }
  waveOffset = (waveOffset + 3) % 100;
  for (int x = 0; x < SCREEN_WIDTH - 1; x++) {
    display.drawLine(x, wavePoints[x], x + 1, wavePoints[x + 1], SSD1306_WHITE);
  }
  display.setTextSize(1);
  display.setCursor(28, 54);
  display.print("Listening...");
  display.display();
}

void drawProcessingScreen() {
  display.clearDisplay();
  // Spinning dots
  static int dotPos = 0;
  dotPos = (dotPos + 1) % 8;
  display.setTextSize(1);
  display.setCursor(22, 22);
  display.print("Thinking");
  String dots = "";
  for (int i = 0; i < (dotPos % 4); i++) dots += ".";
  display.print(dots);
  display.display();
}

void drawSpeakingScreen(const String& textSnippet) {
  display.clearDisplay();
  // Active wave
  for (int x = 0; x < SCREEN_WIDTH; x++) {
    wavePoints[x] = (int16_t)(sin((x + waveOffset) * 0.3) * 18 + 32);
  }
  waveOffset = (waveOffset + 5) % 100;
  for (int x = 0; x < SCREEN_WIDTH - 1; x++) {
    display.drawLine(x, wavePoints[x], x + 1, wavePoints[x + 1], SSD1306_WHITE);
  }
  display.setTextSize(1);
  display.setCursor(32, 54);
  display.print("Speaking");
  display.display();
}

void updateDisplay(int state, const String& extra = "") {
  // 0=IDLE, 1=LISTENING, 2=PROCESSING, 3=SPEAKING
  switch (state) {
    case 0: drawIdleScreen();           break;
    case 1: drawListeningScreen();      break;
    case 2: drawProcessingScreen();     break;
    case 3: drawSpeakingScreen(extra);  break;
  }
}
