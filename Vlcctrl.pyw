# -*- coding: utf-8 -*-
"""
VLC Controller Widget — Apple Liquid Edition (Ultra-Light & Automated)
- Design Apple Liquid (Glassmorphism, micro-animations douces)
- Installation & auto-bootstrap 100% automatique
- Consommation CPU < 0.2% (polling adaptatif, marquee intelligent en veille)
- Grande pochette (136x136 px, coins arrondis Apple)
- Barre de progression seekable interactive (clic et glisser)
- Sélecteur de vitesse Apple-style (détection instantanée, molette et clic)
- Menu contextuel au clic droit complet
- Panneau de configuration exhaustif avec presets de couleurs Apple
"""

import sys
import subprocess
import os

# ─────────────────────────────────────────────────────────────
#  AUTO-BOOTSTRAP DES DÉPENDANCES (100% AUTOMATIQUE)
# ─────────────────────────────────────────────────────────────
REQUIRED_PACKAGES = {
    "customtkinter": "customtkinter",
    "requests": "requests",
    "PIL": "Pillow",
    "keyboard": "keyboard",
    "pycaw": "pycaw",
    "win32gui": "pywin32",
}

missing = []
for module_name, pip_pkg in REQUIRED_PACKAGES.items():
    try:
        __import__(module_name)
    except ImportError:
        missing.append(pip_pkg)

if missing:
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check"] + missing,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    except Exception as e:
        print(f"[Bootstrap] Installation automatique dépendances échouée: {e}")

import time
import threading
import json
import traceback
import urllib.parse
from pathlib import Path
from io import BytesIO
import ctypes

import requests
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageDraw, ImageFilter

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except Exception:
    PYCAW_AVAILABLE = False

try:
    import win32gui
    import win32con
    import win32com.client
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════
#  PALETTES ET STYLES APPLE LIQUID
# ═══════════════════════════════════════════════════════════════
PALETTE = {
    "bg_root":        "#000001",
    "bg_frame":       "#121215",
    "bg_frame_soft":  "#18181c",
    "bg_card":        "#222227",
    "bg_hover":       "#2d2d34",
    "text_primary":   "#f5f5f7",
    "text_secondary": "#9898a0",
    "text_dim":       "#5a5a66",
    "border":         "#27272e",
    "slider_bg":      "#282830",
    "accent":         "#ff6b35",  # Orange Apple par défaut
}

APPLE_ACCENTS = [
    ("#ff6b35", "Orange"),
    ("#007aff", "Bleu"),
    ("#af52de", "Violet"),
    ("#34c759", "Vert"),
    ("#ff2d55", "Rose"),
    ("#ff3b30", "Rouge"),
    ("#ffd60a", "Or"),
]

FONT_TITLE   = ("Segoe UI Variable Display", 15, "bold")
FONT_ARTIST  = ("Segoe UI Variable Text", 12)
FONT_TIME    = ("Segoe UI Variable Text", 10)
FONT_BTN     = ("Segoe UI Variable Text", 11)
FONT_SMALL   = ("Segoe UI Variable Text", 10)

COVER_SIZE   = 136
COVER_RADIUS = 18
CORNER_R     = 26
WIDGET_W     = 560
WIDGET_H     = 196

# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION (ROBUSTE UTF-8 & STANDALONE EXE)
# ═══════════════════════════════════════════════════════════════
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(APP_DIR, "config.json")

DEFAULT_CONFIG = {
    "hotkey":              "alt+é",
    "hide_delay":          3500,
    "max_opacity":         0.93,
    "theme":               "Dark",
    "color_theme":         "blue",
    "accent_color":        "#ff6b35",
    "show_progress":       True,
    "show_controls":       True,
    "show_cover":          True,
    "show_speed":          True,
    "marquee_title":       True,
    "vlc_host":             "http://127.0.0.1:8080",
    "vlc_password":         "vlc",
    "position_x":          -1,
    "position_y":          -1,
    "auto_show_on_change": True,
    "pin_to_desktop":      False,
    "start_menu_shortcut": True,
    "run_on_startup":      False,
}

class Config:
    def __init__(self):
        self._data = self._load()
        self._sync_shortcuts()

    def _load(self):
        data = DEFAULT_CONFIG.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    # Nettoyage éventuel d'encodage corrompu
                    if "hotkey" in file_data and "alt+Ã©" in file_data["hotkey"]:
                        file_data["hotkey"] = "alt+é"
                    data.update(file_data)
            except Exception:
                try:
                    with open(CONFIG_FILE, "r", encoding="cp1252") as f:
                        file_data = json.load(f)
                        data.update(file_data)
                except Exception:
                    pass
        return data

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
            self._sync_shortcuts()
        except Exception as e:
            print(f"[Config] Erreur sauvegarde: {e}")

    def _sync_shortcuts(self):
        if not WIN32_AVAILABLE:
            return
        try:
            appdata = os.environ.get("APPDATA", "")
            programs_dir = os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs")
            startup_dir = os.path.join(programs_dir, "Startup")

            start_menu_lnk = os.path.join(programs_dir, "VLC Controller.lnk")
            startup_lnk = os.path.join(startup_dir, "VLC Controller.lnk")

            # Détection cible (EXE compilé ou script pythonw)
            if getattr(sys, "frozen", False):
                target_exe = sys.executable
                target_args = ""
            else:
                pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                if not os.path.exists(pythonw):
                    pythonw = "pythonw.exe"
                target_exe = pythonw
                target_args = f'"{os.path.join(APP_DIR, "Vlcctrl.pyw")}"'

            icon_path = os.path.join(APP_DIR, "app_icon.ico")
            shell = win32com.client.Dispatch("WScript.Shell")

            # 1. Raccourci Menu Démarrer
            should_start_menu = self._data.get("start_menu_shortcut", True)
            if should_start_menu and not os.path.exists(start_menu_lnk):
                s1 = shell.CreateShortCut(start_menu_lnk)
                s1.TargetPath = target_exe
                s1.Arguments = target_args
                s1.WorkingDirectory = APP_DIR
                s1.Description = "Contrôleur VLC Apple Style"
                if os.path.exists(icon_path):
                    s1.IconLocation = f"{icon_path},0"
                s1.Save()
            elif not should_start_menu and os.path.exists(start_menu_lnk):
                try: os.remove(start_menu_lnk)
                except: pass

            # 2. Raccourci Démarrage automatique
            should_startup = self._data.get("run_on_startup", False)
            if should_startup and not os.path.exists(startup_lnk):
                s2 = shell.CreateShortCut(startup_lnk)
                s2.TargetPath = target_exe
                s2.Arguments = target_args
                s2.WorkingDirectory = APP_DIR
                s2.Description = "Contrôleur VLC Apple Style"
                if os.path.exists(icon_path):
                    s2.IconLocation = f"{icon_path},0"
                s2.Save()
            elif not should_startup and os.path.exists(startup_lnk):
                try: os.remove(startup_lnk)
                except: pass
        except Exception as e:
            print(f"[Config] Erreur synchronisation raccourcis: {e}")

    def __getitem__(self, key):
        return self._data.get(key, DEFAULT_CONFIG.get(key))

    def __setitem__(self, key, value):
        self._data[key] = value

    def get(self, key, fallback=None):
        return self._data.get(key, fallback)


