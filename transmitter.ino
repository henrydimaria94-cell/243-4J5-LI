#define T_BEAM_S3_SUPREME_SX1262

#include "LoRaBoards.h"
#include <RadioLib.h>
#include <ArduinoJson.h>

SX1262 radio = new Module(RADIO_CS_PIN, RADIO_DIO1_PIN, RADIO_RST_PIN, RADIO_BUSY_PIN);

#define POT_PIN   2
#define LED_PIN   43

#define LORA_FREQ      915.0
#define LORA_BW        125.0
#define LORA_SF        9
#define LORA_CR        7
#define LORA_SYNC      0x12
#define LORA_POWER     14
#define LORA_PREAMBLE  16

#define STABILITY_MS      400
#define COOLDOWN_MS       3000
#define HYSTERESIS        80
#define RESPONSE_TIMEOUT  30000

volatile bool rxFlag = false;
void IRAM_ATTR onRx() { rxFlag = true; }

enum TxState { STATE_IDLE, STATE_WAITING };
TxState txState = STATE_IDLE;

int  lastSentPot  = -1000;
int  prevPot      = -1;
int  activePot    = 0;
uint32_t stableStart  = 0;
uint32_t lastSendTime = 0;
uint32_t rxDeadline   = 0;

// ---- Helpers ---------------------------------------------------------

void ledFlash(int n) {
    for (int i = 0; i < n; i++) {
        digitalWrite(LED_PIN, HIGH); delay(80);
        digitalWrite(LED_PIN, LOW);  delay(80);
    }
}

void drawWrap(const String& txt, uint8_t y0, uint8_t lineH = 13) {
    if (!disp) return;
    uint8_t x = 0, y = y0;
    const uint8_t spW = disp->getUTF8Width(" ");
    String word;
    for (int i = 0; i <= (int)txt.length(); i++) {
        char c = (i < (int)txt.length()) ? txt[i] : ' ';
        if (c == ' ' || c == '\n') {
            if (word.length()) {
                uint16_t w = disp->getUTF8Width(word.c_str());
                if (x + w > 128) { x = 0; y += lineH; }
                if (y <= 64) disp->drawUTF8(x, y, word.c_str());
                x += w + spW;
                word = "";
            }
        } else {
            word += c;
        }
    }
}

void showIdle(int pot) {
    if (!disp) return;
    disp->clearBuffer();
    disp->setFont(u8g2_font_fur11_tf);
    disp->drawUTF8(0, 13, "Pot:");
    disp->drawUTF8(36, 13, String(pot).c_str());
    int bw = map(pot, 0, 4095, 0, 126);
    disp->drawFrame(1, 20, 126, 10);
    disp->drawBox(1, 20, bw, 10);
    disp->sendBuffer();
}

void showWaiting(int pot) {
    if (!disp) return;
    disp->clearBuffer();
    disp->setFont(u8g2_font_fur11_tf);
    disp->drawUTF8(0, 16, ("Envoi: " + String(pot)).c_str());
    disp->drawUTF8(0, 38, "Attente coach...");
    disp->sendBuffer();
}

void showAnswer(const String& resp, int pot) {
    if (!disp) return;
    disp->clearBuffer();
    disp->setFont(u8g2_font_fur11_tf);
    disp->drawUTF8(0, 13, "Coach:");
    drawWrap(resp, 30);
    disp->sendBuffer();
}

// ---- Setup -----------------------------------------------------------

void setup() {
    setupBoards();

    analogReadResolution(12);
    pinMode(POT_PIN, INPUT);
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    int err = radio.begin();
    if (err != RADIOLIB_ERR_NONE) {
        Serial.printf("[LoRa] init failed: %d\n", err);
        if (disp) {
            disp->clearBuffer();
            disp->setFont(u8g2_font_fur11_tf);
            disp->drawStr(0, 32, "LoRa ERREUR");
            disp->sendBuffer();
        }
        while (true) delay(500);
    }

    radio.setFrequency(LORA_FREQ);
    radio.setBandwidth(LORA_BW);
    radio.setSpreadingFactor(LORA_SF);
    radio.setCodingRate(LORA_CR);
    radio.setSyncWord(LORA_SYNC);
    radio.setOutputPower(LORA_POWER);
    radio.setPreambleLength(LORA_PREAMBLE);
    radio.setCRC(true);
    radio.setDio1Action(onRx);

    printResult(true);

    if (disp) {
        disp->clearBuffer();
        disp->setFont(u8g2_font_fur11_tf);
        disp->drawUTF8(14, 32, "Transmetteur");
        disp->sendBuffer();
        delay(1500);
    }

    stableStart = millis();
    prevPot = analogRead(POT_PIN);
}

// ---- Loop ------------------------------------------------------------

void loop() {
    int pot = analogRead(POT_PIN);

    if (abs(pot - prevPot) > 20) {
        prevPot = pot;
        stableStart = millis();
    }

    bool stable   = (millis() - stableStart) >= STABILITY_MS;
    bool diff     = abs(pot - lastSentPot) > HYSTERESIS;
    bool cooldown = (millis() - lastSendTime) >= COOLDOWN_MS;

    // ── IDLE ──────────────────────────────────────────────────────────
    if (txState == STATE_IDLE) {
        static uint32_t lastDraw = 0;
        if (millis() - lastDraw > 200) {
            showIdle(pot);
            lastDraw = millis();
        }

        if (stable && diff && cooldown) {
            StaticJsonDocument<64> doc;
            doc["pot"] = pot;
            String msg;
            serializeJson(doc, msg);

            Serial.printf("[TX] %s\n", msg.c_str());
            ledFlash(3);

            int e = radio.transmit(msg);
            if (e == RADIOLIB_ERR_NONE) {
                activePot = pot;
                lastSentPot = pot;
                lastSendTime = millis();
                rxDeadline = millis() + RESPONSE_TIMEOUT;
                rxFlag = false;
                radio.startReceive();
                txState = STATE_WAITING;
                showWaiting(pot);
            } else {
                Serial.printf("[TX] erreur: %d\n", e);
            }
        }

    // ── WAITING ───────────────────────────────────────────────────────
    } else {
        if (rxFlag) {
            rxFlag = false;
            String resp;
            int e = radio.readData(resp);
            if (e == RADIOLIB_ERR_NONE) {
                resp.trim();
                Serial.printf("[RX] %s\n", resp.c_str());
                showAnswer(resp, activePot);
                digitalWrite(LED_PIN, (activePot > 2048) ? HIGH : LOW);
            } else {
                Serial.printf("[RX] erreur: %d\n", e);
                radio.startReceive();
                return;
            }
            txState = STATE_IDLE;
        }

        if (millis() > rxDeadline) {
            Serial.println("[RX] timeout");
            radio.standby();
            digitalWrite(LED_PIN, LOW);
            txState = STATE_IDLE;
            if (disp) {
                disp->clearBuffer();
                disp->setFont(u8g2_font_fur11_tf);
                disp->drawUTF8(0, 32, "Timeout");
                disp->sendBuffer();
                delay(1000);
            }
        }
    }
}
