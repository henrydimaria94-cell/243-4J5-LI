#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface IoT - Projet mi-session
Labyrinthe IoT — Henri Tadja
Mode Dashboard + Mode Jeu
"""

import os
import sys
import json
import random
import time
import math
import threading
from queue import Queue, Empty
import pygame
import paho.mqtt.client as mqtt
try:
    from evdev import InputDevice, ecodes, list_devices
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False
    print("[Touch] evdev non disponible — mode souris uniquement")


# ─── Configuration SDL pour Raspberry Pi ─────────────────────
def init_display() -> bool:
    # Si SDL_VIDEODRIVER est déjà défini (ex: par le service systemd), l'utiliser directement
    if 'SDL_VIDEODRIVER' in os.environ:
        driver = os.environ['SDL_VIDEODRIVER']
        print(f"[SDL] Driver imposé: {driver}")
        try:
            pygame.display.init()
            print(f"[SDL] Driver {pygame.display.get_driver()} initialisé")
            return True
        except Exception as e:
            print(f"[SDL] Échec {driver}: {e}")
            return False

    if 'DISPLAY' in os.environ:
        os.environ['SDL_VIDEODRIVER'] = 'x11'
        print(f"[SDL] Mode X11 (DISPLAY={os.environ.get('DISPLAY')})")
        try:
            pygame.display.init()
            print(f"[SDL] Driver {pygame.display.get_driver()} initialisé")
            return True
        except Exception as e:
            print(f"[SDL] Échec X11: {e}")

    print("[SDL] Mode console, essai des drivers framebuffer...")
    for driver_name, env_vars in [
        ('kmsdrm', {'SDL_VIDEODRIVER': 'kmsdrm'}),
        ('fbcon',  {'SDL_VIDEODRIVER': 'fbcon', 'SDL_FBDEV': '/dev/fb0'}),
    ]:
        for key in ['SDL_VIDEODRIVER', 'SDL_FBDEV', 'SDL_NOMOUSE']:
            os.environ.pop(key, None)
        os.environ.update(env_vars)
        try:
            pygame.display.init()
            print(f"[SDL] Driver {driver_name} initialisé")
            return True
        except Exception as e:
            print(f"[SDL] Échec {driver_name}: {e}")

    print("[SDL] Aucun driver disponible!")
    return False


# ─── Configuration MQTT ───────────────────────────────────────
MQTT_BROKER   = "mqtt.henri-dumont.com"
MQTT_PORT     = 443
MQTT_USER     = "esp_user"
MQTT_PASSWORD = "Dumont@1994"
PRENOM_NOM    = "henri-tadja"

TOPIC_BUTTONS = f"etudiant/{PRENOM_NOM}/sensors/buttons"
TOPIC_POTS    = f"etudiant/{PRENOM_NOM}/sensors/pots"
TOPIC_ACCEL   = f"etudiant/{PRENOM_NOM}/sensors/accel"
TOPIC_STATE   = f"etudiant/{PRENOM_NOM}/game/state"
TOPIC_LED     = f"etudiant/{PRENOM_NOM}/actuators/led1"
TOPIC_COMMAND = f"etudiant/{PRENOM_NOM}/game/command"
TOPIC_STATUS  = f"etudiant/{PRENOM_NOM}/status"

# ─── Palette de couleurs ──────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
GOLD       = (255, 215, 0)
GREEN      = (0,   200, 0)
RED        = (200, 0,   0)
BLUE       = (0,   100, 255)
GRAY       = (180, 180, 180)
DARK_GRAY  = (80,  80,  80)
ORANGE     = (255, 140, 0)
LIGHT_GRAY = (220, 220, 220)

# ─── Résolution cible (écran tactile RPi — 800x480) ──────────
WIDTH, HEIGHT = 800, 480
SCREEN_W, SCREEN_H = HEIGHT, WIDTH   # Portrait : 480 × 800
FPS           = 30

# ─── Tailles du labyrinthe ────────────────────────────────────
MAZE_SIZES = {1: (21, 13), 2: (27, 17), 3: (33, 21)}


# ═══════════════════════════════════════════════════════════════
# TOUCH — Lecture directe evdev (basé sur Labo-02 led-control)
# ═══════════════════════════════════════════════════════════════
class TouchReader(threading.Thread):
    """Lit les événements tactiles directement via evdev (comme le Labo-02)."""

    def __init__(self, event_queue: Queue):
        super().__init__(daemon=True)
        self.event_queue = event_queue
        self.device = self._find_touch_device()
        if not self.device:
            raise RuntimeError("Aucun périphérique touchscreen trouvé.")

        abs_x = self.device.absinfo(ecodes.ABS_MT_POSITION_X)
        abs_y = self.device.absinfo(ecodes.ABS_MT_POSITION_Y)
        self.min_x, self.max_x = abs_x.min, abs_x.max
        self.min_y, self.max_y = abs_y.min, abs_y.max
        self.current_x = (self.min_x + self.max_x) // 2
        self.current_y = (self.min_y + self.max_y) // 2
        print(f"[Touch] Plage X: {self.min_x}-{self.max_x}  Y: {self.min_y}-{self.max_y}")

    def _find_touch_device(self):
        for path in list_devices():
            dev = InputDevice(path)
            name = dev.name.lower()
            if "touch" in name or "ft5406" in name or "goodix" in name:
                print(f"[Touch] Périphérique: {dev.name} ({path})")
                return dev
        return None

    def run(self):
        for event in self.device.read_loop():
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_MT_POSITION_X:
                    self.current_x = event.value
                elif event.code == ecodes.ABS_MT_POSITION_Y:
                    self.current_y = event.value
            elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                if event.value == 1:
                    self.event_queue.put(("tap", self.current_x, self.current_y))


# ═══════════════════════════════════════════════════════════════
# MODELE — Données des capteurs
# ═══════════════════════════════════════════════════════════════
class SensorData:
    """Stocke l'état de tous les capteurs et de la connexion."""

    def __init__(self):
        self.buttons        = {"btn1": False, "btn2": False, "btn3": False}
        self.pots           = {"pot1": 0, "difficulty": 1, "speed": 3, "maze_size": 1}
        self.accel          = {"x": 0.0, "y": 0.0, "z": 1.0, "roll": 0.0, "pitch": 0.0}
        self.status         = {"uptime": 0, "rssi": -50}
        self.mqtt_connected = False
        self.last_update    = time.time()