# ═══════════════════════════════════════════════════════════════
#  WIN32 HELPERS (DESKTOP PINNING)
# ═══════════════════════════════════════════════════════════════
def get_workerw():
    if not WIN32_AVAILABLE:
        return 0
    try:
        progman = win32gui.FindWindow("Progman", None)
        win32gui.SendMessageTimeout(progman, 0x052C, 0, 0, 0, 1000)
        workerw = [0]

        def enum_windows(hwnd, lParam):
            p = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
            if p != 0:
                workerw[0] = win32gui.FindWindowEx(0, hwnd, "WorkerW", None)
            return True

        win32gui.EnumWindows(enum_windows, 0)
        return workerw[0] if workerw[0] else progman
    except Exception:
        return 0


# ═══════════════════════════════════════════════════════════════
#  CLIENT VLC (HTTP API)
# ═══════════════════════════════════════════════════════════════
class VLCClient:
    def __init__(self, config: Config):
        self.config = config
        self._session = requests.Session()
        self._rebuild_session()

    def _rebuild_session(self):
        self._session.auth = ('', self.config["vlc_password"])
        self._session.headers.update({"Accept": "application/json"})

    def _base(self):
        return self.config["vlc_host"].rstrip('/')

    def get_status(self, timeout=1.0):
        url = f"{self._base()}/requests/status.json"
        r = self._session.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()

    def send_command(self, cmd, val=None, timeout=0.6):
        url = f"{self._base()}/requests/status.json"
        params = {"command": cmd}
        if val is not None:
            params["val"] = val
        try:
            self._session.get(url, params=params, timeout=timeout)
        except Exception:
            pass

    def get_art(self, timeout=2.0):
        url = f"{self._base()}/art"
        try:
            r = self._session.get(url, stream=True, timeout=timeout)
            if r.status_code == 200:
                return r.content
        except Exception:
            pass
        return None

    def reload_auth(self):
        self._rebuild_session()


# ═══════════════════════════════════════════════════════════════
#  CONTRÔLE DU VOLUME (PYCAW + FALLBACK)
# ═══════════════════════════════════════════════════════════════
class VolumeController:
    def __init__(self):
        self._interface = None
        if PYCAW_AVAILABLE:
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self._interface = cast(interface, POINTER(IAudioEndpointVolume))
            except Exception:
                self._interface = None

    def get_volume(self) -> float:
        if self._interface:
            try:
                return self._interface.GetMasterVolumeLevelScalar()
            except Exception:
                pass
        return 0.5

    def set_volume(self, level: float):
        level = max(0.0, min(1.0, level))
        if self._interface:
            try:
                self._interface.SetMasterVolumeLevelScalar(level, None)
                return True
            except Exception:
                pass
        if KEYBOARD_AVAILABLE:
            keyboard.send("volume up" if level > self.get_volume() else "volume down")
        return False

    def adjust(self, delta: float):
        curr = self.get_volume()
        new_v = max(0.0, min(1.0, curr + delta))
        self.set_volume(new_v)
        return new_v


