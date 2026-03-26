// auth.h - Configuration WiFi et MQTT
#ifndef AUTH_H
#define AUTH_H

// ============================================================================
// CONFIGURATION WiFi - WPA2-Personal
// ============================================================================

const char* WIFI_SSID = "Henri";              // Nom du réseau WiFi
const char* WIFI_PASSWORD = "Alia0794";     // Mot de passe WiFi

// ============================================================================
// CONFIGURATION MQTT
// ============================================================================

// Configuration MQTT via WebSocket SSL (port 443)
const char MQTT_BROKER[] = "mqtt.henri-dumont.com";
const int  MQTT_PORT = 1883;        // Port MQTT standard (non-SSL, non utilisé)
const int  MQTT_WSS_PORT = 443;     // Port WebSocket SSL (utilisé via Cloudflare)
const char MQTT_USER[] = "esp_user";
const char MQTT_PASS[] = "Dumont@1994";

// Serveur de test (si besoin):
// const char MQTT_BROKER[] = "test.mosquitto.org";
// const int  MQTT_PORT = 8883;  // Port MQTT SSL de test
// const char MQTT_USER[] = "";
// const char MQTT_PASS[] = "";

// Device ID - Identifiant unique de l'appareil
// Format suggéré: "esp32-XXXXXX" (6 derniers caractères de l'IMEI ou personnalisé)
// Cet identifiant sera utilisé comme préfixe pour tous les topics MQTT
const char MQTT_CLIENT_ID[] = "esp32-henridumont";     // ⚠️ À personnaliser selon votre appareil
const char TOPIC_BUTTONS[] = "etudiant/henri-tadja/sensors/buttons";
const char TOPIC_POTS[]    = "etudiant/henri-tadja/sensors/pots";
const char TOPIC_ACCEL[]   = "etudiant/henri-tadja/sensors/accel";
const char TOPIC_STATE[]   = "etudiant/henri-tadja/game/state";
const char TOPIC_STATUS[]  = "etudiant/henri-tadja/status";
const char TOPIC_LED[]     = "etudiant/henri-tadja/actuators/led1";
const char TOPIC_COMMAND[] = "etudiant/henri-tadja/game/command";

#endif // AUTH_H
