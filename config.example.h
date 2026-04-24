// config.example.h — Copiez ce fichier en config.h et remplissez vos valeurs
#ifndef CONFIG_H
#define CONFIG_H

// ============================================================================
// CONFIGURATION WiFi
// Décommentez UNE seule option selon votre réseau
// ============================================================================

#define WIFI_SECURITY_WPA2_PERSONAL   // Réseau personnel (maison)
// #define WIFI_SECURITY_WPA2_ENTERPRISE // Réseau scolaire (EAP-PEAP)

const char* WIFI_SSID     = "VOTRE_SSID";
const char* WIFI_PASSWORD = "VOTRE_MOT_DE_PASSE";

// Réseau d'entreprise / scolaire — remplir seulement si WIFI_SECURITY_WPA2_ENTERPRISE
const char* EAP_IDENTITY = "VOTRE_IDENTIFIANT";   // ex. numéro étudiant
const char* EAP_USERNAME = "VOTRE_IDENTIFIANT";
const char* EAP_PASSWORD = "VOTRE_MOT_DE_PASSE_EAP";

// ============================================================================
// CONFIGURATION LLM (Groq API)
// Obtenez une clé gratuite sur https://console.groq.com
// ============================================================================
const char* OPENWEBUI_URL = "https://api.groq.com/openai/v1/chat/completions";
const char* API_KEY       = "VOTRE_CLE_API_GROQ";   // commence par gsk_
const char* MODEL_NAME    = "llama-3.3-70b-versatile";

const char* SYSTEM_PROMPT =
  "Tu es un entraineur sportif. "
  "Valeur potentiometre 0-4095. "
  "0-1000=effort faible, 1001-3000=bon rythme, 3001-4095=excellent. "
  "REGLE ABSOLUE: repondre en UNE SEULE PHRASE de 40 caracteres MAX. "
  "Pas d'emojis. Pas de ponctuation double.";

// ============================================================================
// CONFIGURATION MQTT (WebSocket TLS port 443)
// ============================================================================
const char* MQTT_BROKER    = "votre-broker.exemple.com";
const int   MQTT_PORT      = 443;
const char* MQTT_USER      = "VOTRE_UTILISATEUR_MQTT";
const char* MQTT_PASS      = "VOTRE_MOT_DE_PASSE_MQTT";
const char* MQTT_CLIENT_ID = "esp32-receiver";

// Topics publiés — remplacez "prenom-nom" par votre identifiant
const char* MQTT_TOPIC_POT     = "prenom-nom/pot";
const char* MQTT_TOPIC_REPONSE = "prenom-nom/reponse";
const char* MQTT_TOPIC_RSSI    = "prenom-nom/rssi";
const char* MQTT_TOPIC_SNR     = "prenom-nom/snr";

#endif // CONFIG_H