# ═══════════════════════════════════════════════════════════════
#  FABRIQUE D'ICÔNES HAUTE DÉFINITION (CACHE PIL)
# ═══════════════════════════════════════════════════════════════
class IconFactory:
    CACHE = {}

    @classmethod
    def get(cls, name: str, color: str = "white", size: int = 20) -> ctk.CTkImage:
        key = (name, color, size)
        if key not in cls.CACHE:
            cls.CACHE[key] = cls._create(name, color, size)
        return cls.CACHE[key]

    @classmethod
    def _create(cls, name: str, color: str, size: int) -> ctk.CTkImage:
        scale = 3
        s = size * scale
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        if name == "play":
            d.polygon([(s*0.30, s*0.20), (s*0.30, s*0.80), (s*0.80, s*0.50)], fill=color)
        elif name == "pause":
            r = max(2, int(s*0.04))
            d.rounded_rectangle([s*0.26, s*0.20, s*0.42, s*0.80], radius=r, fill=color)
            d.rounded_rectangle([s*0.58, s*0.20, s*0.74, s*0.80], radius=r, fill=color)
        elif name == "prev":
            r = max(2, int(s*0.04))
            d.rounded_rectangle([s*0.18, s*0.22, s*0.28, s*0.78], radius=r, fill=color)
            d.polygon([(s*0.80, s*0.20), (s*0.80, s*0.80), (s*0.33, s*0.50)], fill=color)
        elif name == "next":
            r = max(2, int(s*0.04))
            d.polygon([(s*0.20, s*0.20), (s*0.20, s*0.80), (s*0.67, s*0.50)], fill=color)
            d.rounded_rectangle([s*0.72, s*0.22, s*0.82, s*0.78], radius=r, fill=color)
        elif name == "settings":
            cx, cy, r = s*0.5, s*0.5, s*0.26
            d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)
            d.ellipse([cx-r*0.5, cy-r*0.5, cx+r*0.5, cy+r*0.5], fill=(0,0,0,0))
            import math
            for i in range(8):
                rad = math.radians(i * 45)
                x1 = cx + math.cos(rad) * r * 0.95
                y1 = cy + math.sin(rad) * r * 0.95
                x2 = cx + math.cos(rad) * r * 1.40
                y2 = cy + math.sin(rad) * r * 1.40
                d.line([(x1, y1), (x2, y2)], fill=color, width=max(2, int(s*0.11)))

        img = img.resize((size*2, size*2), Image.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


# ═══════════════════════════════════════════════════════════════
#  GESTIONNAIRE DE COUVERTURES (LOCALES + CACHE MÉMOIRE)
# ═══════════════════════════════════════════════════════════════
class CoverManager:
    def __init__(self, size: int, corner_radius: int, config: Config):
        self.size = size
        self.corner_radius = corner_radius
        self.config = config
        self._cached_mask = None
        self._last_art_key = None
        self._last_art_image = None
        self.default = self._make_default()

    def _get_mask(self):
        if self._cached_mask is None:
            size = (self.size * 2, self.size * 2)
            mask = Image.new("L", size, 0)
            d = ImageDraw.Draw(mask)
            r = self.corner_radius * 2
            d.rounded_rectangle([0, 0, size[0]-1, size[1]-1], radius=r, fill=255)
            self._cached_mask = mask
        return self._cached_mask

    def _apply_mask(self, img: Image.Image) -> Image.Image:
        size = (self.size * 2, self.size * 2)
        img = img.resize(size, Image.LANCZOS).convert("RGBA")
        img.putalpha(self._get_mask())
        return img

    def _make_default(self) -> ctk.CTkImage:
        size = self.size * 2
        img = Image.new("RGBA", (size, size), (22, 22, 27, 255))
        d = ImageDraw.Draw(img)

        # Fond dégradé subtil Apple Glass
        for i in range(size // 2, 0, -2):
            alpha = int(35 * (1 - i / (size // 2)))
            d.ellipse([size // 2 - i, size // 2 - i, size // 2 + i, size // 2 + i], fill=(255, 107, 53, alpha))

        # Note de musique Apple
        c = (175, 175, 185, 230)
        s = size
        d.ellipse([s*0.30, s*0.56, s*0.48, s*0.72], fill=c)
        d.ellipse([s*0.56, s*0.48, s*0.74, s*0.64], fill=c)
        d.rectangle([s*0.43, s*0.26, s*0.49, s*0.64], fill=c)
        d.rectangle([s*0.69, s*0.18, s*0.75, s*0.56], fill=c)
        d.polygon([(s*0.43, s*0.26), (s*0.75, s*0.18), (s*0.75, s*0.26), (s*0.43, s*0.34)], fill=c)

        img = self._apply_mask(img)
        return ctk.CTkImage(light_image=img, dark_image=img, size=(self.size, self.size))

    def fetch_local(self, uri: str) -> ctk.CTkImage | None:
        if not uri or not uri.startswith("file:///"):
            return None
        try:
            local_path = urllib.parse.unquote(uri[8:])
            folder = Path(local_path).parent
            candidate_names = ["folder.jpg", "cover.jpg", "front.jpg", "folder.png", "cover.png", "albumart.jpg"]
            for name in candidate_names:
                p = folder / name
                if p.exists():
                    img = Image.open(p).convert("RGBA")
                    return self._process_pil(img, key=str(p))
        except Exception:
            pass
        return None

    def process(self, raw_bytes: bytes, key: str = None) -> ctk.CTkImage | None:
        if key and key == self._last_art_key and self._last_art_image:
            return self._last_art_image
        try:
            img = Image.open(BytesIO(raw_bytes)).convert("RGBA")
            res = self._process_pil(img, key=key)
            return res
        except Exception:
            return None

    def _process_pil(self, img: Image.Image, key: str = None) -> ctk.CTkImage:
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top  = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
        img = self._apply_mask(img)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(self.size, self.size))
        if key:
            self._last_art_key = key
            self._last_art_image = ctk_img
        return ctk_img


# ═══════════════════════════════════════════════════════════════
#  MARQUEE LABEL (OPTIMISÉ ÉNERGIE)
# ═══════════════════════════════════════════════════════════════
class MarqueeLabel(ctk.CTkLabel):
    MAX_VISIBLE = 30

    def __init__(self, master, **kwargs):
        self._full_text = kwargs.pop("text", "")
        super().__init__(master, text=self._full_text, **kwargs)
        self._offset = 0
        self._scroll_job = None
        self._enabled = True
        self._is_active = False

    def set_text(self, text: str, enabled: bool = True):
        self._full_text = text
        self._enabled = enabled
        self._offset = 0
        self.stop()
        if len(self._full_text) <= self.MAX_VISIBLE or not self._enabled:
            self.configure(text=self._full_text)
        else:
            self.resume()

    def resume(self):
        if not self._enabled or len(self._full_text) <= self.MAX_VISIBLE:
            return
        if self._is_active:
            return
        self._is_active = True
        self._step()

    def _step(self):
        if not self._is_active or not self._enabled:
            return
        padded = self._full_text + "   •   "
        chunk = (padded * 3)[self._offset : self._offset + self.MAX_VISIBLE]
        self.configure(text=chunk)
        self._offset = (self._offset + 1) % len(padded)
        self._scroll_job = self.after(140, self._step)

    def stop(self):
        self._is_active = False
        if self._scroll_job:
            try:
                self.after_cancel(self._scroll_job)
            except Exception:
                pass
            self._scroll_job = None


# ═══════════════════════════════════════════════════════════════
#  FENÊTRE DE PARAMÈTRES (APPLE STYLE MODAL)
# ═══════════════════════════════════════════════════════════════
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, config: Config, on_save):
        super().__init__(master)
        self.config = config
        self.on_save = on_save
        self.title("Paramètres - VLC Controller")
        self.geometry("480x670")
        self.attributes("-topmost", True)
        self.configure(fg_color=PALETTE["bg_frame"])
        self.overrideredirect(True)

        self._is_capturing = False

        # Contour de fenêtre Apple
        border = ctk.CTkFrame(self, fg_color=PALETTE["border"], corner_radius=22)
        border.pack(fill="both", expand=True, padx=2, pady=2)

        self.inner = ctk.CTkFrame(border, fg_color=PALETTE["bg_frame"], corner_radius=20)
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)

        self._build_ui()
        self._center_window(master)
        self.focus_force()

    def _center_window(self, parent):
        self.update_idletasks()
        w, h = 480, 670
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw // 2) - (w // 2)
        y = py + (ph // 2) - (h // 2)
        if y < 10:
            y = 20
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        p = self.inner
        p.grid_columnconfigure(0, weight=1)
        p.grid_columnconfigure(1, weight=1)

        # En-tête
        header = ctk.CTkFrame(p, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(16, 8))
        ctk.CTkLabel(header, text="⚙  Paramètres", font=FONT_TITLE, text_color=PALETTE["text_primary"]).pack(side="left", padx=20)

        btn_close = ctk.CTkButton(header, text="✕", width=32, height=32, corner_radius=16,
                                  fg_color="transparent", hover_color=PALETTE["bg_hover"],
                                  text_color=PALETTE["text_secondary"], font=("Segoe UI", 12, "bold"),
                                  command=self.destroy)
        btn_close.pack(side="right", padx=16)

        # Contenu défilable
        self.scroll = ctk.CTkScrollableFrame(p, fg_color="transparent")
        self.scroll.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=12, pady=0)
        p.grid_rowconfigure(1, weight=1)

        s = self.scroll
        s.grid_columnconfigure(0, weight=1)
        s.grid_columnconfigure(1, weight=1)

        # 1. Raccourci
        self._label(s, "Raccourci clavier :", 0)
        self.btn_hotkey = ctk.CTkButton(s, text=self.config["hotkey"], font=FONT_SMALL,
                                         fg_color=PALETTE["bg_card"], hover_color=PALETTE["bg_hover"],
                                         text_color=self.config["accent_color"], border_color=PALETTE["border"],
                                         border_width=1, width=150, height=30,
                                         command=self._start_capture_hotkey)
        self.btn_hotkey.grid(row=0, column=1, padx=10, pady=6, sticky="e")

        # 2. Couleurs Apple
        self._label(s, "Couleur d'accent :", 1)
        accent_box = ctk.CTkFrame(s, fg_color="transparent")
        accent_box.grid(row=1, column=1, padx=10, pady=6, sticky="e")

        self.current_accent = self.config["accent_color"]
        self.accent_buttons = []
        for hex_code, name in APPLE_ACCENTS:
            b = ctk.CTkButton(accent_box, text="", width=18, height=18, corner_radius=9,
                              fg_color=hex_code, hover_color=hex_code,
                              command=lambda c=hex_code: self._set_accent(c))
            b.pack(side="left", padx=2)
            self.accent_buttons.append((hex_code, b))

        # 3. Thème
        self._label(s, "Thème visuel :", 2)
        self.menu_theme = ctk.CTkOptionMenu(s, values=["Dark", "Light", "System"],
                                             fg_color=PALETTE["bg_card"], button_color=PALETTE["bg_hover"],
                                             dropdown_fg_color=PALETTE["bg_card"],
                                             width=150, height=28)
        self.menu_theme.set(self.config["theme"])
        self.menu_theme.grid(row=2, column=1, padx=10, pady=6, sticky="e")

        # 4. Opacité
        self._label(s, "Opacité maximale :", 3)
        self.sl_opacity = ctk.CTkSlider(s, from_=0.3, to=1.0, number_of_steps=70, width=150,
                                        button_color=self.config["accent_color"],
                                        progress_color=self.config["accent_color"],
                                        fg_color=PALETTE["slider_bg"])
        self.sl_opacity.set(self.config["max_opacity"])
        self.sl_opacity.grid(row=3, column=1, padx=10, pady=6, sticky="e")

        # 5. Délai disparition
        self._label(s, "Délai de disparition (ms) :", 4)
        self.sl_delay = ctk.CTkSlider(s, from_=1000, to=10000, number_of_steps=90, width=150,
                                      button_color=self.config["accent_color"],
                                      progress_color=self.config["accent_color"],
                                      fg_color=PALETTE["slider_bg"])
        self.sl_delay.set(self.config["hide_delay"])
        self.sl_delay.grid(row=4, column=1, padx=10, pady=6, sticky="e")

        # 6. Connexion VLC
        self._label(s, "Hôte VLC (Web HTTP) :", 5)
        self.entry_host = self._entry(s, self.config["vlc_host"], 5)

        self._label(s, "Mot de passe VLC :", 6)
        self.entry_pwd = self._entry(s, self.config["vlc_password"], 6, show="•")

        # 7. Switches modulaires
        switches_def = [
            ("show_cover", "Afficher la grande pochette"),
            ("show_progress", "Afficher la timeline (progression)"),
            ("show_controls", "Afficher les boutons de lecture"),
            ("show_speed", "Afficher le sélecteur de vitesse"),
            ("marquee_title", "Titre défilant (Marquee)"),
            ("auto_show_on_change", "Affichage auto sur pause / nouveau titre"),
            ("pin_to_desktop", "Fixer au bureau (toujours visible sur le bureau)"),
            ("start_menu_shortcut", "Ajouter au menu Démarrer de Windows"),
            ("run_on_startup", "Démarrer automatiquement avec Windows"),
        ]

        self._switches = {}
        r_start = 7
        for key, text in switches_def:
            sw = ctk.CTkSwitch(s, text=text, font=FONT_SMALL, text_color=PALETTE["text_secondary"],
                               button_color=self.config["accent_color"],
                               progress_color=self.config["accent_color"],
                               fg_color=PALETTE["bg_card"], width=46, height=22)
            if self.config[key]:
                sw.select()
            sw.grid(row=r_start, column=0, columnspan=2, padx=12, pady=7, sticky="w")
            self._switches[key] = sw
            r_start += 1

        # Bouton enregistrer
        self.btn_save = ctk.CTkButton(p, text="Enregistrer & Appliquer", font=FONT_BTN,
                                      fg_color=self.config["accent_color"], hover_color=self.config["accent_color"],
                                      height=36, corner_radius=12, command=self._save)
        self.btn_save.grid(row=2, column=0, columnspan=2, padx=20, pady=(12, 18), sticky="ew")

        self.bind("<KeyPress>", self._on_key_press)

    def _label(self, parent, text, row):
        ctk.CTkLabel(parent, text=text, font=FONT_SMALL, text_color=PALETTE["text_secondary"]).grid(
            row=row, column=0, padx=12, pady=6, sticky="w"
        )

    def _entry(self, parent, val, row, show=""):
        e = ctk.CTkEntry(parent, font=FONT_SMALL, width=150, height=28,
                         fg_color=PALETTE["bg_card"], border_color=PALETTE["border"], show=show)
        e.insert(0, val)
        e.grid(row=row, column=1, padx=10, pady=6, sticky="e")
        return e

    def _set_accent(self, color_hex):
        self.current_accent = color_hex
        self.btn_hotkey.configure(text_color=color_hex)
        self.sl_opacity.configure(button_color=color_hex, progress_color=color_hex)
        self.sl_delay.configure(button_color=color_hex, progress_color=color_hex)
        self.btn_save.configure(fg_color=color_hex, hover_color=color_hex)
        for sw in self._switches.values():
            sw.configure(button_color=color_hex, progress_color=color_hex)

    def _start_capture_hotkey(self):
        if not KEYBOARD_AVAILABLE:
            return
        self._is_capturing = True
        self.btn_hotkey.configure(text="Appuyez sur une touche...", fg_color=self.current_accent, text_color="white")
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

    def _on_key_press(self, event):
        if not self._is_capturing:
            return
        keys = []
        if event.state & 4:
            keys.append("ctrl")
        if event.state & 1:
            keys.append("shift")
        if event.state & 131072 or event.state & 8:
            keys.append("alt")

        sym = event.keysym.lower()
        ignore = ("control_l", "control_r", "shift_l", "shift_r", "alt_l", "alt_r", "iso_level3_shift")
        if sym not in ignore:
            keys.append(sym)
            hotkey = "+".join(keys)
            self.btn_hotkey.configure(text=hotkey, fg_color=PALETTE["bg_card"], text_color=self.current_accent)
            self.config["hotkey"] = hotkey
            self._is_capturing = False

    def _save(self):
        self.config["accent_color"] = self.current_accent
        self.config["theme"]        = self.menu_theme.get()
        self.config["max_opacity"]  = round(self.sl_opacity.get(), 2)
        self.config["hide_delay"]   = int(self.sl_delay.get())
        self.config["vlc_host"]     = self.entry_host.get().strip()
        self.config["vlc_password"] = self.entry_pwd.get()

        for key, sw in self._switches.items():
            self.config[key] = sw.get() == 1

        self.config.save()
        self.on_save()
        self.destroy()


# ═══════════════════════════════════════════════════════════════
#  OVERLAY PRINCIPAL (LIQUID & ULTRA-LIGHT)
# ═══════════════════════════════════════════════════════════════
class VLCOverlay(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.app_config  = Config()
        self.vlc_client  = VLCClient(self.app_config)
        self.cover_mgr   = CoverManager(size=COVER_SIZE, corner_radius=COVER_RADIUS, config=self.app_config)
        self.volume_ctrl = VolumeController()

        # État
        self.is_visible         = False
        self.is_pinned          = False
        self.hide_timer         = None
        self._fade_job          = None
        self._is_fading         = False
        self.is_dragging_slider = False
        self.is_dragging_window = False

        self.current_title      = ""
        self.current_artist     = ""
        self.last_state         = "stopped"
        self.last_rate          = 1.0
        self.duration           = 1

        # Vitesse
        self.speed_levels = ["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"]
        self.current_speed_idx = 2
        self.initial_rate_synced = False

        # Fenêtre transparente sans bordure
        self.overrideredirect(True)
        self.attributes("-alpha", 0.0)
        self._transparent_color = PALETTE["bg_root"]
        self.configure(bg=self._transparent_color)
        self.attributes("-transparentcolor", self._transparent_color)

        self._apply_theme()
        self._build_ui()
        self._setup_context_menu()
        self._apply_pinning()
        self._setup_hotkey()

        # Polling VLC thread
        self._stop_event = threading.Event()
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

        self._position_window()

        # Apparition douce au démarrage
        self.after(300, self._show_ui_threadsafe)

    def _apply_theme(self):
        ctk.set_appearance_mode(self.app_config["theme"])
        ctk.set_default_color_theme(self.app_config["color_theme"])
        PALETTE["accent"] = self.app_config["accent_color"]

    # ─────────────────────────────────────────────────────────
    #  CONSTRUCTION DE L'INTERFACE (APPLE LIQUID)
    # ─────────────────────────────────────────────────────────
    def _build_ui(self):
        # Ombre portée externe Apple
        self.shadow = ctk.CTkFrame(self, fg_color="#08080a", corner_radius=CORNER_R + 4, bg_color=self._transparent_color)
        self.shadow.place(x=3, y=6, relwidth=1.0, relheight=1.0)

        # Cadre Glassmorphism principal
        self.main_frame = ctk.CTkFrame(self, fg_color=PALETTE["bg_frame"], corner_radius=CORNER_R,
                                       border_width=1, border_color=PALETTE["border"], bg_color=self._transparent_color)
        self.main_frame.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        self.inner = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.inner.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=1.0)

        # 1. Pochette Agrandie (136x136)
        self.cover_label = ctk.CTkLabel(self.inner, text="", image=self.cover_mgr.default,
                                        width=COVER_SIZE, height=COVER_SIZE)
        self.cover_label.place(x=16, rely=0.5, anchor="w")

        # 2. Zone Droite (Informations + Contrôles)
        self.right = ctk.CTkFrame(self.inner, fg_color="transparent")

        # Bouton Paramètres discret (engrenage haut-droit)
        self.btn_settings = ctk.CTkButton(self.inner, text="", image=IconFactory.get("settings", PALETTE["text_dim"], 15),
                                          width=26, height=26, corner_radius=13,
                                          fg_color="transparent", hover_color=PALETTE["bg_hover"],
                                          command=self._open_settings)
        self.btn_settings.place(relx=1.0, x=-12, y=10, anchor="ne")

        # Titre (Marquee)
        self.lbl_title = MarqueeLabel(self.right, text="Recherche VLC...", font=FONT_TITLE,
                                      text_color=PALETTE["text_primary"], anchor="w", fg_color="transparent")
        self.lbl_title.place(x=0, y=16, relwidth=1.0)

        # Artiste
        self.lbl_artist = ctk.CTkLabel(self.right, text="En attente de musique...", font=FONT_ARTIST,
                                       text_color=PALETTE["text_secondary"], anchor="w")
        self.lbl_artist.place(x=0, y=44, relwidth=1.0)

        # 3. Timeline Interactive (Progression Seekable)
        self.progress_row = ctk.CTkFrame(self.right, fg_color="transparent", height=26)
        self.progress_row.place(x=0, y=74, relwidth=1.0)

        self.lbl_curr = ctk.CTkLabel(self.progress_row, text="0:00", font=FONT_TIME, text_color=PALETTE["text_dim"], width=34, anchor="e")
        self.lbl_curr.pack(side="left")

        self.slider = ctk.CTkSlider(self.progress_row, from_=0, to=100, height=12,
                                    button_color=PALETTE["accent"], button_hover_color=PALETTE["accent"],
                                    progress_color=PALETTE["accent"], fg_color=PALETTE["slider_bg"],
                                    command=self._on_slider_drag)
        self.slider.pack(side="left", fill="x", expand=True, padx=8)
        self.slider.bind("<Button-1>", self._on_slider_click)
        self.slider.bind("<ButtonRelease-1>", self._on_slider_release)

        self.lbl_total = ctk.CTkLabel(self.progress_row, text="0:00", font=FONT_TIME, text_color=PALETTE["text_dim"], width=34, anchor="w")
        self.lbl_total.pack(side="right")

        # 4. Contrôles de lecture & Sélecteur de vitesse
        self.ctrl_row = ctk.CTkFrame(self.right, fg_color="transparent", height=48)
        self.ctrl_row.place(x=0, y=110, relwidth=1.0)

        self.btn_prev = self._make_ctrl_btn("prev", 18, lambda: self.vlc_client.send_command("pl_previous"), 38, False)
        self.btn_pp   = self._make_ctrl_btn("play", 24, self._toggle_play, 46, True)
        self.btn_next = self._make_ctrl_btn("next", 18, lambda: self.vlc_client.send_command("pl_next"), 38, False)

        self.btn_prev.pack(side="left", padx=(0, 4))
        self.btn_pp.pack(side="left", padx=4)
        self.btn_next.pack(side="left", padx=4)

        # Sélecteur de vitesse Apple-style
        self.lbl_speed = ctk.CTkLabel(self.ctrl_row, text="1.0x", font=FONT_BTN,
                                      fg_color=PALETTE["bg_card"], text_color=PALETTE["text_primary"],
                                      corner_radius=12, width=64, height=30)
        self.lbl_speed.bind("<MouseWheel>", self._on_speed_scroll)
        self.lbl_speed.bind("<Button-1>", self._on_speed_click)
        self.lbl_speed.bind("<Enter>", lambda e: self.lbl_speed.configure(text_color=PALETTE["accent"]))
        self.lbl_speed.bind("<Leave>", lambda e: self.lbl_speed.configure(text_color=PALETTE["text_primary"]))
        self.lbl_speed.pack(side="right")

        self._apply_visibility()
        self._setup_drag(self.main_frame, self.inner, self.lbl_title, self.lbl_artist, self.cover_label)

    def _make_ctrl_btn(self, icon, sz, cmd, wh=38, filled=False):
        return ctk.CTkButton(self.ctrl_row, text="", image=IconFactory.get(icon, "white", sz),
                             width=wh, height=wh, corner_radius=wh // 2,
                             fg_color=PALETTE["accent"] if filled else "transparent",
                             hover_color=PALETTE["accent"] if filled else PALETTE["bg_hover"],
                             command=cmd)

    def _apply_visibility(self):
        show_c = self.app_config["show_cover"]
        if show_c:
            self.cover_label.place(x=16, rely=0.5, anchor="w")
            offset = 16 + COVER_SIZE + 16
        else:
            self.cover_label.place_forget()
            offset = 18

        self.right.configure(width=WIDGET_W - offset - 18)
        self.right.place(x=offset, y=0, relheight=1.0)

        if self.app_config["show_progress"]:
            self.progress_row.place(x=0, y=74, relwidth=1.0)
        else:
            self.progress_row.place_forget()

        if self.app_config["show_controls"]:
            self.ctrl_row.place(x=0, y=110, relwidth=1.0)
        else:
            self.ctrl_row.place_forget()

        if self.app_config["show_speed"]:
            self.lbl_speed.pack(side="right")
        else:
            self.lbl_speed.pack_forget()

        base_h = WIDGET_H
        if not self.app_config["show_progress"]:
            base_h -= 30
        if not self.app_config["show_controls"]:
            base_h -= 48
        self.geometry(f"{WIDGET_W}x{max(base_h, 96)}")

    def _position_window(self):
        self.update_idletasks()
        cx, cy = self.app_config["position_x"], self.app_config["position_y"]
        if cx < 0 or cy < 0:
            cx = (self.winfo_screenwidth() - WIDGET_W) // 2
            cy = 35
        self.geometry(f"+{cx}+{cy}")

    # ─────────────────────────────────────────────────────────
    #  GESTION DU Z-ORDER & MODE BUREAU
    # ─────────────────────────────────────────────────────────
    def _apply_pinning(self, temporary_topmost=False):
        if not WIN32_AVAILABLE:
            return
        hwnd = self.winfo_id()
        if self.app_config["pin_to_desktop"] and not temporary_topmost:
            workerw = get_workerw()
            if workerw:
                ctypes.windll.user32.SetParent(hwnd, workerw)
                self.is_pinned = True
                self.attributes("-alpha", self.app_config["max_opacity"])
                self.is_visible = True
        else:
            if self.is_pinned:
                ctypes.windll.user32.SetParent(hwnd, 0)
                self.is_pinned = False
            self.attributes("-topmost", True)

    # ─────────────────────────────────────────────────────────
    #  ANIMATIONS FLUIDES & PERFORMANCE (FADE IN/OUT SANS LAG)
    # ─────────────────────────────────────────────────────────
    def _cancel_animations(self):
        if self._fade_job:
            try:
                self.after_cancel(self._fade_job)
            except Exception:
                pass
            self._fade_job = None
        self._is_fading = False

    def _fade_in(self):
        if self.is_pinned:
            return
        self._is_fading = True
        alpha = self.attributes("-alpha")
        target = self.app_config["max_opacity"]
        if alpha < target:
            self.attributes("-alpha", min(alpha + 0.12, target))
            self._fade_job = self.after(14, self._fade_in)
        else:
            self._is_fading = False

    def _fade_out(self):
        if self.is_pinned:
            return
        self._is_fading = True
        alpha = self.attributes("-alpha")
        if alpha > 0.05:
            self.attributes("-alpha", alpha * 0.78)
            self._fade_job = self.after(14, self._fade_out)
        else:
            self.attributes("-alpha", 0.0)
            self.withdraw()
            self.is_visible = False
            self._is_fading = False
            self.lbl_title.stop()  # Stoppe le marquee en veille pour économiser le CPU
            self._save_pos()

    def show_ui(self, force_topmost=False):
        self._cancel_animations()
        self.deiconify()

        if self.app_config["pin_to_desktop"]:
            if force_topmost:
                self._apply_pinning(temporary_topmost=True)
            else:
                self._apply_pinning(temporary_topmost=False)
                self.attributes("-alpha", self.app_config["max_opacity"])
                self.is_visible = True
                self.lbl_title.resume()
                return

        self.lift()
        self.attributes("-topmost", True)
        self._reset_timer()

        if not self.is_visible:
            self.is_visible = True
            self._fade_in()
        else:
            self.attributes("-alpha", self.app_config["max_opacity"])

        self.lbl_title.resume()

    def _show_ui_threadsafe(self):
        self.after(0, lambda: self.show_ui(force_topmost=True))

    def _reset_timer(self):
        if self.hide_timer:
            try:
                self.after_cancel(self.hide_timer)
            except Exception:
                pass
            self.hide_timer = None

        if not self.app_config["pin_to_desktop"]:
            self.hide_timer = self.after(self.app_config["hide_delay"], self._try_fade_out)
        else:
            self.hide_timer = self.after(self.app_config["hide_delay"], lambda: self._apply_pinning(temporary_topmost=False))

    def _try_fade_out(self):
        if self.is_pinned or self.is_dragging_window or self.is_dragging_slider:
            return
        try:
            x, y = self.winfo_pointerxy()
            w = self.winfo_containing(x, y)
            if w and str(w).startswith(str(self)):
                return
        except Exception:
            pass
        self._cancel_animations()
        self._fade_out()

    def _on_mouse_enter(self, e):
        self._cancel_animations()
        if self.hide_timer:
            try:
                self.after_cancel(self.hide_timer)
            except Exception:
                pass
            self.hide_timer = None
        self.attributes("-alpha", self.app_config["max_opacity"])
        self.is_visible = True
        self.lbl_title.resume()

    def _on_mouse_leave(self, e):
        self._reset_timer()

    # ─────────────────────────────────────────────────────────
    #  INTERACTIONS SOURIS & DÉPLACEMENT
    # ─────────────────────────────────────────────────────────
    def _setup_drag(self, *widgets):
        for w in widgets:
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._do_drag)
            w.bind("<ButtonRelease-1>", self._end_drag)
            w.bind("<MouseWheel>", self._on_scroll)
        self.bind("<Enter>", self._on_mouse_enter)
        self.bind("<Leave>", self._on_mouse_leave)

    def _start_drag(self, e):
        self.is_dragging_window = True
        self._drag_start_x = e.x
        self._drag_start_y = e.y
        if self.hide_timer:
            try:
                self.after_cancel(self.hide_timer)
            except Exception:
                pass

    def _do_drag(self, e):
        if self.is_pinned:
            return
        dx = e.x - self._drag_start_x
        dy = e.y - self._drag_start_y
        self.geometry(f"+{self.winfo_x() + dx}+{self.winfo_y() + dy}")

    def _end_drag(self, e):
        self.is_dragging_window = False
        self._reset_timer()

    def _save_pos(self):
        if self.is_pinned:
            return
        try:
            geo = self.geometry().split("+")
            self.app_config["position_x"] = int(geo[1])
            self.app_config["position_y"] = int(geo[2])
            self.app_config.save()
        except Exception:
            pass

    def _on_scroll(self, e):
        delta = 0.05 if e.delta > 0 else -0.05
        vol = self.volume_ctrl.adjust(delta)
        pct = int(vol * 100)
        self.lbl_artist.configure(text=f"🔊 Volume : {pct}%", text_color=PALETTE["accent"])
        self.after(1200, lambda: self.lbl_artist.configure(
            text=self.current_artist[:36] if self.current_artist else "En attente...",
            text_color=PALETTE["text_secondary"]
        ))

    # ─────────────────────────────────────────────────────────
    #  TIMELINE INTERACTIVE (SEEKABLE)
    # ─────────────────────────────────────────────────────────
    def _on_slider_click(self, e):
        self.is_dragging_slider = True
        if self.hide_timer:
            try:
                self.after_cancel(self.hide_timer)
            except Exception:
                pass
        # Calcul direct du pourcentage au clic
        width = self.slider.winfo_width()
        if width > 0:
            pct = max(0, min(100, (e.x / width) * 100))
            self.slider.set(pct)
            self._on_slider_drag(pct)

    def _on_slider_drag(self, val):
        self.is_dragging_slider = True
        target_s = int((val / 100.0) * self.duration)
        self.lbl_curr.configure(text=self._fmt(target_s))

    def _on_slider_release(self, e):
        val = self.slider.get()
        threading.Thread(target=lambda: self.vlc_client.send_command("seek", f"{val:.1f}%"), daemon=True).start()
        self.after(350, lambda: setattr(self, "is_dragging_slider", False))
        self._reset_timer()

    # ─────────────────────────────────────────────────────────
    #  CONTRÔLES DE LECTURE & VITESSE APPLE
    # ─────────────────────────────────────────────────────────
    def _toggle_play(self):
        threading.Thread(target=lambda: self.vlc_client.send_command("pl_pause"), daemon=True).start()
        self._reset_timer()

    def _on_speed_scroll(self, e):
        if e.delta > 0 and self.current_speed_idx < len(self.speed_levels) - 1:
            self.current_speed_idx += 1
        elif e.delta < 0 and self.current_speed_idx > 0:
            self.current_speed_idx -= 1
        self._set_speed_from_idx()

    def _on_speed_click(self, e):
        self.current_speed_idx = (self.current_speed_idx + 1) % len(self.speed_levels)
        self._set_speed_from_idx()

    def _set_speed_from_idx(self):
        val_str = self.speed_levels[self.current_speed_idx]
        self.lbl_speed.configure(text=val_str, text_color=PALETTE["accent"])
        self.after(300, lambda: self.lbl_speed.configure(text_color=PALETTE["text_primary"]))
        val = val_str.replace("x", "")
        threading.Thread(target=lambda: self.vlc_client.send_command("rate", val), daemon=True).start()

    # ─────────────────────────────────────────────────────────
    #  BOUCLE DE SURVEILLANCE VLC (POLLING ULTRA-LÉGER)
    # ─────────────────────────────────────────────────────────
    def _poll_loop(self):
        failures = 0
        while not self._stop_event.is_set():
            try:
                data = self.vlc_client.get_status()
                failures = 0
                self.after(0, lambda d=data: self._update_ui(d))

                # Mode actif (fenêtre affichée) -> 0.8s
                # Mode veille (fenêtre masquée) -> 2.0s pour économiser le CPU
                sleep_time = 0.8 if self.is_visible or self.is_pinned else 2.0
                self._stop_event.wait(sleep_time)
            except Exception:
                failures += 1
                if failures == 1:
                    self.after(0, self._set_disconnected)
                # VLC éteint ou inaccessible -> back-off à 3.0s
                self._stop_event.wait(3.0)

    def _set_disconnected(self):
        self.lbl_title.set_text("VLC non détecté", False)
        self.lbl_artist.configure(text="En attente de connexion...", text_color=PALETTE["text_dim"])
        self.cover_label.configure(image=self.cover_mgr.default)
        self.current_title = ""
        self.slider.set(0)
        self.btn_pp.configure(image=IconFactory.get("play", "white", 24))

    def _update_ui(self, data: dict):
        info   = data.get("information", {})
        meta   = info.get("category", {}).get("meta", {})
        title  = meta.get("title", meta.get("filename", "Lecture en cours"))
        artist = meta.get("artist", "")
        length = data.get("length", 1) or 1
        tpos   = data.get("time", 0)
        state  = data.get("state", "stopped")
        rate   = data.get("rate", 1.0)
        uri    = info.get("category", {}).get("info", {}).get("uri", "")

        self.duration = length

        # 1. Détection de la vitesse dès le premier statut
        if not self.initial_rate_synced or abs(rate - self.last_rate) > 0.04:
            self.last_rate = rate
            self.initial_rate_synced = True
            try:
                closest_idx = min(
                    range(len(self.speed_levels)),
                    key=lambda i: abs(float(self.speed_levels[i].replace("x", "")) - rate)
                )
                self.current_speed_idx = closest_idx
                self.lbl_speed.configure(text=self.speed_levels[self.current_speed_idx])
            except Exception:
                pass

        # 2. Changement de morceau
        if title != self.current_title and title not in ("", "Lecture en cours"):
            self.current_title = title
            self.current_artist = artist
            self.lbl_title.set_text(title, self.app_config["marquee_title"])
            self.lbl_artist.configure(
                text=artist[:36] if artist else "Artiste inconnu",
                text_color=PALETTE["text_secondary"]
            )
            # Récupération de la pochette
            threading.Thread(target=self._fetch_cover, args=(uri, title), daemon=True).start()

            if self.app_config["auto_show_on_change"]:
                self.show_ui(force_topmost=True)

        # 3. Changement d'état (Play / Pause)
        if state != self.last_state:
            self.last_state = state
            self.btn_pp.configure(image=IconFactory.get("pause" if state == "playing" else "play", "white", 24))
            if state in ("playing", "paused") and self.app_config["auto_show_on_change"]:
                self.show_ui(force_topmost=True)

        # 4. Progression temporelle (mise à jour seulement si visible pour économiser le CPU)
        if (self.is_visible or self.is_pinned) and not self.is_dragging_slider:
            self.lbl_curr.configure(text=self._fmt(tpos))
            self.lbl_total.configure(text=self._fmt(length))
            if length > 0:
                self.slider.set((tpos / length) * 100)

    def _fetch_cover(self, uri, title):
        # 1. Vérifier si une image de dossier existe
        img = self.cover_mgr.fetch_local(uri)
        # 2. Sinon interroger l'API /art de VLC
        if not img:
            raw = self.vlc_client.get_art()
            if raw:
                img = self.cover_mgr.process(raw, key=title)

        final_img = img if img else self.cover_mgr.default
        self.after(0, lambda: self.cover_label.configure(image=final_img))

    def _fmt(self, s):
        s = int(s)
        return f"{s // 60}:{s % 60:02d}"

    # ─────────────────────────────────────────────────────────
    #  HOTKEY GLOBAL (SÉCURISÉ)
    # ─────────────────────────────────────────────────────────
    def _setup_hotkey(self):
        if not KEYBOARD_AVAILABLE:
            return
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        try:
            keyboard.add_hotkey(self.app_config["hotkey"], self._show_ui_threadsafe)
        except Exception as e:
            print(f"[Hotkey] Erreur enregistrement: {e}")

    # ─────────────────────────────────────────────────────────
    #  MENU CONTEXTUEL (CLIC DROIT SUR TOUTE L'INTERFACE)
    # ─────────────────────────────────────────────────────────
    def _setup_context_menu(self):
        self.ctx = tk.Menu(self, tearoff=0, bg=PALETTE["bg_card"], fg=PALETTE["text_primary"],
                           activebackground=PALETTE["accent"], activeforeground="white",
                           bd=1, relief="solid", font=("Segoe UI", 10))
        self.ctx.add_command(label="⚙  Paramètres...", command=self._open_settings)
        self.ctx.add_separator()
        self.ctx.add_command(label="⏯  Lecture / Pause", command=self._toggle_play)
        self.ctx.add_command(label="⏭  Piste suivante", command=lambda: self.vlc_client.send_command("pl_next"))
        self.ctx.add_command(label="⏮  Piste précédente", command=lambda: self.vlc_client.send_command("pl_previous"))
        self.ctx.add_separator()
        self.ctx.add_command(label="❌  Quitter", command=self._quit)

        def _show_menu(e):
            try:
                self.ctx.tk_popup(e.x_root, e.y_root)
            finally:
                self.ctx.grab_release()

        self._bind_right_click(self, _show_menu)

    def _bind_right_click(self, widget, handler):
        widget.bind("<Button-3>", handler)
        for child in widget.winfo_children():
            self._bind_right_click(child, handler)

    def _open_settings(self):
        SettingsWindow(self, self.app_config, self._on_settings_saved)

    def _on_settings_saved(self):
        self._apply_theme()
        self.cover_mgr = CoverManager(size=COVER_SIZE, corner_radius=COVER_RADIUS, config=self.app_config)
        self.vlc_client.reload_auth()
        self._setup_hotkey()
        self._apply_visibility()
        self._apply_pinning()
        self.show_ui(force_topmost=True)

    def _quit(self):
        self._stop_event.set()
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        if self.is_pinned and WIN32_AVAILABLE:
            ctypes.windll.user32.SetParent(self.winfo_id(), 0)
        self.destroy()


# ═══════════════════════════════════════════════════════════════
#  LANCEMENT PRINCIPAL
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = VLCOverlay()
    app.mainloop()