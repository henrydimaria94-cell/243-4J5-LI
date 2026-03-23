# Projet Mi-Session — Jeu de Labyrinthe IoT
**Cours :** 243-4J5-LI
**Étudiant :** Henri-Tadja

---

## Description
Un labyrinthe généré procéduralement s'affiche sur l'écran tactile du Raspberry Pi 5.
Le joueur incline le shield LilyGO A7670G pour déplacer une balle dorée jusqu'à la sortie via le MPU6050 (roll/pitch).

---

## Architecture
```
Shield LilyGO A7670G                   Raspberry Pi 5 (écran tactile)
─────────────────────                  ─────────────────────────────
Incliner le shield    ──── LTE/MQTT ──→  Balle se déplace dans le labyrinthe
BTN1 : Démarrer/Reprendre              Labyrinthe + capteurs temps réel
BTN2 : Pause/Reprendre                 Boutons tactiles : Start/Pause/Reset
BTN3 : Reset                           Chronomètre + meilleur temps
POT1 : Difficulté (1–3)
POT2 : Vitesse balle (1–5)
POT3 : Taille labyrinthe (S/M/L)
LED1 : Allumée pendant la partie, clignote à la victoire
```

---

## Broches GPIO

| Composant   | Broche  | Rôle                         |
|-------------|---------|------------------------------|
| BTN1        | GPIO 13 | Démarrer / Reprendre         |
| BTN2        | GPIO 14 | Pause / Reprendre            |
| BTN3        | GPIO 27 | Reset                        |
| LED rouge   | GPIO 25 | Feedback (partie / victoire) |
| POT1        | GPIO 32 | Difficulté (1–3)             |
| POT2        | GPIO 33 | Vitesse (1–5)                |
| POT3        | GPIO 34 | Taille du labyrinthe (S/M/L) |
| MPU6050 SDA | GPIO 21 | I2C données                  |
| MPU6050 SCL | GPIO 22 | I2C horloge                  |

---

## Structure du projet
```
projet-mi-session/
├── firmware/
│   ├── firmware.ino          # Code principal LilyGO A7670G
│   ├── auth.h.example        # Template credentials MQTT
│   ├── auth.h                # Credentials réels (ne pas committer !)
│   ├── trust_anchors.h       # Certificats TLS
│   └── tests/
│       └── checklist.md      # Checklist validation firmware
├── interface/
│   ├── main.py               # Interface pygame + MQTT (Raspberry Pi)
│   ├── requirements.txt      # Dépendances Python
│   ├── iot-interface.service # Service systemd
│   └── tests/
│       └── checklist.md      # Checklist validation interface
└── README.md
```

---

## Topics MQTT

| Direction     | Topic                                        |
|---------------|----------------------------------------------|
| LilyGO → Pi  | `etudiant/henri-tadja/sensors/buttons`       |
| LilyGO → Pi  | `etudiant/henri-tadja/sensors/pots`          |
| LilyGO → Pi  | `etudiant/henri-tadja/sensors/accel`         |
| LilyGO → Pi  | `etudiant/henri-tadja/game/state`            |
| LilyGO → Pi  | `etudiant/henri-tadja/status`                |
| Pi → LilyGO  | `etudiant/henri-tadja/actuators/led1`        |
| Pi → LilyGO  | `etudiant/henri-tadja/game/command`          |

---

## Installation firmware (LilyGO)
```bash
cd ~/243-4J5-LI/projet-mi-session/firmware
cp auth.h.example auth.h
nano auth.h
arduino-cli compile --fqbn esp32:esp32:esp32 firmware.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 firmware.ino
arduino-cli monitor -p /dev/ttyUSB0 -c baudrate=115200
```

---

## Installation interface (Raspberry Pi)
```bash
cd ~/243-4J5-LI/projet-mi-session/interface
pip3 install -r requirements.txt --break-system-packages
python3 main.py
```

---

## Démarrage automatique (systemd)
```bash
sudo cp iot-interface.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable iot-interface.service
sudo systemctl start iot-interface.service
sudo systemctl status iot-interface.service
```

---

## Git — Remise finale
```bash
cd ~/243-4J5-LI/projet-mi-session
git add .
git commit -m "Projet mi-session : système IoT complet"
git push origin henri-tadja/projet-mi-session
```

> ⚠️ Ne jamais committer `auth.h` — vérifier que `.gitignore` contient `auth.h`
