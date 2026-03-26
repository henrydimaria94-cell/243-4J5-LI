#!/bin/bash
# Script pour lancer l'interface de contrôle MQTT sur l'écran tactile

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Lancement de l'interface MQTT sur l'écran tactile..."
echo "Pour revenir au bureau: Ctrl+Alt+F7 ou 'sudo chvt 7' depuis SSH"
echo ""

# Passer sur tty1
sudo chvt 1

# Lancer le programme sur tty1
sudo setsid sh -c "exec </dev/tty1 >/dev/tty1 2>&1 python3 ${SCRIPT_DIR}/touch_ui_mqtt.py"
