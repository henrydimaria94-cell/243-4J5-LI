import threading
import time
from queue import Queue

import curses
from evdev import InputDevice, ecodes, list_devices
import serial


# ---------- GESTION DU TOUCH ----------

class TouchReader(threading.Thread):
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

    def _find_touch_device(self):
        for path in list_devices():
            dev = InputDevice(path)
            name = dev.name.lower()
            if "touch" in name or "ft5406" in name:
                print(f"[TouchReader] Using device: {dev.name} ({path})")
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


# ---------- UI CURSES ----------

# Paires de couleurs
COLOR_BTN_NORMAL  = 1  # bouton normal (cyan)
COLOR_BTN_ACTIVE  = 2  # bouton actif
COLOR_STATUS      = 3  # texte status (jaune)
COLOR_BTN_BLEU    = 4  # bouton BLEU fond bleu
COLOR_BTN_VERT    = 5  # bouton VERT fond vert
COLOR_LED_ON_B    = 6  # indicateur LED bleue allumée
COLOR_LED_ON_V    = 7  # indicateur LED verte allumée
COLOR_LED_OFF     = 8  # indicateur LED éteinte
COLOR_PANEL_TITLE = 9  # titre panneau


class LEDControlUI:
    def __init__(self, stdscr, touch_reader: TouchReader, event_queue: Queue):
        self.stdscr = stdscr
        self.touch_reader = touch_reader
        self.event_queue = event_queue
        self.running = True
        self.status_message = "Prêt - Contrôle des LEDs"

        # Communication série avec l'ESP32 A7670E
        self.serial_port = None
        self._init_serial()

        self.buttons = []

        # Buffer pour les messages série reçus (max 8 lignes)
        self.serial_feedback = []
        self.max_feedback_lines = 8

        # État visuel des LEDs
        # GPIO 27 = LED verte, GPIO 12 = LED bleue
        self.led_verte_on = False   # GPIO 27
        self.led_bleue_on = False   # GPIO 12

        # Timestamp du dernier appui (pour flash visuel)
        self.last_bleu_press = 0.0
        self.last_vert_press = 0.0

    def _init_serial(self):
        try:
            self.serial_port = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
            time.sleep(2)
            self.status_message = "Port serie connecte: /dev/ttyACM0"
        except Exception as e:
            self.status_message = f"Erreur port serie: {str(e)}"
            self.serial_port = None

    def _send_command(self, command):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(f"{command}\n".encode())
                self.status_message = f"Commande envoyee: {command}"
                if command == "bleu":
                    self.led_bleue_on = True
                    self.led_verte_on = False
                elif command == "vert":
                    self.led_verte_on = True
                    self.led_bleue_on = False
                elif command in ("off", "eteindre"):
                    self.led_bleue_on = False
                    self.led_verte_on = False
            except Exception as e:
                self.status_message = f"Erreur d'envoi: {str(e)}"
        else:
            self.status_message = "Port serie non disponible"

    def _read_serial(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                while self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.serial_feedback.append(line)
                        if len(self.serial_feedback) > self.max_feedback_lines:
                            self.serial_feedback.pop(0)
            except Exception:
                pass

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(COLOR_BTN_NORMAL,  curses.COLOR_BLACK,  curses.COLOR_CYAN)
        curses.init_pair(COLOR_BTN_ACTIVE,  curses.COLOR_WHITE,  curses.COLOR_GREEN)
        curses.init_pair(COLOR_STATUS,      curses.COLOR_YELLOW, -1)
        curses.init_pair(COLOR_BTN_BLEU,    curses.COLOR_WHITE,  curses.COLOR_BLUE)
        curses.init_pair(COLOR_BTN_VERT,    curses.COLOR_WHITE,  curses.COLOR_GREEN)
        curses.init_pair(COLOR_LED_ON_B,    curses.COLOR_WHITE,  curses.COLOR_BLUE)
        curses.init_pair(COLOR_LED_ON_V,    curses.COLOR_WHITE,  curses.COLOR_GREEN)
        curses.init_pair(COLOR_LED_OFF,     curses.COLOR_BLACK,  curses.COLOR_WHITE)
        curses.init_pair(COLOR_PANEL_TITLE, curses.COLOR_CYAN,   -1)

    def _build_buttons(self, h, w):
        """
        Construit 3 boutons dans la moitié gauche de l'écran :
          - BLEU (haut, très grand)  → envoie "bleu" → GPIO 12
          - VERT (milieu, très grand) → envoie "vert" → GPIO 27
          - QUIT (bas, normal)
        Préserve l'état active des boutons existants.
        """
        active_states = {btn["label"]: btn["active"] for btn in self.buttons}
        self.buttons = []

        if w >= 60:
            btn_zone_w = w // 2 - 2
        else:
            btn_zone_w = w - 4

        btn_col   = 1
        btn_width = max(10, btn_zone_w)
        btn_width = min(btn_width, w - btn_col - 1)

        usable_h    = h - 5
        color_btn_h = max(3, usable_h // 3)
        quit_btn_h  = max(3, min(4, usable_h - color_btn_h * 2 - 2))

        start_row = 2

        buttons_config = [
            {
                "label":      "BLEU",
                "color_pair": COLOR_BTN_BLEU,
                "command":    "bleu",
                "height":     color_btn_h,
            },
            {
                "label":      "VERT",
                "color_pair": COLOR_BTN_VERT,
                "command":    "vert",
                "height":     color_btn_h,
            },
            {
                "label":      "QUIT",
                "color_pair": COLOR_BTN_NORMAL,
                "command":    None,
                "height":     quit_btn_h,
            },
        ]

        row = start_row
        for btn_cfg in buttons_config:
            self.buttons.append({
                "label":      btn_cfg["label"],
                "row":        row,
                "col":        btn_col,
                "height":     btn_cfg["height"],
                "width":      btn_width,
                "active":     active_states.get(btn_cfg["label"], False),
                "color_pair": btn_cfg["color_pair"],
                "command":    btn_cfg["command"],
            })
            row += btn_cfg["height"] + 1

    def _draw_led_panel(self, h, w):
        """
        Panneau de contrôle visuel des LEDs dans la moitié droite.
        GPIO 27 = LED verte, GPIO 12 = LED bleue.
        """
        if w < 60:
            return

        panel_col   = w // 2 + 1
        panel_width = w - panel_col - 1
        panel_row   = 2

        # Titre du panneau
        title = " Panneau de controle LED "
        self.stdscr.attron(curses.color_pair(COLOR_PANEL_TITLE) | curses.A_BOLD)
        try:
            self.stdscr.addstr(panel_row, panel_col,
                               title[:panel_width].center(panel_width))
        except curses.error:
            pass
        self.stdscr.attroff(curses.color_pair(COLOR_PANEL_TITLE) | curses.A_BOLD)

        # Indicateurs LED
        row = panel_row + 2

        leds = [
            {
                "gpio":     27,
                "nom":      "LED VERTE",
                "on":       self.led_verte_on,
                "color_on": COLOR_LED_ON_V,
            },
            {
                "gpio":     12,
                "nom":      "LED BLEUE",
                "on":       self.led_bleue_on,
                "color_on": COLOR_LED_ON_B,
            },
        ]

        indicator_h = 4

        for led in leds:
            color  = curses.color_pair(led["color_on"] if led["on"] else COLOR_LED_OFF)
            etat   = "ALLUMEE" if led["on"] else "ETEINTE"
            safe_w = min(panel_width, w - panel_col - 1)

            for r in range(row, row + indicator_h):
                if r < h - 3:
                    try:
                        self.stdscr.attron(color)
                        self.stdscr.addstr(r, panel_col, " " * safe_w)
                        self.stdscr.attroff(color)
                    except curses.error:
                        pass

            try:
                self.stdscr.attron(color | curses.A_BOLD)
                self.stdscr.addstr(row,     panel_col, f"  GPIO {led['gpio']}"[:safe_w])
                self.stdscr.addstr(row + 1, panel_col, f"  {led['nom']}"[:safe_w])
                self.stdscr.addstr(row + 2, panel_col, f"  {etat}"[:safe_w])
                self.stdscr.attroff(color | curses.A_BOLD)
            except curses.error:
                pass

            row += indicator_h + 1

        # Feedback série
        row += 1
        fb_title = " Retour Arduino "
        self.stdscr.attron(curses.A_UNDERLINE | curses.A_BOLD)
        try:
            self.stdscr.addstr(row, panel_col, fb_title[:panel_width])
        except curses.error:
            pass
        self.stdscr.attroff(curses.A_UNDERLINE | curses.A_BOLD)

        row += 1
        for msg in self.serial_feedback:
            if row >= h - 3:
                break
            try:
                self.stdscr.addstr(row, panel_col, msg[:panel_width])
            except curses.error:
                pass
            row += 1

    def _draw(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        # Titre global
        title = " ESP32 A7670E - Controle de LEDs "
        self.stdscr.attron(curses.A_BOLD | curses.A_REVERSE)
        try:
            self.stdscr.addstr(0, max(0, (w - len(title)) // 2), title)
        except curses.error:
            pass
        self.stdscr.attroff(curses.A_BOLD | curses.A_REVERSE)

        # Séparateur vertical
        if w >= 60:
            sep_col = w // 2
            for r in range(1, h - 2):
                try:
                    self.stdscr.addstr(r, sep_col, "|")
                except curses.error:
                    pass

        # Construire et dessiner les boutons
        self._build_buttons(h, w)

        now = time.time()
        for btn in self.buttons:
            is_flashing = False
            if btn["label"] == "BLEU" and (now - self.last_bleu_press) < 0.4:
                is_flashing = True
            elif btn["label"] == "VERT" and (now - self.last_vert_press) < 0.4:
                is_flashing = True

            attr = curses.color_pair(btn["color_pair"]) | curses.A_BOLD
            if btn["active"] or is_flashing:
                attr |= curses.A_REVERSE

            safe_w = min(btn["width"], w - btn["col"] - 1)
            if safe_w <= 0:
                continue

            # Fond du bouton
            for r in range(btn["row"], btn["row"] + btn["height"]):
                if 0 <= r < h - 2:
                    try:
                        self.stdscr.attron(attr)
                        self.stdscr.addstr(r, btn["col"], " " * safe_w)
                        self.stdscr.attroff(attr)
                    except curses.error:
                        pass

            # Bordures haute et basse
            for r in [btn["row"], btn["row"] + btn["height"] - 1]:
                if 0 <= r < h - 2:
                    try:
                        self.stdscr.attron(attr | curses.A_UNDERLINE)
                        self.stdscr.addstr(r, btn["col"], "=" * safe_w)
                        self.stdscr.attroff(attr | curses.A_UNDERLINE)
                    except curses.error:
                        pass

            # Label centré
            label     = f"  {btn['label']}  "
            label_col = btn["col"] + max(0, (safe_w - len(label)) // 2)
            label_row = btn["row"] + btn["height"] // 2
            if 0 <= label_row < h - 2 and label_col + len(label) < w:
                try:
                    self.stdscr.attron(attr | curses.A_BOLD)
                    self.stdscr.addstr(label_row, label_col, label[:safe_w])
                    self.stdscr.attroff(attr | curses.A_BOLD)
                except curses.error:
                    pass

        # Panneau LED (droite)
        self._draw_led_panel(h, w)

        # Barre de statut
        self.stdscr.attron(curses.color_pair(COLOR_STATUS))
        try:
            self.stdscr.addstr(h - 2, 1, f"Status: {self.status_message[:w - 12]}")
        except curses.error:
            pass
        self.stdscr.attroff(curses.color_pair(COLOR_STATUS))

        # Aide clavier
        help_txt = " [q] Quitter "
        try:
            self.stdscr.addstr(h - 1, max(0, w - len(help_txt) - 1), help_txt)
        except curses.error:
            pass

        self.stdscr.refresh()

    def _touch_to_rowcol(self, x_raw, y_raw):
        h, w = self.stdscr.getmaxyx()
        dx = max(1, self.touch_reader.max_x - self.touch_reader.min_x)
        dy = max(1, self.touch_reader.max_y - self.touch_reader.min_y)
        x_norm = (x_raw - self.touch_reader.min_x) / dx
        y_norm = (y_raw - self.touch_reader.min_y) / dy
        col = int(x_norm * (w - 1))
        row = int(y_norm * (h - 1))
        row = max(0, min(h - 1, row))
        col = max(0, min(w - 1, col))
        return row, col

    def _handle_touch_tap(self, x_raw, y_raw):
        row, col = self._touch_to_rowcol(x_raw, y_raw)

        clicked_btn = None
        for btn in self.buttons:
            if (btn["row"] <= row < btn["row"] + btn["height"] and
                    btn["col"] <= col < btn["col"] + btn["width"]):
                clicked_btn = btn
                break

        for btn in self.buttons:
            btn["active"] = False

        if not clicked_btn:
            self.status_message = f"Touche hors bouton: row={row}, col={col}"
            return

        clicked_btn["active"] = True
        label = clicked_btn["label"]

        if label == "BLEU":
            self.last_bleu_press = time.time()
            self._send_command("bleu")
        elif label == "VERT":
            self.last_vert_press = time.time()
            self._send_command("vert")
        elif label == "QUIT":
            self.status_message = "Arret demande..."
            self.running = False

    def run(self):
        self.stdscr.nodelay(True)
        curses.curs_set(0)
        self._init_colors()

        last_redraw = 0.0

        while self.running:
            now = time.time()

            if now - last_redraw > 0.05:  # ~20 FPS
                self._draw()
                last_redraw = now

            self._read_serial()

            try:
                ch = self.stdscr.getch()
            except curses.error:
                ch = -1

            if ch == ord('q'):
                self.status_message = "Quit avec 'q'."
                self.running = False

            try:
                event = self.event_queue.get_nowait()
            except Exception:
                event = None

            if event:
                kind, x_raw, y_raw = event
                if kind == "tap":
                    self._handle_touch_tap(x_raw, y_raw)

            time.sleep(0.01)

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()


# ---------- ENTRY POINT ----------

def main(stdscr):
    event_queue = Queue()
    touch_reader = TouchReader(event_queue)
    touch_reader.start()

    ui = LEDControlUI(stdscr, touch_reader, event_queue)
    ui.run()


if __name__ == "__main__":
    curses.wrapper(main)
