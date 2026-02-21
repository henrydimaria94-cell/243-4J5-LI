# Guide : Synchronisation ESP32 ↔ Interface Python

## 🔄 Problème résolu

L'interface Python n'affichait pas les changements d'état des LEDs causés par les boutons physiques car elle ne s'abonnait pas aux topics d'état.

## ✅ Modifications apportées

### 1. Code Arduino (`lilygo_lte_mqtt_toggle.ino`)

#### Nouveaux topics MQTT
```cpp
char LED1_STATE_TOPIC[50];  // {device_id}/led/1/state
char LED2_STATE_TOPIC[50];  // {device_id}/led/2/state
```

#### Variables d'état avec debounce
```cpp
bool led1State = false;
bool led2State = false;
unsigned long lastButton1Press = 0;
unsigned long lastButton2Press = 0;
const unsigned long DEBOUNCE_DELAY = 200;  // 200ms
```

#### Fonction de toggle
```cpp
void checkButtonsForToggle() {
    unsigned long now = millis();
    
    // Bouton 1
    if (digitalRead(BUTTON1_PIN) == LOW) {
        if (now - lastButton1Press > DEBOUNCE_DELAY) {
            lastButton1Press = now;
            led1State = !led1State;
            digitalWrite(LED1_PIN, led1State ? HIGH : LOW);
            const char* state = led1State ? "ON" : "OFF";
            mqttClient.publish(LED1_STATE_TOPIC, state);
        }
    }
    
    // Bouton 2 (même logique)
}
```

### 2. Interface Python (`touch_ui_mqtt.py`)

#### Ajout des topics d'état
```python
self.led1_state_topic = f"{device_id}/led/1/state"
self.led2_state_topic = f"{device_id}/led/2/state"
```

#### Abonnement aux topics d'état
```python
def _on_mqtt_connect(self, client, userdata, flags, rc):
    # ... code existant ...
    client.subscribe(self.led1_state_topic)
    client.subscribe(self.led2_state_topic)
```

#### Synchronisation de l'état
```python
def _on_mqtt_message(self, client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8', errors='ignore')
    
    # Synchroniser LED1
    if topic == self.led1_state_topic:
        self.led1_state = (payload == "ON")
        self.status_message = f"LED ROUGE: {payload} (ESP32)"
    
    # Synchroniser LED2
    elif topic == self.led2_state_topic:
        self.led2_state = (payload == "ON")
        self.status_message = f"LED VERTE: {payload} (ESP32)"
```

## 📊 Architecture de communication

### Flux de données

```
┌─────────────────┐                    ┌──────────────────┐
│   ESP32 LilyGO  │                    │  Interface Python│
│                 │                    │                  │
│  Bouton 1 (34) ─┼──┐                 │                  │
│  Bouton 2 (35) ─┼──┤                 │                  │
│                 │  │                 │                  │
│  LED 1 (32)  ◄──┼──┤                 │                  │
│  LED 2 (33)  ◄──┼──┘                 │                  │
└────────┬────────┘                    └────────┬─────────┘
         │                                      │
         │  MQTT via WSS (Port 443)            │
         │  ════════════════════════            │
         │                                      │
         ├──► {id}/led/1/state ────────────────┤
         │         (ON/OFF)                     │
         │                                      │
         ├──► {id}/led/2/state ────────────────┤
         │         (ON/OFF)                     │
         │                                      │
         │◄──── {id}/led/1/set ─────────────────┤
         │         (ON/OFF)                     │
         │                                      │
         │◄──── {id}/led/2/set ─────────────────┤
                   (ON/OFF)
```

### Topics MQTT

| Topic | Publisher | Subscriber | Payload | Description |
|-------|-----------|------------|---------|-------------|
| `{id}/led/1/set` | Python | ESP32 | `ON` / `OFF` | Commande depuis interface |
| `{id}/led/2/set` | Python | ESP32 | `ON` / `OFF` | Commande depuis interface |
| `{id}/led/1/state` | ESP32 | Python | `ON` / `OFF` | État actuel LED1 |
| `{id}/led/2/state` | ESP32 | Python | `ON` / `OFF` | État actuel LED2 |
| `{id}/button/1/state` | ESP32 | Python | `PRESSED` / `RELEASED` | Événement bouton 1 |
| `{id}/button/2/state` | ESP32 | Python | `PRESSED` / `RELEASED` | Événement bouton 2 |

## 🧪 Test de fonctionnement

