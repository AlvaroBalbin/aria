/**
 * ARIA Pendant Firmware
 * ESP32 — I2S microphone + SSD1306 OLED + NeoPixel ring + WebSocket
 *
 * Libraries needed (install via Arduino Library Manager):
 *   - WebSockets by Markus Sattler
 *   - FastLED
 *   - Adafruit GFX Library
 *   - Adafruit SSD1306
 *   - ArduinoJson
 *
 * Pin assignments:
 *   I2S mic  : SCK=26, WS=25, SD=34
 *   OLED     : SDA=21, SCL=22
 *   NeoPixel : GPIO 5
 *   Button   : GPIO 0 (boot button — always available)
 */

#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include "audio_stream.h"
#include "display.h"
#include "leds.h"

// ── Configuration ────────────────────────────────────────────────────────────
// Pi 5 runs as WiFi hotspot. Default IP for NetworkManager hotspot is 10.42.0.1
const char* WIFI_SSID     = "ARIA-BASE";
const char* WIFI_PASSWORD = "aria1234";
const char* PI_HOST       = "10.42.0.1";
const int   PI_PORT       = 8000;
const char* WS_PATH       = "/ws/audio";

#define BUTTON_PIN 0   // Boot button. LOW when pressed.

// ── State machine ─────────────────────────────────────────────────────────────
enum State { IDLE = 0, LISTENING = 1, PROCESSING = 2, SPEAKING = 3 };
volatile State currentState = IDLE;
volatile bool  stopStreaming = false;

WebSocketsClient ws;

// ── WiFi + WebSocket setup ────────────────────────────────────────────────────
void connectWiFi() {
  Serial.print("Connecting to ");
  Serial.print(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 30) {
    delay(500);
    Serial.print(".");
    retries++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWiFi failed — check SSID/password");
  }
}

void onWebSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  if (type == WStype_CONNECTED) {
    Serial.println("WebSocket connected");
    setState(IDLE);
  } else if (type == WStype_DISCONNECTED) {
    Serial.println("WebSocket disconnected");
  } else if (type == WStype_TEXT) {
    // Server sends state updates: {"state":"processing"} etc.
    StaticJsonDocument<64> doc;
    if (!deserializeJson(doc, payload, length)) {
      const char* state = doc["state"];
      if (state) {
        if      (strcmp(state, "idle")       == 0) setState(IDLE);
        else if (strcmp(state, "processing") == 0) setState(PROCESSING);
        else if (strcmp(state, "speaking")   == 0) setState(SPEAKING);
      }
    }
  }
}

// ── State management ──────────────────────────────────────────────────────────
void setState(State s) {
  currentState = s;
  // Notify Pi for dashboard sync
  String msg = "{\"pendant_state\":\"" + stateStr(s) + "\"}";
  ws.sendTXT(msg);
}

String stateStr(State s) {
  switch (s) {
    case IDLE:       return "idle";
    case LISTENING:  return "listening";
    case PROCESSING: return "processing";
    case SPEAKING:   return "speaking";
  }
  return "idle";
}

// ── Main ──────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(200);

  pinMode(BUTTON_PIN, INPUT_PULLUP);

  initLEDs();
  initDisplay();
  initI2S();

  connectWiFi();

  ws.begin(PI_HOST, PI_PORT, WS_PATH);
  ws.onEvent(onWebSocketEvent);
  ws.setReconnectInterval(3000);

  Serial.println("ARIA ready.");
}

void loop() {
  ws.loop();

  // Button held → start listening
  if (digitalRead(BUTTON_PIN) == LOW && currentState == IDLE && ws.isConnected()) {
    delay(50); // debounce
    if (digitalRead(BUTTON_PIN) == LOW) {
      setState(LISTENING);
      stopStreaming = false;

      // Stream audio while button is held
      while (digitalRead(BUTTON_PIN) == LOW) {
        ws.loop();
        // Stream one chunk
        int32_t raw[BUFFER_SIZE];
        int16_t pcm[BUFFER_SIZE];
        size_t bytesRead;
        i2s_read(I2S_PORT, raw, sizeof(raw), &bytesRead, portMAX_DELAY);
        int samples = bytesRead / 4;
        for (int i = 0; i < samples; i++) {
          pcm[i] = (int16_t)(raw[i] >> 16);
        }
        ws.sendBIN((uint8_t*)pcm, samples * 2);
        updateDisplay(LISTENING);
        updateLEDs(LISTENING);
      }

      // Button released → signal end of speech to server
      ws.sendTXT("{\"event\":\"end_of_speech\"}");
      setState(PROCESSING);
    }
  }

  updateDisplay(currentState);
  updateLEDs(currentState);
}
