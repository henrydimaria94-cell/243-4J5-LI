// ============================================================================
// LABYRINTHE IoT - ESP32 FIRMWARE (WiFi + MQTT over WebSocket)
// Par: Henri-Tadja
// Mode: WiFi (WPA2-Personal)
// ============================================================================

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <MPU6050.h>
#include <mbedtls/base64.h>
#include "auth.h"

// ─── Configuration des broches ────────────────────────────────────────────
#define BTN1_PIN     13
#define BTN2_PIN     14
#define BTN3_PIN     15
#define LED1_PIN     25
#define POT1_PIN     32
#define POT2_PIN     33
#define POT3_PIN     34

// ============================================================================
// CLASSE WEBSOCKET CLIENT POUR MQTT
// ============================================================================
class WebSocketClient : public Client {
private:
  WiFiClientSecure* _sslClient;
  bool _wsConnected;
  
  // Buffer pour les données reçues
  uint8_t _rxBuffer[512];
  size_t _rxBufferLen;
  size_t _rxBufferPos;

  // Génération de clé WebSocket aléatoire
  String generateWebSocketKey() {
    uint8_t key[16];
    for(int i = 0; i < 16; i++) {
      key[i] = random(0, 256);
    }
    size_t olen;
    unsigned char output[64];
    mbedtls_base64_encode(output, sizeof(output), &olen, key, 16);
    return String((char*)output);
  }

  // Lecture d'une frame WebSocket
bool readWebSocketFrame() {
    if (!_sslClient->available()) return false;
    
    // Lire les 2 premiers octets
    uint8_t byte1 = _sslClient->read();
    if (!_sslClient->available()) return false;
    uint8_t byte2 = _sslClient->read();
    
    uint8_t opcode = byte1 & 0x0F;
    bool masked = (byte2 & 0x80) != 0;
    uint64_t payloadLen = byte2 & 0x7F;
    
    // Gestion de la longueur étendue
    if (payloadLen == 126) {
      if (_sslClient->available() < 2) return false;
      payloadLen = (_sslClient->read() << 8) | _sslClient->read();
    } else if (payloadLen == 127) {
      if (_sslClient->available() < 8) return false;
      payloadLen = 0;
      for(int i = 0; i < 8; i++) {
        payloadLen = (payloadLen << 8) | _sslClient->read();
      }
    }
    
    // Lecture du masque si présent
    uint8_t mask[4] = {0};
    if (masked) {
      if (_sslClient->available() < 4) return false;
      for(int i = 0; i < 4; i++) {
        mask[i] = _sslClient->read();
      }
    }
    
    // Traitement selon le type de frame
    if (opcode == 0x01 || opcode == 0x02) { // Text ou Binary
      if (_sslClient->available() < payloadLen) return false;
      
      _rxBufferLen = payloadLen < sizeof(_rxBuffer) ? payloadLen : sizeof(_rxBuffer);
      for(size_t i = 0; i < _rxBufferLen; i++) {
        _rxBuffer[i] = _sslClient->read();
        if (masked) _rxBuffer[i] ^= mask[i % 4];
      }
      _rxBufferPos = 0;
      return true;
    }
    else if (opcode == 0x08) { // Close
      Serial.println("[WSS] Serveur a ferme la connexion");
      _wsConnected = false;
      return false;
    }
    else if (opcode == 0x09) { // Ping
      uint8_t pong[2] = {0x8A, 0x00};
      _sslClient->write(pong, 2);
      return false;
    }
    else if (opcode == 0x0A) { // Pong
      return false;
    }
    
    return false;
  }

public:
  WebSocketClient(WiFiClientSecure* sslClient) {
    _sslClient = sslClient;
    _wsConnected = false;
    _rxBufferLen = 0;
    _rxBufferPos = 0;
  }
 // Connexion IP (non utilisée)
  int connect(IPAddress ip, uint16_t port) { 
    return 0; 
  }

