#!/bin/bash
sleep 5
export DISPLAY=:0
xhost +SI:localuser:henridumont 2>/dev/null || true
cd /home/henridumont/243-4J5-LI/projet-mi-session/interface
/usr/bin/python3 main.py
