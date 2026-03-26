#!/bin/bash
# Script xinit — applique la rotation puis lance l'interface
xrandr --output DSI-2 --rotate left 2>/dev/null || true
sleep 1
timeout 3 xinput set-prop "11-005d Goodix Capacitive TouchScreen" --type=float "Coordinate Transformation Matrix" 0 -1 1 1 0 0 0 0 1 2>/dev/null || true
export SDL_RENDER_DRIVER=software
exec /usr/bin/python3 /home/henridumont/243-4J5-LI/projet-mi-session/interface/main.py
