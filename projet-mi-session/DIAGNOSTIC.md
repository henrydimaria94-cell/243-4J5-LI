# Guide de diagnostic - Labyrinthe IoT

## Problème: L'interface Pygame ne répond pas aux boutons/potentiomètres

### Étapes de diagnostic

#### 1. Vérifier l'ESP32

**a) Téléverser le firmware**
```bash
# Dans Arduino IDE:
# 1. Ouvrir firmware/firmware.ino
# 2. Sélectionner la carte ESP32 Dev Module
# 3. Sélectionner le port série (ex: /dev/ttyUSB0)
# 4. Téléverser
```

**b) Monitorer le port série de l'ESP32**
```bash
# Dans Arduino IDE: Outils > Moniteur série (115200 baud)
# Ou en ligne de commande:
screen /dev/ttyUSB0 115200
# (Ctrl+A puis K pour quitter)
```

**Ce que vous devez voir:**
```
=== Labyrinthe IoT - Henri-Tadja (WiFi) ===

[MPU6050] OK - Connexion etablie
[WiFi] Connexion a BELL183... OK
[WiFi] IP: 192.168.x.x
[WSS] Connexion SSL...
[WSS] SSL connecte, envoi handshake WebSocket...
[WSS] Handshake WebSocket reussi!
[MQTT] Tentative 1/5... OK !

=== Systeme pret ===
```

**Si problème WiFi:**
- Vérifier le SSID et mot de passe dans `firmware/auth.h`
- Vérifier que le routeur est allumé
- Vérifier le signal WiFi (RSSI > -70 dBm)

**Si problème MQTT:**
- Vérifier que le broker est accessible: `ping mqtt.henri-dumont.com`
- Vérifier les identifiants MQTT dans `firmware/auth.h`

#### 2. Tester la connexion MQTT

**Lancer le script de test:**
```bash
cd /home/henridumont/243-4J5-LI/projet-mi-session/interface
python3 test_mqtt.py
```

**Actions à faire:**
1. Appuyer sur BTN1, BTN2, BTN3 sur l'ESP32
2. Tourner les potentiomètres POT1, POT2, POT3
3. Bouger l'ESP32 (si MPU6050 connecté)

**Ce que vous devez voir:**
```
✓ Connecté au broker MQTT (rc=0)
En attente des messages de l'ESP32...

[14:23:45] 🔘 BUTTONS: BTN1
[14:23:46] 📐 ACCEL: Roll=12.3° Pitch=-8.5°
[14:23:47] 🎛️  POTS: Diff=2 Speed=4 Size=1
```

**Si aucun message:**
- L'ESP32 n'est pas connecté au broker MQTT
- Vérifier le moniteur série de l'ESP32
- Vérifier que les topics sont identiques (ESP32 et Python)

#### 3. Lancer l'interface Pygame

```bash
cd /home/henridumont/243-4J5-LI/projet-mi-session/interface
python3 main.py
```

**Ce que vous devez voir au démarrage:**
```
✓ MQTT connecté avec succès (rc=0)
  Broker: mqtt.henri-dumont.com:443
  Souscription aux topics:
    - etudiant/henri-tadja/sensors/buttons
    - etudiant/henri-tadja/sensors/pots
    - etudiant/henri-tadja/sensors/accel
    - etudiant/henri-tadja/game/state
  ✓ Prêt à recevoir les messages de l'ESP32
[PYGAME] Fenêtre créée, début de la boucle de jeu...
```

**Quand vous appuyez sur BTN1:**
```
[BUTTONS] Reçu: {'btn1': True, 'btn2': False, 'btn3': False}
[BTN1] Démarrage du jeu
```

**Quand vous bougez l'ESP32:**
```
[ACCEL] Roll=15.3° Pitch=-10.2°
```

#### 4. Contrôles du jeu

**Via ESP32 (mode normal):**
- **BTN1**: Démarrer le jeu
- **BTN2**: Pause/Resume
- **BTN3**: Reset
- **POT1**: Difficulté (1-3)
- **POT2**: Vitesse de la balle (1-5)
- **POT3**: Taille du labyrinthe (1-3)
- **MPU6050**: Incliner l'ESP32 pour bouger la balle

**Via Clavier (mode test, si ajouté):**
- **ESPACE/S**: Démarrer
- **P**: Pause
- **R**: Reset
- **Flèches**: Bouger la balle
- **ESC/Q**: Quitter

#### 5. Problèmes courants

| Symptôme | Cause probable | Solution |
|----------|---------------|----------|
| Interface affichée mais rien ne bouge | ESP32 non connecté à MQTT | Vérifier moniteur série ESP32 |
| `rc=4` dans les logs MQTT | Mauvais identifiants | Vérifier `MQTT_USER` et `MQTT_PASSWORD` |
| Balle ne bouge pas | État du jeu = `idle` | Appuyer sur BTN1 pour démarrer |
| Messages MQTT non reçus | Topics différents ESP32/Pygame | Vérifier `PRENOM_NOM` identique |
| MPU6050 non détecté | I2C mal connecté | Vérifier câblage SDA/SCL, le système continue sans |

#### 6. Schéma de connexion ESP32

```
ESP32 DevKit v1
┌─────────────────┐
│  GPIO 13  BTN1  ├─→ Bouton → GND
│  GPIO 14  BTN2  ├─→ Bouton → GND
│  GPIO 15  BTN3  ├─→ Bouton → GND
│  GPIO 25  LED1  ├─→ LED + Résistance → GND
│  GPIO 32  POT1  ├─→ Potentiomètre (Difficulté)
│  GPIO 33  POT2  ├─→ Potentiomètre (Vitesse)
│  GPIO 34  POT3  ├─→ Potentiomètre (Taille)
│  GPIO 21  SDA   ├─→ MPU6050 SDA
│  GPIO 22  SCL   ├─→ MPU6050 SCL
│  3.3V          ├─→ MPU6050 VCC
│  GND           ├─→ MPU6050 GND
└─────────────────┘
```

**Note:** Les boutons utilisent les résistances pull-up internes (INPUT_PULLUP).

## Commandes utiles

```bash
# Surveiller les messages MQTT en direct
python3 interface/test_mqtt.py

# Lancer l'interface
python3 interface/main.py

# Moniteur série ESP32 (Linux)
screen /dev/ttyUSB0 115200

# Tester la connectivité au broker
ping mqtt.henri-dumont.com
curl -I https://mqtt.henri-dumont.com
```

## Support

Si le problème persiste après avoir suivi ces étapes:
1. Capturer les logs du moniteur série ESP32
2. Capturer les logs de `test_mqtt.py`
3. Capturer les logs de `main.py`
4. Vérifier que tous les topics MQTT correspondent exactement