  // Connexion WebSocket via hostname
  int connect(const char *host, uint16_t port) {
    Serial.println("[WSS] Connexion SSL...");
    
    if (!_sslClient->connect(host, port)) {
      Serial.println("[WSS] Echec connexion SSL");
      return 0;
    }
    
    Serial.println("[WSS] SSL connecte, envoi handshake WebSocket...");
    
    // Envoi du handshake WebSocket
    String wsKey = generateWebSocketKey();
    _sslClient->print("GET / HTTP/1.1\r\n");
    _sslClient->print("Host: ");
    _sslClient->print(host);
    _sslClient->print("\r\n");
    _sslClient->print("Upgrade: websocket\r\n");
    _sslClient->print("Connection: Upgrade\r\n");
    _sslClient->print("Sec-WebSocket-Key: ");
    _sslClient->print(wsKey);
    _sslClient->print("\r\n");
    _sslClient->print("Sec-WebSocket-Protocol: mqtt\r\n");
    _sslClient->print("Sec-WebSocket-Version: 13\r\n\r\n");
    
    // Attendre la réponse
    unsigned long timeout = millis();
    while (!_sslClient->available() && millis() - timeout < 5000) {
      delay(10);
    }
    
    if (!_sslClient->available()) {
      Serial.println("[WSS] Timeout handshake");
      return 0;
    }
    
    // Lire la réponse HTTP
    String response = "";
    while (_sslClient->available()) {
      char c = _sslClient->read();
      response += c;
      if (response.endsWith("\r\n\r\n")) break;
    }
    
    // Vérifier si le handshake a réussi
    if (response.indexOf("101") > 0 && response.indexOf("Switching Protocols") > 0) {
      Serial.println("[WSS] Handshake WebSocket reussi!");
      _wsConnected = true;
      return 1;
    } else {
      Serial.println("[WSS] Handshake WebSocket echoue");
      Serial.println(response);
      return 0;
    }
  }

  // Écriture d'un octet
  size_t write(uint8_t b) {
    return write(&b, 1);
  }

  // Écriture d'un buffer
  size_t write(const uint8_t *buf, size_t size) {
    if (!_wsConnected) return 0;
    
    // Création de la frame WebSocket binaire avec masque
    uint8_t header[14];
    int headerLen = 2;
    
    header[0] = 0x82; // FIN + Binary frame
    
    // Déterminer la longueur du payload
    if (size < 126) {
      header[1] = 0x80 | size;
    } else if (size < 65536) {
      header[1] = 0x80 | 126;
      header[2] = (size >> 8) & 0xFF;
      header[3] = size & 0xFF;
      headerLen = 4;
    } else {
      header[1] = 0x80 | 127;
      for(int i = 0; i < 8; i++) header[2 + i] = 0;
      header[6] = (size >> 24) & 0xFF;
      header[7] = (size >> 16) & 0xFF;
      header[8] = (size >> 8) & 0xFF;
      header[9] = size & 0xFF;
      headerLen = 10;
    }
     // Générer un masque aléatoire
    uint8_t mask[4];
    for(int i = 0; i < 4; i++) {
      mask[i] = random(0, 256);
      header[headerLen + i] = mask[i];
    }
    headerLen += 4;
    
    // Envoyer le header
    _sslClient->write(header, headerLen);
    
    // Envoyer le payload masqué
    for(size_t i = 0; i < size; i++) {
      uint8_t maskedByte = buf[i] ^ mask[i % 4];
      _sslClient->write(&maskedByte, 1);
    }
    
    return size;
  }

  // Vérifier si des données sont disponibles
  int available() {
    // Vérifier le buffer d'abord
    if (_rxBufferPos < _rxBufferLen) {
      return _rxBufferLen - _rxBufferPos;
    }
    
    // Sinon essayer de lire une nouvelle frame
    if (_sslClient->available()) {
      if (readWebSocketFrame()) {
        return _rxBufferLen - _rxBufferPos;
      }
    }
    
    return 0;
  }

  // Lire un octet
  int read() {
    if (_rxBufferPos < _rxBufferLen) {
      return _rxBuffer[_rxBufferPos++];
    }
    
    if (_sslClient->available()) {
      if (readWebSocketFrame() && _rxBufferPos < _rxBufferLen) {
        return _rxBuffer[_rxBufferPos++];
      }
    }
    
    return -1;
  }