### Scénario 1 : Toggle depuis bouton physique
1. **Action** : Appuyer sur Bouton 1 (GPIO 34)
2. **ESP32** :
   - Toggle `led1State` (OFF → ON)
   - Allume LED1 physiquement
   - Publie `{id}/led/1/state = ON`
3. **Interface Python** :
   - Reçoit le message MQTT
   - Met à jour `self.led1_state = True`
   - Affiche "ON" en gros caractères
   - Status : "LED ROUGE: ON (ESP32)"

### Scénario 2 : Commande depuis interface
1. **Action** : Toucher "LED VERTE" dans l'interface
2. **Interface Python** :
   - Toggle `self.led2_state` (OFF → ON)
   - Publie `{id}/led/2/set = ON`
3. **ESP32** :
   - Reçoit la commande
   - Allume LED2 physiquement
   - Met à jour `led2State = true`
   - Confirme avec `{id}/led/2/state = ON`
4. **Interface Python** :
   - Reçoit la confirmation
   - État déjà à jour (pas de changement visuel)

### Scénario 3 : Synchronisation au démarrage
1. **ESP32** démarre avec LEDs éteintes
2. **ESP32** se connecte à MQTT et publie :
   - `{id}/led/1/state = OFF`
   - `{id}/led/2/state = OFF`
3. **Interface Python** reçoit les messages et synchronise l'affichage

## 🐛 Vérification du bon fonctionnement

### Dans le moniteur série de l'ESP32
```
[BTN1 TOGGLE] LED1 -> ON
[BTN1 TOGGLE] LED1 -> OFF
[BTN2 TOGGLE] LED2 -> ON
[LED1] Allumee (ROUGE) - commande distante
```

### Dans l'interface Python (zone MQTT DEBUG)
```
✓ Connecté au broker MQTT
✓ Abonné à esp32-XXXX/led/1/state
✓ Abonné à esp32-XXXX/led/2/state
← esp32-XXXX/led/1/state: ON
🔴 LED1 mise à jour: ON
→ esp32-XXXX/led/2/set: OFF
← esp32-XXXX/led/2/state: OFF
🟢 LED2 mise à jour: OFF
```

## 🔧 Configuration requise

### Fichier `auth.h` (ESP32)
```cpp
#define MQTT_BROKER "mqtt.edxo.ca"
#define MQTT_CLIENT_ID "esp32-XXXX"  // Votre ID unique
#define MQTT_USER "esp_user"
#define MQTT_PASS "votre_mot_de_passe"
#define APN "votre_apn"
// ...
```

### Fichier `mqtt_config.py` (Python)
```python
MQTT_CONFIG = {
    "broker": "mqtt.edxo.ca",
    "port": 443,
    "device_id": "esp32-XXXX",  # Doit correspondre à MQTT_CLIENT_ID
    "username": "esp_user",
    "password": "votre_mot_de_passe"
}
```

## ⚠️ Points d'attention

1. **Device ID identique** : Le `device_id` dans Python doit correspondre au `MQTT_CLIENT_ID` de l'ESP32
2. **Connexion WSS** : Port 443 avec WebSocket Secure
3. **Debounce** : 200ms pour éviter les rebonds des boutons
4. **Pull-up interne** : Les boutons utilisent `INPUT_PULLUP` (LOW = pressé)
5. **Synchronisation bidirectionnelle** : Les deux interfaces publient ET s'abonnent aux états

## 📝 Fichiers modifiés

- ✅ `lilygo_lte_mqtt_toggle.ino` (nouveau fichier)
- ✅ `touch_ui_mqtt.py` (modifications)
- ✅ Code original `lilygo_lte_mqtt.ino` (conservé intact)

## 🚀 Démarrage rapide

1. **Téléverser** `lilygo_lte_mqtt_toggle.ino` sur l'ESP32
2. **Vérifier** les connexions :
   - Bouton 1 → GPIO 34
   - Bouton 2 → GPIO 35
   - LED 1 → GPIO 32 (rouge)
   - LED 2 → GPIO 33 (verte)
3. **Lancer** l'interface Python :
   ```bash
   cd /home/henridumont/243-4J5-LI/labo/Labo-02/led-control
   python3 touch_ui_mqtt.py
   ```
4. **Tester** :
   - Appuyer sur les boutons physiques
   - Toucher l'écran pour contrôler les LEDs
   - Observer la synchronisation dans les deux sens

## 🎯 Résultat attendu

- ✅ Appui sur bouton physique → LED change + Interface se met à jour
- ✅ Touch sur interface → LED change + État confirmé par ESP32
- ✅ Messages MQTT visibles dans la zone DEBUG
- ✅ Pas de désynchronisation entre ESP32 et Python
