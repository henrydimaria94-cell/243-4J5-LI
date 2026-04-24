# Labo 04 — Communication LoRa avec LilyGo T-Beam Supreme

Communication bidirectionnelle LoRa entre deux modules LilyGo T-Beam Supreme S3.  
Le transmetteur envoie la valeur d'un potentiomètre ; le récepteur interroge un LLM via l'API Groq, renvoie la réponse par LoRa et publie les métriques sur un broker MQTT.

## Architecture du système

```
[Transmetteur]                              [Récepteur]
  Potentiomètre                               SX1262 (LoRa)
       │                                           │
  SX1262 (LoRa) ──── 915 MHz / SF9 ──────►  WiFi → API Groq (LLM)
       │                                           │
  OLED SH1106   ◄──── réponse texte ────────  MQTT WebSocket TLS
  LED GPIO 43                                 LED GPIO 43
```

## Matériel requis

| Composant | Quantité |
|-----------|----------|
| LilyGo T-Beam Supreme S3 (SX1262) | 2 |
| Potentiomètre (branché sur GPIO 2) | 1 |

## Structure du projet

```
Labo-04-TP/
├── transmitter/
│   ├── transmitter.ino       # Sketch émetteur LoRa
│   ├── LoRaBoards.h/.cpp     # Abstraction matérielle LilyGo
│   └── utilities.h           # Définitions des broches
│
├── receiver/
│   ├── receiver.ino          # Sketch récepteur LoRa + LLM + MQTT
│   ├── config.example.h      # ← Modèle de configuration
│   ├── config.h              # ← À créer (ignoré par Git)
│   ├── LoRaBoards.h/.cpp
│   └── utilities.h
│
└── llm-t-beam-supreme/       # Sketch autonome test LLM sans LoRa
```

## Installation

### 1. Cloner le dépôt

```bash
git clone <url-du-repo>
```

### 2. Créer le fichier de configuration

```bash
cp receiver/config.example.h receiver/config.h
```

Ouvrez `receiver/config.h` et remplissez vos valeurs :

```cpp
// WiFi personnel
#define WIFI_SECURITY_WPA2_PERSONAL
const char* WIFI_SSID     = "MonReseau";
const char* WIFI_PASSWORD = "MonMotDePasse";

// API Groq — https://console.groq.com
const char* API_KEY = "gsk_...";

// MQTT
const char* MQTT_BROKER = "votre-broker.exemple.com";
const char* MQTT_USER   = "utilisateur";
const char* MQTT_PASS   = "motdepasse";

// Topics — adaptez le préfixe
const char* MQTT_TOPIC_POT     = "prenom-nom/pot";
const char* MQTT_TOPIC_REPONSE = "prenom-nom/reponse";
const char* MQTT_TOPIC_RSSI    = "prenom-nom/rssi";
const char* MQTT_TOPIC_SNR     = "prenom-nom/snr";
```

> `config.h` est listé dans `.gitignore` — il ne sera jamais commité.

### 3. Librairies Arduino requises

Installez via le gestionnaire de librairies Arduino IDE :

| Librairie | Auteur |
|-----------|--------|
| ArduinoJson | Benoit Blanchon |
| U8g2 | olikraus |
| XPowersLib | Lewis He |
| RadioLib | jgromes |
| PubSubClient | Nick O'Leary |

### 4. Sélectionner la carte

**Tools → Board → ESP32S3 Dev Module**

| Paramètre | Valeur |
|-----------|--------|
| USB CDC On Boot | Enabled |
| Flash Size | 16MB |
| PSRAM | OPI PSRAM |

### 5. Téléverser

1. Téléverser `transmitter/transmitter.ino` sur le premier T-Beam.
2. Téléverser `receiver/receiver.ino` sur le second T-Beam.

## Paramètres LoRa

| Paramètre | Valeur |
|-----------|--------|
| Fréquence | 915.0 MHz |
| Bande passante | 125 kHz |
| Spreading Factor | 9 |
| Coding Rate | 7 |
| Sync Word | 0x12 |
| Puissance TX | 14 dBm |
| Préambule | 16 |
| CRC | Activé |

## Format des messages LoRa

**Transmetteur → Récepteur**
```json
{ "pot": 2048 }
```

**Récepteur → Transmetteur**
```
Texte brut — réponse du LLM (max 40 caractères)
```

## Topics MQTT publiés par le récepteur

| Topic | Contenu |
|-------|---------|
| `{prefix}/pot` | Valeur du potentiomètre (0–4095) |
| `{prefix}/reponse` | Réponse du LLM |
| `{prefix}/rssi` | RSSI LoRa (dBm) |
| `{prefix}/snr` | SNR LoRa (dB) |

## Comportement du transmetteur

- Lecture continue du potentiomètre (GPIO 2, ADC 12 bits, 0–4095)
- Envoi si valeur stable ≥ 400 ms **et** variation > 80 unités depuis le dernier envoi
- Délai minimal de 3 secondes entre deux transmissions
- Attente de la réponse du récepteur (timeout 30 s)
- LED GPIO 43 : 3 flashs rapides à l'envoi, puis fixe selon l'effort (HIGH si pot > 2048)

## Comportement du récepteur

- Réception LoRa par interruption (DIO1)
- Appel API Groq dès réception d'un paquet valide
- Retransmission de la réponse texte au transmetteur
- Publication MQTT sur 4 topics
- Affichage OLED avec retour écran veille après 10 secondes
- LED GPIO 43 : allumée pendant le traitement LLM
