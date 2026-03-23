
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface IoT - Projet mi-session
Labyrinthe IoT - Henri Tadja
Mode Dashboard + Mode Jeu
"""
 
import os
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'
import subprocess
try:
    subprocess.run(['xhost', '+local:'], capture_output=True, check=False)
except:
    pass

import sys
import pygame
import paho.mqtt.client as mqtt
import json
import random
import time
import math
 
# Configuration SDL pour Raspberry Pi
def init_display():
    for key in ['SDL_VIDEODRIVER', 'SDL_FBDEV', 'SDL_NOMOUSE']:
        if key in os.environ:
            del os.environ[key]
    
    if 'DISPLAY' not in os.environ and 'WAYLAND_DISPLAY' not in os.environ:
        import subprocess
        try:
            result = subprocess.run(['pgrep', 'X'], capture_output=True, timeout=1)
            if result.returncode == 0:
                print("[SDL] Serveur X détecté, définition de DISPLAY=:0")
                os.environ['DISPLAY'] = ':0'
        except:
            pass
    
    if 'DISPLAY' in os.environ or 'WAYLAND_DISPLAY' in os.environ:
        print(f"[SDL] Environnement graphique détecté")
        try:
            pygame.display.init()
            driver = pygame.display.get_driver()
            print(f"[SDL] Driver {driver} initialisé avec succès")
            return True
        except Exception as e:
            print(f"[SDL] Échec initialisation: {e}")
            return False
    
    print("[SDL] Mode console détecté, essai des drivers framebuffer...")
    drivers_config = [
        ('kmsdrm', {'SDL_VIDEODRIVER': 'kmsdrm', 'SDL_FBDEV': '/dev/fb0', 'SDL_NOMOUSE': '1'}),
        ('fbcon', {'SDL_VIDEODRIVER': 'fbcon', 'SDL_FBDEV': '/dev/fb0', 'SDL_NOMOUSE': '1'}),
    ]
    
    for driver_name, env_vars in drivers_config:
        try:
            for key in ['SDL_VIDEODRIVER', 'SDL_FBDEV', 'SDL_NOMOUSE']:
                if key in os.environ:
                    del os.environ[key]
            for key, value in env_vars.items():
                os.environ[key] = value
            pygame.display.init()
            print(f"[SDL] Driver {driver_name} initialisé")
            return True
        except Exception as e:
            continue
    
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
 
# ─── Paramètres pygame ────────────────────────────────────────
WIDTH, HEIGHT = 1024,  600
FPS           = 30
WHITE         = (255, 255, 255)
BLACK         = (0,   0,   0)
GOLD          = (255, 215, 0)
GREEN         = (0,   200, 0)
RED           = (200, 0,   0)
BLUE          = (0,   100, 255)
GRAY          = (180, 180, 180)
DARK_GRAY     = (80,  80,  80)
ORANGE        = (255, 140, 0)
 
# ─── État global ──────────────────────────────────────────────
app_mode = "dashboard"  # "dashboard" ou "game"
 
sensor_data = {
    "buttons": {"btn1": False, "btn2": False, "btn3": False},
    "pots": {"pot1": 0, "difficulty": 1, "speed": 3, "maze_size": 1},
    "accel": {"x": 0.0, "y": 0.0, "z": 1.0, "roll": 0.0, "pitch": 0.0},
    "status": {"uptime": 0, "rssi": -50},
    "mqtt_connected": False,
    "last_update": time.time(),
}
 
game_state = {
    "state": "idle",
    "roll": 0.0,
    "pitch": 0.0,
    "difficulty": 1,
    "speed": 3,
    "maze_size": 1,
    "best_time": None,
    "start_time": None,
}
# ─── Génération du labyrinthe ─────────────────────────────────
def generate_maze(cols, rows):
    maze = [[1] * cols for _ in range(rows)]
    def carve(x, y):
        dirs = [(0,-2),(0,2),(-2,0),(2,0)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x+dx, y+dy
            if 0 < nx < cols-1 and 0 < ny < rows-1 and maze[ny][nx] == 1:
                maze[y+dy//2][x+dx//2] = 0
                maze[ny][nx] = 0
                carve(nx, ny)
    maze[1][1] = 0
    carve(1, 1)
    maze[rows-2][cols-2] = 0
    return maze
 
MAZE_SIZES = {1: (21, 13), 2: (27, 17), 3: (33, 21)}
maze       = generate_maze(*MAZE_SIZES[1])
COLS, ROWS = MAZE_SIZES[1]
CELL       = min(WIDTH // COLS, (HEIGHT - 100) // ROWS)
 
ball_x = CELL * 1 + CELL // 2
ball_y = CELL * 1 + CELL // 2
 
# ─── MQTT callbacks ───────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        sensor_data["mqtt_connected"] = True
        print(f"✓ MQTT connecté (rc={rc})")
        client.subscribe(TOPIC_BUTTONS)
        client.subscribe(TOPIC_POTS)
        client.subscribe(TOPIC_ACCEL)
        client.subscribe(TOPIC_STATE)
        client.subscribe(TOPIC_STATUS)
    else:
        sensor_data["mqtt_connected"] = False
        print(f"✗ MQTT échec (rc={rc})")
 
def on_disconnect(client, userdata, rc):
    sensor_data["mqtt_connected"] = False
    print(f"✗ MQTT déconnecté (rc={rc})")
 
def on_message(client, userdata, msg):
    global maze, COLS, ROWS, CELL, ball_x, ball_y
    sensor_data["last_update"] = time.time()
    
    try:
        # Ignorer les messages vides
        if not msg.payload or len(msg.payload) == 0:
            return
        
        data = json.loads(msg.payload)
        
        if msg.topic == TOPIC_BUTTONS:
            sensor_data["buttons"] = data
            if data.get("btn1"):
                game_state["state"] = "running"
                game_state["start_time"] = time.time()
                send_led("on")
            if data.get("btn2"):
                game_state["state"] = "paused" if game_state["state"] == "running" else "running"
            if data.get("btn3"):
                game_state["state"] = "idle"
                game_state["start_time"] = None
                ball_x = CELL * 1 + CELL // 2
                ball_y = CELL * 1 + CELL // 2
                send_led("off")
                
        elif msg.topic == TOPIC_POTS:
            sensor_data["pots"] = data
            game_state["difficulty"] = data.get("difficulty", 1)
            game_state["speed"] = data.get("speed", 3)
            size = data.get("maze_size", 1)
            if size != game_state["maze_size"]:
                game_state["maze_size"] = size
                COLS, ROWS = MAZE_SIZES[size]
                CELL = min(WIDTH // COLS, (HEIGHT-100) // ROWS)
                maze = generate_maze(COLS, ROWS)
                ball_x = CELL * 1 + CELL // 2
                ball_y = CELL * 1 + CELL // 2
                
        elif msg.topic == TOPIC_ACCEL:
            sensor_data["accel"] = data
            game_state["roll"] = data.get("roll", 0)
            game_state["pitch"] = data.get("pitch", 0)
            
        elif msg.topic == TOPIC_STATUS:
            sensor_data["status"] = data
            
        elif msg.topic == TOPIC_STATE:
            game_state["state"] = data.get("state", "idle")
            
    except Exception as e:
        print(f"Erreur message: {e}")
 
def send_command(cmd):
    client.publish(TOPIC_COMMAND, json.dumps({"command": cmd}))
 
def send_led(state):
    client.publish(TOPIC_LED, json.dumps({"state": state}))
 
# ─── Connexion MQTT ───────────────────────────────────────────
client = mqtt.Client(transport="websockets")
client.ws_set_options(path="/")
client.tls_set()
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
 
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print(f"Connexion MQTT WebSocket SSL à {MQTT_BROKER}:{MQTT_PORT}...")
except Exception as e:
    print(f"Erreur connexion MQTT: {e}")
 
# ─── Pygame ───────────────────────────────────────────────────
if not init_display():
    sys.exit(1)
 
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Labyrinthe IoT - Dashboard & Jeu")
pygame.mouse.set_visible(True)
 
font_small = pygame.font.Font(None, 20)
font = pygame.font.Font(None, 28)
font_large = pygame.font.Font(None, 36)
font_big = pygame.font.Font(None, 56)
fps_clock = pygame.time.Clock()
 
# ═══════════════════════════════════════════════════════════════
# MODE DASHBOARD - Affichage des capteurs
# ═══════════════════════════════════════════════════════════════
def draw_dashboard():
    screen.fill(WHITE)
    
    # Titre
    title = font_big.render("DASHBOARD IoT", True, BLUE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 10))
    
    # Indicateur connexion MQTT
    mqtt_color = GREEN if sensor_data["mqtt_connected"] else RED
    mqtt_text = "CONNECTÉ" if sensor_data["mqtt_connected"] else "DÉCONNECTÉ"
    pygame.draw.circle(screen, mqtt_color, (WIDTH - 50, 30), 15)
    status_label = font_small.render(f"MQTT: {mqtt_text}", True, BLACK)
    screen.blit(status_label, (WIDTH - 150, 20))
    
    y_offset = 80
    
    # ─── Boutons ───
    pygame.draw.rect(screen, GRAY, (20, y_offset, 360, 100), border_radius=10)
    pygame.draw.rect(screen, BLACK, (20, y_offset, 360, 100), 2, border_radius=10)
    label = font_large.render("Boutons", True, BLACK)
    screen.blit(label, (30, y_offset + 10))
    
    btn_data = sensor_data["buttons"]
    for i, (btn_name, btn_state) in enumerate([("BTN1", btn_data.get("btn1", False)),
                                                 ("BTN2", btn_data.get("btn2", False)),
                                                 ("BTN3", btn_data.get("btn3", False))]):
        color = GREEN if btn_state else DARK_GRAY
        pygame.draw.circle(screen, color, (60 + i*110, y_offset + 65), 20)
        pygame.draw.circle(screen, BLACK, (60 + i*110, y_offset + 65), 20, 2)
        txt = font_small.render(btn_name, True, BLACK)
        screen.blit(txt, (40 + i*110, y_offset + 50))
# ─── Potentiomètres ───
    y_offset += 120
    pygame.draw.rect(screen, GRAY, (20, y_offset, 360, 120), border_radius=10)
    pygame.draw.rect(screen, BLACK, (20, y_offset, 360, 120), 2, border_radius=10)
    label = font_large.render("Potentiomètres", True, BLACK)
    screen.blit(label, (30, y_offset + 10))
    
    pot_data = sensor_data["pots"]
    pot_val = pot_data.get("pot1", 0)
    diff = pot_data.get("difficulty", 1)
    speed = pot_data.get("speed", 3)
    maze_size = pot_data.get("maze_size", 1)
    
    pot_y = y_offset + 50
    txt1 = font.render(f"POT1: {pot_val}", True, BLACK)
    screen.blit(txt1, (30, pot_y))
    
    txt2 = font.render(f"Difficulté: {diff}", True, BLACK)
    screen.blit(txt2, (30, pot_y + 25))
    
    txt3 = font.render(f"Vitesse: {speed}", True, BLACK)
    screen.blit(txt3, (200, pot_y))
    
    txt4 = font.render(f"Taille: {maze_size}", True, BLACK)
    screen.blit(txt4, (200, pot_y + 25))
    
    # Barres de progression
    bar_width = 300
    bar_height = 15
    pot_percent = pot_val / 4095.0
    pygame.draw.rect(screen, DARK_GRAY, (30, pot_y + 55, bar_width, bar_height))
    pygame.draw.rect(screen, BLUE, (30, pot_y + 55, int(bar_width * pot_percent), bar_height))
    pygame.draw.rect(screen, BLACK, (30, pot_y + 55, bar_width, bar_height), 2)
    
    # ─── Accéléromètre ───
    y_offset = 80
    x_offset = 400
    pygame.draw.rect(screen, GRAY, (x_offset, y_offset, 380, 240), border_radius=10)
    pygame.draw.rect(screen, BLACK, (x_offset, y_offset, 380, 240), 2, border_radius=10)
    label = font_large.render("Accéléromètre", True, BLACK)
    screen.blit(label, (x_offset + 10, y_offset + 10))
    
    accel_data = sensor_data["accel"]
    ax = accel_data.get("x", 0.0)
    ay = accel_data.get("y", 0.0)
    az = accel_data.get("z", 1.0)
    roll = accel_data.get("roll", 0.0)
    pitch = accel_data.get("pitch", 0.0)
    
    accel_y = y_offset + 50
    txt1 = font.render(f"X: {ax:.2f} g", True, BLACK)
    screen.blit(txt1, (x_offset + 20, accel_y))
    
    txt2 = font.render(f"Y: {ay:.2f} g", True, BLACK)
    screen.blit(txt2, (x_offset + 20, accel_y + 30))
    
    txt3 = font.render(f"Z: {az:.2f} g", True, BLACK)
    screen.blit(txt3, (x_offset + 20, accel_y + 60))
    
    txt4 = font.render(f"Roll:  {roll:.1f}°", True, BLACK)
    screen.blit(txt4, (x_offset + 20, accel_y + 100))
    
    txt5 = font.render(f"Pitch: {pitch:.1f}°", True, BLACK)
    screen.blit(txt5, (x_offset + 20, accel_y + 130))
    
    # Visualisation Roll/Pitch
    center_x = x_offset + 280
    center_y = accel_y + 100
    radius = 50
    pygame.draw.circle(screen, WHITE, (center_x, center_y), radius)
    pygame.draw.circle(screen, BLACK, (center_x, center_y), radius, 2)
    
    # Point représentant l'inclinaison
    point_x = center_x + int(roll * 1.2)
    point_y = center_y + int(pitch * 1.2)
    pygame.draw.circle(screen, RED, (point_x, point_y), 8)
    pygame.draw.circle(screen, BLACK, (point_x, point_y), 8, 2)
    
    # ─── Statut système ───
    y_offset += 260
    pygame.draw.rect(screen, GRAY, (x_offset, y_offset, 380, 60), border_radius=10)
    pygame.draw.rect(screen, BLACK, (x_offset, y_offset, 380, 60), 2, border_radius=10)
    label = font_large.render("Statut Système", True, BLACK)
    screen.blit(label, (x_offset + 10, y_offset + 10))
    
    status_data = sensor_data["status"]
    uptime = status_data.get("uptime", 0)
    rssi = status_data.get("rssi", 0)
    
    txt_uptime = font.render(f"Uptime: {uptime}s", True, BLACK)
    screen.blit(txt_uptime, (x_offset + 20, y_offset + 35))
    
    txt_rssi = font.render(f"RSSI: {rssi} dBm", True, BLACK)
    screen.blit(txt_rssi, (x_offset + 200, y_offset + 35))
    
    # ─── Contrôle LED ───
    y_offset = 340
    pygame.draw.rect(screen, GRAY, (20, y_offset, 360, 100), border_radius=10)
    pygame.draw.rect(screen, BLACK, (20, y_offset, 360, 100), 2, border_radius=10)
    label = font_large.render("Contrôle LED", True, BLACK)
    screen.blit(label, (30, y_offset + 10))
    
    # Boutons LED
    btn_y = y_offset + 50
    buttons_led = [
        (40, btn_y, 90, 35, "ON", GREEN),
        (145, btn_y, 90, 35, "OFF", RED),
        (250, btn_y, 90, 35, "BLINK", ORANGE),
    ]
    
    for bx, by, bw, bh, text, color in buttons_led:
        pygame.draw.rect(screen, color, (bx, by, bw, bh), border_radius=5)
        pygame.draw.rect(screen, BLACK, (bx, by, bw, bh), 2, border_radius=5)
        btn_text = font.render(text, True, BLACK)
        text_rect = btn_text.get_rect(center=(bx + bw//2, by + bh//2))
        screen.blit(btn_text, text_rect)
# ─── Bouton Mode Jeu ───
    btn_game = pygame.Rect(WIDTH - 200, HEIGHT - 60, 180, 50)
    pygame.draw.rect(screen, BLUE, btn_game, border_radius=10)
    pygame.draw.rect(screen, BLACK, btn_game, 3, border_radius=10)
    game_txt = font_large.render("MODE JEU", True, WHITE)
    text_rect = game_txt.get_rect(center=btn_game.center)
    screen.blit(game_txt, text_rect)
    
    return buttons_led, btn_game
 
# ═══════════════════════════════════════════════════════════════
# MODE JEU - Labyrinthe
# ═══════════════════════════════════════════════════════════════
def draw_maze():
    for r in range(ROWS):
        for c in range(COLS):
            color = BLACK if maze[r][c] == 1 else WHITE
            pygame.draw.rect(screen, color, (c*CELL, r*CELL, CELL, CELL))
    goal_rect = pygame.Rect((COLS-2)*CELL, (ROWS-2)*CELL, CELL, CELL)
    pygame.draw.rect(screen, GREEN, goal_rect)
    pygame.draw.rect(screen, RED, goal_rect, 2)
 
def draw_ball():
    ball_radius = max(CELL//2 - 2, 8)
    pygame.draw.circle(screen, GOLD, (int(ball_x), int(ball_y)), ball_radius)
    pygame.draw.circle(screen, BLACK, (int(ball_x), int(ball_y)), ball_radius, 2)
 
def draw_game_hud():
    elapsed = ""
    if game_state["start_time"] and game_state["state"] == "running":
        elapsed = f"{time.time() - game_state['start_time']:.1f}s"
    best = f"Meilleur: {game_state['best_time']:.1f}s" if game_state["best_time"] else "Meilleur: --"
    state_txt = game_state["state"].upper()
    
    pygame.draw.rect(screen, GRAY, (0, ROWS*CELL, WIDTH, HEIGHT - ROWS*CELL))
    
    hud_text = f"État: {state_txt}  |  Temps: {elapsed}  |  {best}"
    hud = font.render(hud_text, True, BLACK)
    screen.blit(hud, (10, ROWS*CELL + 5))
    
    info_text = f"Diff: {game_state['difficulty']}  |  Vitesse: {game_state['speed']}  |  Taille: {game_state['maze_size']}"
    info = font.render(info_text, True, BLACK)
    screen.blit(info, (10, ROWS*CELL + 30))
    
    # Bouton retour Dashboard
    btn_dashboard = pygame.Rect(WIDTH - 200, ROWS*CELL + 10, 180, 50)
    pygame.draw.rect(screen, ORANGE, btn_dashboard, border_radius=10)
    pygame.draw.rect(screen, BLACK, btn_dashboard, 3, border_radius=10)
    dash_txt = font_large.render("DASHBOARD", True, BLACK)
    text_rect = dash_txt.get_rect(center=btn_dashboard.center)
    screen.blit(dash_txt, text_rect)
    
    return btn_dashboard
 
def move_ball():
    global ball_x, ball_y
    if game_state["state"] != "running":
        return
    speed = game_state["speed"] * 1.5
    dx = math.sin(math.radians(game_state["roll"])) * speed
    dy = math.sin(math.radians(game_state["pitch"])) * speed
    new_x = ball_x + dx
    new_y = ball_y + dy
    col = int(new_x // CELL)
    row = int(new_y // CELL)
    if 0 <= col < COLS and 0 <= row < ROWS and maze[row][col] == 0:
        ball_x, ball_y = new_x, new_y
 
def check_victory():
    col = int(ball_x // CELL)
    row = int(ball_y // CELL)
    if col == COLS-2 and row == ROWS-2 and game_state["state"] == "running":
        elapsed = time.time() - game_state["start_time"]
        if game_state["best_time"] is None or elapsed < game_state["best_time"]:
            game_state["best_time"] = elapsed
        game_state["state"] = "victory"
        game_state["start_time"] = None
        send_led("blink")
        send_command("victory")
 
# ─── Boucle principale ────────────────────────────────────────
running = True
print(f"[APP] Démarrage en mode: {app_mode}")
print("[CONTROLES] ESC=Quitter | Clic sur boutons pour changer de mode")
 
while running:
    pygame.event.pump()
    
    if app_mode == "dashboard":
        led_buttons, game_button = draw_dashboard()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_g:
                    app_mode = "game"
                    print("[APP] Passage en mode JEU")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Boutons LED
                for bx, by, bw, bh, text, color in led_buttons:
                    if bx <= mx <= bx+bw and by <= my <= by+bh:
                        send_led(text.lower())
                        print(f"[LED] Commande: {text}")
                # Bouton Mode Jeu
                if game_button.collidepoint(mx, my):
                    app_mode = "game"
                    print("[APP] Passage en mode JEU")
    
    elif app_mode == "game":
        screen.fill(WHITE)
        move_ball()
        check_victory()
        draw_maze()
        draw_ball()
        dashboard_button = draw_game_hud()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_d:
                    app_mode = "dashboard"
                    print("[APP] Passage en mode DASHBOARD")
                elif event.key == pygame.K_SPACE:
                    game_state["state"] = "running"
                    game_state["start_time"] = time.time()
                    send_led("on")
                elif event.key == pygame.K_r:
                    game_state["state"] = "idle"
                    game_state["start_time"] = None
                    ball_x = CELL * 1 + CELL // 2
                    ball_y = CELL * 1 + CELL // 2
                    send_led("off")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if dashboard_button.collidepoint(mx, my):
                    app_mode = "dashboard"
                    print("[APP] Passage en mode DASHBOARD")
    
    pygame.display.flip()
    fps_clock.tick(FPS)
 
client.loop_stop()
pygame.quit()
print("[APP] Arrêt propre")
 
