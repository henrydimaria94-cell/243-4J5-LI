#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Lancement du jeu Labyrinthe IoT sur l'écran tactile..."
echo "Pour revenir au bureau: Ctrl+Alt+F7 ou 'sudo chvt 7' depuis SSH"
echo ""

# Passer sur tty1
sudo chvt 1

# Lancer le programme sur tty1
# PYTHONPATH force l'utilisation du pygame système (SDL 2.30 avec KMSDRM)
# au lieu du pygame pip (SDL 2.28 sans KMSDRM)
sudo setsid sh -c "exec </dev/tty1 >/dev/tty1 2>&1 PYTHONPATH=/usr/lib/python3/dist-packages SDL_VIDEODRIVER=KMSDRM SDL_RENDER_DRIVER=software python3 ${SCRIPT_DIR}/main.py"