# ═══════════════════════════════════════════════════════════════
# MODELE/LOGIQUE — Labyrinthe
# ═══════════════════════════════════════════════════════════════
class MazeGame:
    """Logique du jeu labyrinthe (état, physique de la balle, génération)."""

    GAME_AREA_H = HEIGHT - 90

    def __init__(self):
        self.state      = "idle"
        self.roll       = 0.0
        self.pitch      = 0.0
        self.difficulty = 1
        self.speed      = 3
        self.maze_size  = 1
        self.best_time  = None
        self.start_time = None
        self._reset_maze(1)

    def _reset_maze(self, size: int) -> None:
        self.maze_size = size
        cols, rows = MAZE_SIZES[size]
        self.cols = cols
        self.rows = rows
        self.cell = min(WIDTH // cols, self.GAME_AREA_H // rows)
        self.maze = self._generate(cols, rows)
        self.ball_x = self.cell * 1.5
        self.ball_y = self.cell * 1.5

    def _generate(self, cols: int, rows: int) -> list:
        maze = [[1] * cols for _ in range(rows)]

        def carve(x, y):
            dirs = [(0, -2), (0, 2), (-2, 0), (2, 0)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 < nx < cols - 1 and 0 < ny < rows - 1 and maze[ny][nx] == 1:
                    maze[y + dy // 2][x + dx // 2] = 0
                    maze[ny][nx] = 0
                    carve(nx, ny)

        maze[1][1] = 0
        carve(1, 1)
        maze[rows - 2][cols - 2] = 0
        return maze

    def start(self) -> None:
        if self.state != "running":
            self.state = "running"
            self.start_time = time.time()

    def toggle_pause(self) -> None:
        if self.state == "running":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "running"

    def reset(self) -> None:
        self.state = "idle"
        self.start_time = None
        self.ball_x = self.cell * 1.5
        self.ball_y = self.cell * 1.5

    def update_settings(self, data: dict) -> None:
        self.difficulty = data.get("difficulty", 1)
        self.speed = data.get("speed", 3)
        size = data.get("maze_size", 1)
        if size != self.maze_size:
            self._reset_maze(size)

    def update(self) -> bool:
        """Déplace la balle. Retourne True si victoire."""
        if self.state != "running":
            return False

        spd = self.speed * 1.5
        dx  = math.sin(math.radians(self.roll))  * spd
        dy  = math.sin(math.radians(self.pitch)) * spd
        nx  = self.ball_x + dx
        ny  = self.ball_y + dy
        col = int(nx // self.cell)
        row = int(ny // self.cell)

        if 0 <= col < self.cols and 0 <= row < self.rows and self.maze[row][col] == 0:
            self.ball_x, self.ball_y = nx, ny

        if col == self.cols - 2 and row == self.rows - 2:
            elapsed = time.time() - self.start_time
            if self.best_time is None or elapsed < self.best_time:
                self.best_time = elapsed
            self.state = "victory"
            self.start_time = None
            return True
        return False


# ═══════════════════════════════════════════════════════════════
# VUE — Affichage des capteurs (Dashboard)
# ═══════════════════════════════════════════════════════════════
class SensorDisplay:
    """Affiche les données des capteurs dans le dashboard."""

    COL_L   = 10
    COL_R   = 410
    COL_W   = 380
    Y_START = 50

    def __init__(self, screen: pygame.Surface, fonts: dict):
        self._screen = screen
        self._fonts  = fonts

    def draw(self, data: SensorData, game_state: str = "idle") -> tuple:
        """Dessine tous les panneaux. Retourne (led_buttons, game_buttons)."""
        self._draw_buttons_panel(data.buttons)
        self._draw_pots_panel(data.pots)
        led_buttons = self._draw_led_panel()
        self._draw_accel_panel(data.accel)
        self._draw_status_panel(data.status)
        game_buttons = self._draw_game_commands_panel(game_state)
        return led_buttons, game_buttons

    def _panel(self, x: int, y: int, w: int, h: int, title: str) -> None:
        pygame.draw.rect(self._screen, LIGHT_GRAY, (x, y, w, h), border_radius=8)
        pygame.draw.rect(self._screen, DARK_GRAY,  (x, y, w, h), 2, border_radius=8)
        lbl = self._fonts["medium"].render(title, True, BLACK)
        self._screen.blit(lbl, (x + 8, y + 6))

    def _draw_buttons_panel(self, buttons: dict) -> None:
        x, y, w, h = self.COL_L, self.Y_START, self.COL_W, 80
        self._panel(x, y, w, h, "Boutons")
        for i, (name, key) in enumerate([("BTN1", "btn1"), ("BTN2", "btn2"), ("BTN3", "btn3")]):
            cx = x + 70 + i * 110
            cy = y + 52
            pressed = buttons.get(key, False)
            color = GREEN if pressed else DARK_GRAY
            pygame.draw.circle(self._screen, color, (cx, cy), 18)
            pygame.draw.circle(self._screen, BLACK, (cx, cy), 18, 2)
            lbl = self._fonts["small"].render(name, True, WHITE if pressed else GRAY)
            self._screen.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))

    def _draw_pots_panel(self, pots: dict) -> None:
        x, y, w, h = self.COL_L, self.Y_START + 90, self.COL_W, 110
        self._panel(x, y, w, h, "Potentiometres")
        pot1    = pots.get("pot1", 0)
        diff    = pots.get("difficulty", 1)
        speed   = pots.get("speed", 3)
        maze_sz = pots.get("maze_size", 1)

        fy = y + 32
        for line in [
            f"POT1: {pot1}       Difficulte: {diff}",
            f"Vitesse: {speed}        Taille: {maze_sz}",
        ]:
            self._screen.blit(self._fonts["small"].render(line, True, BLACK), (x + 10, fy))
            fy += 22

        bx, by, bw, bh = x + 10, y + 80, w - 20, 14
        pct = pot1 / 4095.0
        pygame.draw.rect(self._screen, DARK_GRAY, (bx, by, bw, bh))
        pygame.draw.rect(self._screen, BLUE, (bx, by, int(bw * pct), bh))
        pygame.draw.rect(self._screen, BLACK, (bx, by, bw, bh), 2)
        pct_lbl = self._fonts["tiny"].render(f"{int(pct * 100)} %", True, WHITE)
        self._screen.blit(pct_lbl, (bx + 4, by + 1))

    def _draw_led_panel(self) -> list:
        x, y, w, h = self.COL_L, self.Y_START + 210, self.COL_W, 80
        self._panel(x, y, w, h, "Controle LED")
        buttons = []
        configs = [
            (x + 15,  y + 42, 100, 30, "on",    GREEN),
            (x + 130, y + 42, 100, 30, "off",   RED),
            (x + 245, y + 42, 110, 30, "blink", ORANGE),
        ]
        for bx, by, bw, bh, cmd, color in configs:
            pygame.draw.rect(self._screen, color, (bx, by, bw, bh), border_radius=5)
            pygame.draw.rect(self._screen, BLACK, (bx, by, bw, bh), 2, border_radius=5)
            lbl = self._fonts["small"].render(cmd.upper(), True, BLACK)
            self._screen.blit(lbl, (bx + bw // 2 - lbl.get_width() // 2,
                                    by + bh // 2 - lbl.get_height() // 2))
            buttons.append((bx, by, bw, bh, cmd))
        return buttons

    def _draw_accel_panel(self, accel: dict) -> None:
        x, y, w, h = self.COL_R, self.Y_START, self.COL_W, 190
        self._panel(x, y, w, h, "Accelerometre")
        ax    = accel.get("x", 0.0)
        ay    = accel.get("y", 0.0)
        az    = accel.get("z", 1.0)
        roll  = accel.get("roll",  0.0)
        pitch = accel.get("pitch", 0.0)

        fy = y + 32
        for line in [
            f"X: {ax:+.2f} g    Roll:  {roll:+.1f} deg",
            f"Y: {ay:+.2f} g    Pitch: {pitch:+.1f} deg",
            f"Z: {az:+.2f} g",
        ]:
            self._screen.blit(self._fonts["small"].render(line, True, BLACK), (x + 10, fy))
            fy += 22

        cx_c = x + w - 65
        cy_c = y + 115
        r = 55
        pygame.draw.circle(self._screen, WHITE,      (cx_c, cy_c), r)
        pygame.draw.circle(self._screen, DARK_GRAY,  (cx_c, cy_c), r, 2)
        pygame.draw.line(self._screen, LIGHT_GRAY, (cx_c - r, cy_c), (cx_c + r, cy_c), 1)
        pygame.draw.line(self._screen, LIGHT_GRAY, (cx_c, cy_c - r), (cx_c, cy_c + r), 1)
        px = cx_c + int(max(-r + 8, min(r - 8, roll  * 0.8)))
        py = cy_c + int(max(-r + 8, min(r - 8, pitch * 0.8)))
        pygame.draw.circle(self._screen, RED,   (px, py), 9)
        pygame.draw.circle(self._screen, BLACK, (px, py), 9, 2)

    def _draw_status_panel(self, status: dict) -> None:
        x, y, w, h = self.COL_R, self.Y_START + 200, self.COL_W, 55
        self._panel(x, y, w, h, "Statut Systeme")
        uptime = status.get("uptime", 0)
        rssi   = status.get("rssi", 0)
        lbl = self._fonts["small"].render(
            f"Uptime: {uptime} s        RSSI: {rssi} dBm", True, BLACK)
        self._screen.blit(lbl, (x + 10, y + 32))

    def _draw_game_commands_panel(self, game_state: str) -> list:
        x, y, w, h = self.COL_R, self.Y_START + 260, self.COL_W, 130
        self._panel(x, y, w, h, "Commandes Jeu")

        state_colors = {
            "idle": DARK_GRAY, "running": GREEN,
            "paused": ORANGE,  "victory": GOLD,
        }
        color = state_colors.get(game_state, DARK_GRAY)
        state_lbl = self._fonts["small"].render(
            f"Etat: {game_state.upper()}", True, color)
        self._screen.blit(state_lbl, (x + 10, y + 30))

        pause_label = "REPRISE" if game_state == "paused" else "PAUSE"
        buttons = []
        configs = [
            (x + 10,  y + 62, 108, 38, "start", GREEN,  "DEMARRER"),
            (x + 130, y + 62, 108, 38, "pause", ORANGE, pause_label),
            (x + 250, y + 62, 108, 38, "reset", RED,    "RESET"),
        ]
        for bx, by, bw, bh, cmd, clr, label in configs:
            pygame.draw.rect(self._screen, clr,   (bx, by, bw, bh), border_radius=5)
            pygame.draw.rect(self._screen, BLACK, (bx, by, bw, bh), 2, border_radius=5)
            lbl = self._fonts["small"].render(label, True, BLACK)
            self._screen.blit(lbl, (bx + bw // 2 - lbl.get_width()  // 2,
                                    by + bh // 2 - lbl.get_height() // 2))
            buttons.append((bx, by, bw, bh, cmd))
        return buttons


# ═══════════════════════════════════════════════════════════════
# VUE — Affichage du jeu
# ═══════════════════════════════════════════════════════════════
class GameDisplay:
    """Rendu graphique du labyrinthe et du HUD."""

    def __init__(self, screen: pygame.Surface, fonts: dict):
        self._screen = screen
        self._fonts  = fonts

    def draw(self, game: MazeGame) -> dict:
        """Dessine le labyrinthe, la balle et le HUD. Retourne les boutons du HUD."""
        for r in range(game.rows):
            for c in range(game.cols):
                color = BLACK if game.maze[r][c] == 1 else WHITE
                pygame.draw.rect(self._screen, color,
                                 (c * game.cell, r * game.cell, game.cell, game.cell))

        goal = pygame.Rect((game.cols - 2) * game.cell, (game.rows - 2) * game.cell,
                           game.cell, game.cell)
        pygame.draw.rect(self._screen, GREEN, goal)
        pygame.draw.rect(self._screen, RED,   goal, 2)

        br = max(game.cell // 2 - 2, 6)
        pygame.draw.circle(self._screen, GOLD,  (int(game.ball_x), int(game.ball_y)), br)
        pygame.draw.circle(self._screen, BLACK, (int(game.ball_x), int(game.ball_y)), br, 2)

        return self._draw_hud(game)

    def _draw_hud(self, game: MazeGame) -> dict:
        hud_y = game.rows * game.cell
        pygame.draw.rect(self._screen, GRAY, (0, hud_y, WIDTH, HEIGHT - hud_y))

        # ── Boutons tactiles (ligne supérieure du HUD) ──────────────
        buttons: dict = {}
        btn_configs = [
            ("start",  5,   78, "DEMARRER", GREEN),
            ("pause",  90,  78, "PAUSE",    ORANGE),
            ("reset",  175, 78, "RESET",    RED),
        ]
        for name, bx_off, bw, label, clr in btn_configs:
            r = pygame.Rect(bx_off, hud_y + 4, bw, 36)
            pygame.draw.rect(self._screen, clr,   r, border_radius=6)
            pygame.draw.rect(self._screen, BLACK, r, 2, border_radius=6)
            lbl = self._fonts["small"].render(label, True, BLACK)
            self._screen.blit(lbl, (r.centerx - lbl.get_width()  // 2,
                                    r.centery - lbl.get_height() // 2))
            buttons[name] = r

        # ── Informations de jeu ─────────────────────────────────────
        elapsed = ""
        if game.start_time and game.state == "running":
            elapsed = f"{time.time() - game.start_time:.1f} s"
        best = (f"Meilleur: {game.best_time:.1f} s"
                if game.best_time else "Meilleur: --")

        self._screen.blit(
            self._fonts["small"].render(
                f"Etat: {game.state.upper()}  |  Temps: {elapsed}  |  {best}",
                True, BLACK),
            (10, hud_y + 46))
        self._screen.blit(
            self._fonts["small"].render(
                f"Diff: {game.difficulty}  |  Vitesse: {game.speed}"
                f"  |  Taille: {game.maze_size}",
                True, BLACK),
            (10, hud_y + 66))

        # ── Bouton Dashboard ────────────────────────────────────────
        dash_btn = pygame.Rect(WIDTH - 190, hud_y + 4, 178, 36)
        pygame.draw.rect(self._screen, ORANGE, dash_btn, border_radius=8)
        pygame.draw.rect(self._screen, BLACK,  dash_btn, 2, border_radius=8)
        lbl = self._fonts["medium"].render("DASHBOARD", True, BLACK)
        self._screen.blit(lbl, (dash_btn.centerx - lbl.get_width()  // 2,
                                 dash_btn.centery - lbl.get_height() // 2))
        buttons["dashboard"] = dash_btn

        return buttons


# ═══════════════════════════════════════════════════════════════
# CONTROLEUR — LED
# ═══════════════════════════════════════════════════════════════
class LEDControl:
    """Contrôle des LEDs via MQTT."""

    def __init__(self, mqtt_client):
        self._client = mqtt_client

    def toggle(self, state: str) -> None:
        """Envoie une commande LED : 'on', 'off' ou 'blink'."""
        try:
            self._client.publish(TOPIC_LED, json.dumps({"state": state}))
            print(f"[LED] {state}")
        except Exception as e:
            print(f"[LED] Erreur: {e}")

    def send_command(self, cmd: str) -> None:
        try:
            self._client.publish(TOPIC_COMMAND, json.dumps({"command": cmd}))
        except Exception as e:
            print(f"[CMD] Erreur: {e}")


# ═══════════════════════════════════════════════════════════════
# CONTROLEUR — MQTT
# ═══════════════════════════════════════════════════════════════
class MQTTHandler:
    """Gère la connexion MQTT et route les messages vers le modèle."""

    def __init__(self, data: SensorData, game: MazeGame):
        self._data   = data
        self._game   = game
        self._client = mqtt.Client(transport="websockets")
        self._client.ws_set_options(path="/")
        self._client.tls_set()
        self._client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message    = self._on_message
        self.led = LEDControl(self._client)

    def connect(self) -> None:
        try:
            self._client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self._client.loop_start()
            print(f"[MQTT] Connexion WebSocket SSL -> {MQTT_BROKER}:{MQTT_PORT}")
        except Exception as e:
            print(f"[MQTT] Erreur connexion: {e}")

    def stop(self) -> None:
        self._client.loop_stop()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._data.mqtt_connected = True
            print(f"[MQTT] Connecte (rc={rc})")
            for topic in (TOPIC_BUTTONS, TOPIC_POTS, TOPIC_ACCEL,
                          TOPIC_STATE, TOPIC_STATUS):
                client.subscribe(topic)
        else:
            self._data.mqtt_connected = False
            print(f"[MQTT] Echec connexion (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        self._data.mqtt_connected = False
        print(f"[MQTT] Deconnecte (rc={rc})")

    def _on_message(self, client, userdata, msg):
        if not msg.payload:
            return
        try:
            data = json.loads(msg.payload)
            self._data.last_update = time.time()

            if msg.topic == TOPIC_BUTTONS:
                self._data.buttons = data
                if data.get("btn1"):
                    self._game.start()
                    self.led.toggle("on")
                if data.get("btn2"):
                    self._game.toggle_pause()
                if data.get("btn3"):
                    self._game.reset()
                    self.led.toggle("off")

            elif msg.topic == TOPIC_POTS:
                self._data.pots = data
                self._game.update_settings(data)

            elif msg.topic == TOPIC_ACCEL:
                self._data.accel = data
                self._game.roll  = data.get("roll",  0.0)
                self._game.pitch = data.get("pitch", 0.0)

            elif msg.topic == TOPIC_STATUS:
                self._data.status = data

            elif msg.topic == TOPIC_STATE:
                self._game.state = data.get("state", "idle")

        except Exception as e:
            print(f"[MQTT] Erreur message: {e}")


# ═══════════════════════════════════════════════════════════════
# APPLICATION PRINCIPALE
# ═══════════════════════════════════════════════════════════════
class App:
    """Application principale — gère le cycle de vie et la boucle d'événements."""

    def __init__(self):
        if not init_display():
            sys.exit(1)

        pygame.init()
        self._screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN | pygame.SCALED)
        self._canvas = pygame.Surface((WIDTH, HEIGHT))
        pygame.display.set_caption("Labyrinthe IoT")
        pygame.mouse.set_visible(True)

        self._fonts = {
            "tiny":   pygame.font.Font(None, 18),
            "small":  pygame.font.Font(None, 22),
            "medium": pygame.font.Font(None, 28),
            "large":  pygame.font.Font(None, 36),
            "big":    pygame.font.Font(None, 52),
        }
        self._clock       = pygame.time.Clock()
        self._mode        = "dashboard"
        self._data        = SensorData()
        self._game        = MazeGame()
        self._sensor_view = SensorDisplay(self._canvas, self._fonts)
        self._game_view   = GameDisplay(self._canvas, self._fonts)
        self._mqtt        = MQTTHandler(self._data, self._game)
        self._mqtt.connect()

        # TouchReader evdev (basé sur Labo-02)
        self._touch_queue = Queue()
        self._touch = self._init_touch()

    def _init_touch(self):
        """Initialise le TouchReader evdev (comme Labo-02)."""
        if not EVDEV_AVAILABLE:
            return None
        try:
            reader = TouchReader(self._touch_queue)
            reader.start()
            print("[Touch] TouchReader démarré")
            return reader
        except RuntimeError as e:
            print(f"[Touch] {e} — mode souris uniquement")
            return None

    def _touch_to_pixel(self, x_raw: int, y_raw: int) -> tuple:
        """
        Convertit les coordonnées evdev brutes en pixels écran.
        Applique la même rotation 90° gauche que xinitrc.sh (Goodix RPi).
        """
        dx = max(1, self._touch.max_x - self._touch.min_x)
        dy = max(1, self._touch.max_y - self._touch.min_y)
        x_norm = (x_raw - self._touch.min_x) / dx
        y_norm = (y_raw - self._touch.min_y) / dy
        # Rotation 90° CW — correspond à video=DSI-2:rotate=90 dans cmdline.txt
        sx = y_norm
        sy = 1.0 - x_norm
        return (max(0, min(WIDTH - 1, int(sx * WIDTH))),
                max(0, min(HEIGHT - 1, int(sy * HEIGHT))))

    def run(self) -> None:
        print("[APP] Démarrage — ESC pour quitter")
        running = True
        while running:
            if self._mode == "dashboard":
                running = self._tick_dashboard()
            else:
                running = self._tick_game()
            rotated = pygame.transform.rotate(self._canvas, -90)
            self._screen.blit(rotated, (0, 0))
            pygame.display.flip()
            self._clock.tick(FPS)
        self._shutdown()

    # ── Dashboard ─────────────────────────────────────────────
    def _tick_dashboard(self) -> bool:
        self._canvas.fill(WHITE)
        self._draw_header()
        led_buttons, game_buttons = self._sensor_view.draw(
            self._data, self._game.state)
        game_btn = self._draw_game_button()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return False
                elif event.key == pygame.K_g:
                    self._mode = "game"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_dashboard_click(event.pos[0], event.pos[1],
                                             led_buttons, game_buttons, game_btn)

        # Événements tactiles evdev (comme Labo-02)
        if self._touch:
            try:
                while True:
                    kind, x_raw, y_raw = self._touch_queue.get_nowait()
                    if kind == "tap":
                        px, py = self._touch_to_pixel(x_raw, y_raw)
                        self._handle_dashboard_click(px, py,
                                                     led_buttons, game_buttons, game_btn)
            except Empty:
                pass

        return True

    def _handle_dashboard_click(self, mx, my, led_buttons, game_buttons, game_btn):
        for bx, by, bw, bh, cmd in led_buttons:
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self._mqtt.led.toggle(cmd)
        for bx, by, bw, bh, cmd in game_buttons:
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                if cmd == "start":
                    self._game.start()
                    self._mqtt.led.toggle("on")
                    self._mqtt.led.send_command("start")
                    self._mode = "game"
                elif cmd == "pause":
                    self._game.toggle_pause()
                    self._mqtt.led.send_command("pause")
                elif cmd == "reset":
                    self._game.reset()
                    self._mqtt.led.toggle("off")
                    self._mqtt.led.send_command("reset")
        if game_btn.collidepoint(mx, my):
            self._mode = "game"

    def _draw_header(self) -> None:
        title = self._fonts["big"].render("DASHBOARD IoT", True, BLUE)
        self._canvas.blit(title, (WIDTH // 2 - title.get_width() // 2, 5))
        color = GREEN if self._data.mqtt_connected else RED
        label = "CONNECTE" if self._data.mqtt_connected else "DECONNECTE"
        pygame.draw.circle(self._canvas, color, (WIDTH - 20, 22), 10)
        lbl = self._fonts["tiny"].render(f"MQTT: {label}", True, BLACK)
        self._canvas.blit(lbl, (WIDTH - 130, 15))

    def _draw_game_button(self) -> pygame.Rect:
        btn = pygame.Rect(SensorDisplay.COL_L, HEIGHT - 60, SensorDisplay.COL_W, 48)
        pygame.draw.rect(self._canvas, BLUE, btn, border_radius=8)
        pygame.draw.rect(self._canvas, BLACK, btn, 2, border_radius=8)
        lbl = self._fonts["medium"].render("> MODE JEU", True, WHITE)
        self._canvas.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                                 btn.centery - lbl.get_height() // 2))
        return btn

    # ── Mode Jeu ───────────────────────────────────────────────
    def _tick_game(self) -> bool:
        self._canvas.fill(WHITE)
        if self._game.update():
            self._mqtt.led.toggle("blink")
            self._mqtt.led.send_command("victory")
        hud_btns = self._game_view.draw(self._game)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return False
                elif event.key == pygame.K_d:
                    self._mode = "dashboard"
                elif event.key == pygame.K_SPACE:
                    self._game.start()
                    self._mqtt.led.toggle("on")
                    self._mqtt.led.send_command("start")
                elif event.key == pygame.K_p:
                    self._game.toggle_pause()
                    self._mqtt.led.send_command("pause")
                elif event.key == pygame.K_r:
                    self._game.reset()
                    self._mqtt.led.toggle("off")
                    self._mqtt.led.send_command("reset")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_game_click(event.pos[0], event.pos[1], hud_btns)

        # Événements tactiles evdev (comme Labo-02)
        if self._touch:
            try:
                while True:
                    kind, x_raw, y_raw = self._touch_queue.get_nowait()
                    if kind == "tap":
                        px, py = self._touch_to_pixel(x_raw, y_raw)
                        self._handle_game_click(px, py, hud_btns)
            except Empty:
                pass

        return True

    def _handle_game_click(self, mx, my, hud_btns):
        if hud_btns["dashboard"].collidepoint(mx, my):
            self._mode = "dashboard"
        elif hud_btns["start"].collidepoint(mx, my):
            self._game.start()
            self._mqtt.led.toggle("on")
            self._mqtt.led.send_command("start")
        elif hud_btns["pause"].collidepoint(mx, my):
            self._game.toggle_pause()
            self._mqtt.led.send_command("pause")
        elif hud_btns["reset"].collidepoint(mx, my):
            self._game.reset()
            self._mqtt.led.toggle("off")
            self._mqtt.led.send_command("reset")

    def _shutdown(self) -> None:
        self._mqtt.stop()
        pygame.quit()
        print("[APP] Arret propre")


if __name__ == "__main__":
    App().run()