  // Lire dans un buffer
  int read(uint8_t *buf, size_t size) {
    size_t count = 0;
    while (count < size) {
      int c = read();
      if (c < 0) break;
      buf[count++] = (uint8_t)c;
    }
    return count;
  }

  // Lire sans consommer
  int peek() {
    if (_rxBufferPos < _rxBufferLen) {
      return _rxBuffer[_rxBufferPos];
    }
    return -1;
  }

  // Vider le buffer
  void flush() {
    _sslClient->flush();
  }

  // Fermer la connexion
  void stop() {
    if (_wsConnected) {
      // Envoyer une frame de fermeture
      uint8_t closeFrame[2] = {0x88, 0x00};
      _sslClient->write(closeFrame, 2);
    }
    _wsConnected = false;
    _sslClient->stop();
  }

  // Vérifier si connecté
  uint8_t connected() {
    return _wsConnected && _sslClient->connected();
  }

  // Opérateur booléen
  operator bool() {
    return _wsConnected;
  }
};

// ============================================================================
// OBJETS GLOBAUX
// ============================================================================
WiFiClientSecure sslClient;
WebSocketClient  wsClient(&sslClient);
PubSubClient     mqtt(wsClient);
MPU6050          mpu;

// ─── Variables d'état ─────────────────────────────────────────────────────
bool btn1Last = LOW, btn2Last = LOW, btn3Last = LOW;  // MODIFIÉ: LOW au lieu de HIGH
bool ledState = false;
bool ledBlink = false;
bool mpuAvailable = false;

unsigned long lastBlink    = 0;
unsigned long lastPublish  = 0;
unsigned long lastStatus   = 0;
unsigned long lastReconnect = 0;

String gameState = "idle";
// ============================================================================
// FONCTIONS DE CONNEXION
// ============================================================================

// Connexion au WiFi
bool connectToWiFi() {
  Serial.println("[WiFi] Initialisation...");
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  
  Serial.print("[WiFi] Connexion a ");
  Serial.print(WIFI_SSID);
  Serial.print("...");
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 20000) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(" ECHEC");
    Serial.println("[WiFi] Impossible de se connecter au reseau WiFi");
    Serial.println("[WiFi] Verifiez:");
    Serial.println("  - Le SSID est correct");
    Serial.println("  - Le mot de passe est correct");
    Serial.println("  - Le routeur est allume et accessible");
    return false;
  }
  
  Serial.println(" OK");
  Serial.print("[WiFi] IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("[WiFi] Signal (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
  
  return true;
}

// Callback MQTT
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  
  StaticJsonDocument<256> doc;
  deserializeJson(doc, msg);
  
  String t = String(topic);
  
  // Contrôle de la LED
  if (t == TOPIC_LED) {
    String state = doc["state"].as<String>();
    if (state == "on") { 
      ledState = true;  
      ledBlink = false; 
      digitalWrite(LED1_PIN, HIGH); 
    }
    if (state == "off") { 
      ledState = false; 
      ledBlink = false; 
      digitalWrite(LED1_PIN, LOW);  
    }
    if (state == "blink") { 
      ledBlink = true; 
    }
  }
  
  // Commandes de jeu
  if (t == TOPIC_COMMAND) {
    String cmd = doc["command"].as<String>();
    if (cmd == "start")   gameState = "running";
    if (cmd == "pause")   gameState = "paused";
    if (cmd == "reset")   gameState = "idle";
    if (cmd == "victory") gameState = "victory";
  }
}

