#pragma once
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>

#define DISP_CS  D10
#define DISP_DC  A7
#define DISP_RST A3

Adafruit_ST7789 tft = Adafruit_ST7789(DISP_CS, DISP_DC, DISP_RST);

static int lastDrawnState = -1;
static String lastText = "";

void showStatus(const char* line1, const char* line2) {
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(40, 90);
  tft.print(line1);
  tft.setCursor(40, 120);
  tft.print(line2);
  lastDrawnState = -1;
}

void initDisplay() {
  delay(200);
  tft.init(240, 320);
  tft.setRotation(1);
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(4);
  tft.setCursor(100, 100);
  tft.print("ARIA");
  delay(1200);
  lastDrawnState = -1;
}

// Word-wrap and display text on the TFT
void showResponseText(const String& text) {
  tft.fillScreen(ST77XX_BLACK);

  // Header
  tft.setTextColor(ST77XX_GREEN);
  tft.setTextSize(2);
  tft.setCursor(10, 8);
  tft.print("ARIA says:");

  // Body — word-wrapped at size 2 (12px wide chars, ~26 chars per line)
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);

  int x = 10, y = 36;
  int maxX = 310;  // 320 - 10 margin
  int lineH = 20;
  int maxY = 230;

  for (int i = 0; i < (int)text.length() && y < maxY; i++) {
    char c = text[i];
    if (c == '\n') {
      x = 10;
      y += lineH;
      continue;
    }
    // Word wrap: if next char would overflow, wrap
    if (x + 12 > maxX) {
      x = 10;
      y += lineH;
      if (y >= maxY) break;
    }
    tft.setCursor(x, y);
    tft.print(c);
    x += 12;
  }

  lastDrawnState = -1;
  lastText = text;
  showingText = true;
}

static bool showingText = false;  // true when response text is on screen

void updateDisplay(int state) {
  // Don't overwrite response text while speaking
  if (showingText && (state == 3 || state == 2)) return;
  if (state == lastDrawnState) return;
  lastDrawnState = state;
  showingText = false;

  switch (state) {
    case 0:  // IDLE
      tft.fillScreen(ST77XX_BLACK);
      tft.setTextColor(ST77XX_CYAN);
      tft.setTextSize(3);
      tft.setCursor(120, 105);
      tft.print("ARIA");
      break;
    case 1:  // LISTENING
      tft.fillScreen(ST77XX_BLACK);
      tft.setTextColor(ST77XX_GREEN);
      tft.setTextSize(3);
      tft.setCursor(60, 105);
      tft.print("Listening...");
      break;
    case 2:  // PROCESSING
      tft.fillScreen(ST77XX_BLACK);
      tft.setTextColor(ST77XX_YELLOW);
      tft.setTextSize(3);
      tft.setCursor(75, 105);
      tft.print("Thinking...");
      break;
    case 3:  // SPEAKING
      tft.fillScreen(ST77XX_BLACK);
      tft.setTextColor(ST77XX_MAGENTA);
      tft.setTextSize(3);
      tft.setCursor(85, 105);
      tft.print("Speaking...");
      break;
  }
}
