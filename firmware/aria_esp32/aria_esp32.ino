/**
 * ARIA Pendant Firmware — Arduino Nano ESP32
 *
 * What this does:
 *   - Tap the button → tells Pi 5 to start/stop listening (toggle)
 *   - Pi 5 sends state updates + response text → OLED + LEDs show it
 *   - No microphone on pendant; AirPods/headphones handle audio in + out
 *
 * Libraries needed (Arduino Library Manager):
 *   - WebSockets by Markus Sattler
 *   - Adafruit GFX Library
 *   - Adafruit ST7735 and ST7789 Libraries
 *   - ArduinoJson
 */

#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include "display.h"
#include "leds.h"

// ── Configuration ─────────────────────────────────────────────────────────────
#define WIFI_SSID "Ashwin\xe2\x80\x99s Phone"
#define WIFI_PASS "3.14159265"

const char* PI_HOST  = "172.20.10.14";
const int   PI_PORT  = 8000;
const char* WS_PATH  = "/ws/pendant";

#define BUTTON_PIN D6   // physical button (other leg to GND)

// ── State machine ─────────────────────────────────────────────────────────────
enum State { IDLE = 0, LISTENING = 1, PROCESSING = 2, SPEAKING = 3 };
volatile State currentState = IDLE;

WebSocketsClient ws;
bool wsConnected = false;

// ── WebSocket events ──────────────────────────────────────────────────────────
void onWebSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  if (type == WStype_CONNECTED) {
    Serial.println("WS connected to Pi");
    wsConnected = true;
    setState(IDLE);

  } else if (type == WStype_DISCONNECTED) {
    Serial.println("WS disconnected — reconnecting...");
    wsConnected = false;

  } else if (type == WStype_TEXT) {
    Serial.print("WS recv: ");
    Serial.println((char*)payload);

    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, payload, length);
    if (err) {
      Serial.print("JSON parse error: ");
      Serial.println(err.c_str());
      return;
    }

    // Handle state updates
    const char* state = doc["state"];
    if (state) {
      if      (strcmp(state, "idle")       == 0) { lastText = ""; showingText = false; setState(IDLE); }
      else if (strcmp(state, "listening")  == 0) { lastText = ""; showingText = false; setState(LISTENING); }
      else if (strcmp(state, "processing") == 0) setState(PROCESSING);
      else if (strcmp(state, "speaking")   == 0) setState(SPEAKING);
    }

    // Handle response text for OLED display
    const char* text = doc["text"];
    if (text) {
      Serial.print("Display text: ");
      Serial.println(text);
      showResponseText(String(text));
    }
  }
}

// ── State management ──────────────────────────────────────────────────────────
void setState(State s) {
  currentState = s;
  lastStateChange = millis();
  Serial.print("State -> ");
  Serial.println(s == IDLE ? "IDLE" : s == LISTENING ? "LISTENING" : s == PROCESSING ? "PROCESSING" : "SPEAKING");
}

// ── WiFi ──────────────────────────────────────────────────────────────────────
void connectWiFi() {
  Serial.print("Connecting to: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nFAILED — status: " + String(WiFi.status()));
    Serial.println("0=IDLE 1=NO_SSID 2=SCAN_DONE 3=CONNECTED 4=CONNECT_FAILED 6=DISCONNECTED");
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(200);

  Serial.println("\n=== ARIA Pendant ===");

  pinMode(BUTTON_PIN, INPUT_PULLUP);  // LOW when pressed

  initDisplay();
  initLEDs();
  connectWiFi();

  ws.begin(PI_HOST, PI_PORT, WS_PATH);
  ws.onEvent(onWebSocketEvent);
  ws.setReconnectInterval(3000);

  Serial.println("Ready. Tap button to talk.");
}

unsigned long lastDisplayUpdate = 0;
unsigned long lastStateChange = 0;
bool buttonWasPressed = false;

void loop() {
  ws.loop();

  bool buttonPressed = (digitalRead(BUTTON_PIN) == LOW);

  // Rising edge: button just pressed
  if (buttonPressed && !buttonWasPressed) {
    delay(30);  // debounce
    if (digitalRead(BUTTON_PIN) == LOW) {
      Serial.println("Button pressed -> sending to Pi");
      if (wsConnected) {
        ws.sendTXT("{\"event\":\"button_press\"}");
      } else {
        Serial.println("Not connected to Pi yet");
      }
    }
  }
  buttonWasPressed = buttonPressed;

  // Timeout: if stuck in non-idle state for >90s, reset to idle
  if (currentState != IDLE && (millis() - lastStateChange > 90000)) {
    Serial.println("State timeout — resetting to IDLE");
    lastText = "";
    setState(IDLE);
  }

  // Update display + LEDs at ~30fps
  if (millis() - lastDisplayUpdate > 33) {
    lastDisplayUpdate = millis();
    updateDisplay(currentState);
    updateLEDs(currentState);
  }
}