// Connexion MQTT
void connectMQTT() {
  Serial.print("[MQTT] Connexion WebSocket a ");
  Serial.print(MQTT_BROKER);
  Serial.print(":");
  Serial.println(MQTT_WSS_PORT);
  
  // Connexion WebSocket SSL
  if (!wsClient.connect(MQTT_BROKER, MQTT_WSS_PORT)) {
    Serial.println("[MQTT] Echec connexion WebSocket - systeme continue localement");
    return;
  }
  
  // Connexion MQTT via WebSocket
  int tentatives = 0;
  while (!mqtt.connected() && tentatives < 5) {
    tentatives++;
    Serial.print("[MQTT] Tentative ");
    Serial.print(tentatives);
    Serial.print("/5... ");
    
    if (mqtt.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASS)) {
      Serial.println("OK !");
      mqtt.subscribe(TOPIC_LED);
      mqtt.subscribe(TOPIC_COMMAND);
    } else {
      int rc = mqtt.state();
      Serial.print("Echec rc=");
      Serial.println(rc);
      delay(2000);
    }
  }
  
  if (!mqtt.connected()) {
    Serial.println("[MQTT] ECHEC - systeme continue localement");
  }
}

// ============================================================================
// FONCTIONS DE LECTURE ET PUBLICATION
// ============================================================================

// Lecture des potentiomètres
int readDifficulty() { 
  return map(analogRead(POT1_PIN), 0, 4095, 1, 3); 
}

int readSpeed() { 
  return map(analogRead(POT2_PIN), 0, 4095, 1, 5); 
}

int readMazeSize() { 
  return map(analogRead(POT3_PIN), 0, 4095, 1, 3); 
}

// Publication des boutons
void publishButtons(bool b1, bool b2, bool b3) {
  if (!mqtt.connected()) return;
  
  StaticJsonDocument<128> doc;
  doc["btn1"] = b1; 
  doc["btn2"] = b2; 
  doc["btn3"] = b3;
  
  char buf[128]; 
  serializeJson(doc, buf);
  mqtt.publish(TOPIC_BUTTONS, buf);
}

// Publication des potentiomètres
void publishPots() {
  if (!mqtt.connected()) return;
  
  StaticJsonDocument<128> doc;
  doc["pot1"]       = analogRead(POT1_PIN);
  doc["difficulty"] = readDifficulty();
  doc["speed"]      = readSpeed();
  doc["maze_size"]  = readMazeSize();
  
  char buf[128]; 
  serializeJson(doc, buf);
  mqtt.publish(TOPIC_POTS, buf);
}

// Publication de l'accéléromètre
void publishAccel() {
  if (!mqtt.connected()) return;
  
  if (!mpuAvailable) {
    // Envoyer des valeurs par défaut si MPU6050 non disponible
    StaticJsonDocument<256> doc;
    doc["x"]     = 0.0;
    doc["y"]     = 0.0;
    doc["z"]     = 1.0;  // Simule gravité en Z
    doc["roll"]  = 0.0;
    doc["pitch"] = 0.0;
    
    char buf[256]; 
    serializeJson(doc, buf);
    mqtt.publish(TOPIC_ACCEL, buf);
    return;
  }
  
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  
  float roll  = atan2(ay, az) * 180.0 / PI;
  float pitch = atan2(-ax, sqrt((float)ay*ay + (float)az*az)) * 180.0 / PI;
  
  StaticJsonDocument<256> doc;
  doc["x"]     = ax / 16384.0;
  doc["y"]     = ay / 16384.0;
  doc["z"]     = az / 16384.0;
  doc["roll"]  = roll;
  doc["pitch"] = pitch;
  
  char buf[256]; 
  mqtt.publish(TOPIC_ACCEL, buf);
}

// Publication de l'état du jeu
void publishState() {
  if (!mqtt.connected()) return;
  
  StaticJsonDocument<64> doc;
  doc["state"] = gameState;
  
  char buf[64]; 
  serializeJson(doc, buf);
  mqtt.publish(TOPIC_STATE, buf);
}

// Publication du statut système
void publishStatus() {
  if (!mqtt.connected()) return;
  
  StaticJsonDocument<128> doc;
  doc["uptime"] = millis() / 1000;
  doc["rssi"]   = WiFi.RSSI();
  
  char buf[128]; 
  serializeJson(doc, buf);
  mqtt.publish(TOPIC_STATUS, buf);
}

