#pragma once
#include <driver/i2s.h>
#include <WebSocketsClient.h>

// INMP441 I2S pins
#define I2S_WS   25   // Word Select (LRCLK)
#define I2S_SCK  26   // Bit Clock (BCLK)
#define I2S_SD   34   // Serial Data in (DIN) — input-only pin, perfect for mic

#define I2S_PORT       I2S_NUM_0
#define SAMPLE_RATE    16000
#define BUFFER_SIZE    512   // samples per chunk

void initI2S() {
  i2s_config_t cfg = {
    .mode                 = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate          = SAMPLE_RATE,
    .bits_per_sample      = I2S_BITS_PER_SAMPLE_32BIT,  // INMP441 sends 32-bit frames
    .channel_format       = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags     = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count        = 4,
    .dma_buf_len          = BUFFER_SIZE,
    .use_apll             = false,
    .tx_desc_auto_clear   = false,
    .fixed_mclk           = 0,
  };

  i2s_pin_config_t pins = {
    .bck_io_num   = I2S_SCK,
    .ws_io_num    = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num  = I2S_SD,
  };

  i2s_driver_install(I2S_PORT, &cfg, 0, NULL);
  i2s_set_pin(I2S_PORT, &pins);
  i2s_zero_dma_buffer(I2S_PORT);
}

// Stream audio over WebSocket until stopFlag is set.
// Sends binary frames of 16-bit PCM at 16kHz.
void streamAudio(WebSocketsClient& ws, volatile bool& stopFlag) {
  int32_t raw[BUFFER_SIZE];
  int16_t pcm[BUFFER_SIZE];
  size_t bytesRead;

  while (!stopFlag) {
    i2s_read(I2S_PORT, raw, sizeof(raw), &bytesRead, portMAX_DELAY);
    int samples = bytesRead / 4;

    // Convert 32-bit I2S → 16-bit PCM (top 16 bits)
    for (int i = 0; i < samples; i++) {
      pcm[i] = (int16_t)(raw[i] >> 16);
    }

    ws.sendBIN((uint8_t*)pcm, samples * 2);
  }

  // Signal end of speech to server
  ws.sendTXT("{\"event\":\"end_of_speech\"}");
}

// Read a single buffer for level checking (used for VU meter on display)
int16_t getAudioLevel() {
  int32_t raw[64];
  size_t bytesRead;
  i2s_read(I2S_PORT, raw, sizeof(raw), &bytesRead, 10);
  int32_t sum = 0;
  for (int i = 0; i < 64; i++) sum += abs(raw[i] >> 16);
  return (int16_t)(sum / 64);
}