// ============================================================================
// SETUP
// ============================================================================
void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("\n========================================");
  Serial.println("  Labyrinthe IoT - Henri-Tadja");
  Serial.println("  Mode: WiFi + MQTT over WebSocket");
  Serial.println("========================================\n");
  
  // Configuration des broches - MODIFIÉ: INPUT au lieu de INPUT_PULLUP
  pinMode(BTN1_PIN, INPUT);
  pinMode(BTN2_PIN, INPUT);
  pinMode(BTN3_PIN, INPUT);
  pinMode(LED1_PIN, OUTPUT);
  digitalWrite(LED1_PIN, LOW);
  
  // Initialisation MPU6050
  Wire.begin();
  mpu.initialize();
  
  if (mpu.testConnection()) {
    Serial.println("[MPU6050] Connexion etablie");
    
    // Configuration du MPU6050
    mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2); // ±2g
    mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_250); // ±250°/s
    mpu.setSleepEnabled(false); // CRITIQUE: Sortir du mode veille
    
    Serial.println("[MPU6050] Configuration appliquee (wake up + ranges)");
    mpuAvailable = true;
  } else {
    Serial.println("[MPU6050] AVERTISSEMENT - Pas de connexion I2C");
    Serial.println("[MPU6050] Le systeme continuera sans accelerometre");
    mpuAvailable = false;
  }
  
  // Connexion WiFi
  if (!connectToWiFi()) {
    Serial.println("\n[ERREUR CRITIQUE] Impossible de se connecter au WiFi");
    Serial.println("[ERREUR] Le systeme va redemarrer dans 5 secondes...");
    delay(5000);
    ESP.restart();
  }
  
  // Configuration SSL
  Serial.println("[SSL] Configuration du client SSL...");
  sslClient.setInsecure(); // Désactive la vérification du certificat
  
  // Configuration MQTT
  mqtt.setServer(MQTT_BROKER, MQTT_WSS_PORT);
  mqtt.setCallback(mqttCallback);
  mqtt.setBufferSize(512);
  mqtt.setKeepAlive(60);
  
  // Connexion MQTT
  connectMQTT();
  
  Serial.println("\n========================================");
  Serial.println("  Systeme pret !");
  Serial.println("========================================\n");
}

// ============================================================================
// LOOP PRINCIPAL
// ============================================================================
void loop() {
  // Reconnexion MQTT si nécessaire
  if (!mqtt.connected() && (millis() - lastReconnect > 10000)) {
    lastReconnect = millis();
    connectMQTT();
  }
  
  // Traitement MQTT
  mqtt.loop();
  
  // Lecture des boutons - MODIFIÉ: Lecture directe SANS inversion
  bool b1 = digitalRead(BTN1_PIN);
  bool b2 = digitalRead(BTN2_PIN);
  bool b3 = digitalRead(BTN3_PIN);
  
  // Détection des changements d'état des boutons
  if (b1 != btn1Last || b2 != btn2Last || b3 != btn3Last) {
    publishButtons(b1, b2, b3);
    
    // Bouton 1: Démarrer le jeu - MODIFIÉ: Détection de front montant (LOW→HIGH)
    if (b1 && !btn1Last) { 
      gameState = "running"; 
      publishState(); 
    }
    
    // Bouton 2: Pause/Reprendre
    if (b2 && !btn2Last) { 
      gameState = (gameState == "paused") ? "running" : "paused"; 
      publishState(); 
    }
    
    // Bouton 3: Reset
    if (b3 && !btn3Last) { 
      gameState = "idle"; 
      publishState(); 
      digitalWrite(LED1_PIN, LOW); 
      ledBlink = false; 
    }
    
    btn1Last = b1; 
    btn2Last = b2; 
    btn3Last = b3;
  }
  
  // Publication périodique des données (100ms)
  if (millis() - lastPublish > 100) {
    publishAccel();
    publishPots();
    lastPublish = millis();
  }
  
  // Publication du statut système (60s)
  if (millis() - lastStatus > 60000) {
    publishStatus();
    lastStatus = millis();
  }
  
  // Gestion du clignotement LED
  if (ledBlink && millis() - lastBlink > 300) {
    ledState = !ledState;
    digitalWrite(LED1_PIN, ledState ? HIGH : LOW);
    lastBlink = millis();
  }
  
  delay(10);
}
