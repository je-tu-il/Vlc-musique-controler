#!/usr/bin/env python3
"""
VLC Overlay Controller — Contrôleur flottant & discret pour VLC
Une interface overlay élégante pour piloter VLC (lecture, progression, vitesse, volume) sans encombrer l'écran.
"""

import time
import threading
import requests
import customtkinter as ctk
import keyboard
import subprocess
import os
import sys
from PIL import Image, ImageDraw
from io import BytesIO

# --- CONFIGURATION PAR DÉFAUT ---
VLC_HOST = "http://127.0.0.1:8080/requests/status.json"
VLC_ART_ROOT = "http://127.0.0.1:8080/art"
VLC_PASSWORD = "vlc"
HOTKEY = "alt+é"
AUTO_HIDE_DELAY = 3000
MAX_OPACITY = 0.95

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")


class VLCOverlay(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Fenêtre sans bordures & transparente ---
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)

        self.config(bg="#000001")
        try:
            self.attributes("-transparentcolor", "#000001")
        except Exception:
            pass

        # --- Positionnement ---
        self.update_idletasks()
        width = 500
        height = 170
        screen_width = self.winfo_screenwidth()
        x_pos = (screen_width - width) // 2
        y_pos = 10
        self.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

        # --- Variables ---
        self.auth = ("", VLC_PASSWORD)
        self.hide_timer = None
        self.is_dragging_slider = False
        self.current_title = ""
        self.last_state = "stopped"
        self.duration = 1
        self.is_visible = False
        self.first_connection_made = False

        # --- Icônes vectorielles dynamiques ---
        self.icon_play = self.create_icon("play", "white", 24)
        self.icon_pause = self.create_icon("pause", "white", 24)
        self.icon_prev = self.create_icon("prev", "#dddddd", 20)
        self.icon_next = self.create_icon("next", "#dddddd", 20)

        # --- Structure UI ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color="#1a1a1a", bg_color="#000001")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. Zone Info (Haut)
        self.info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.info_frame.pack(fill="x", padx=15, pady=(15, 5))

        # A. Pochette
        self.cover_label = ctk.CTkLabel(
            self.info_frame, text="🎵", width=55, height=55, fg_color="#333", corner_radius=10, font=("Arial", 24)
        )
        self.cover_label.pack(side="left")

        # B. Menu Vitesse
        self.speed_var = ctk.StringVar(value="1.0")
        self.speed_menu = ctk.CTkOptionMenu(
            self.info_frame,
            values=["0.5", "1.0", "1.25", "1.5", "1.7", "2.0"],
            command=self.change_speed,
            width=65,
            height=24,
            variable=self.speed_var,
            fg_color="#333",
            button_color="#444",
            button_hover_color="#555",
        )
        self.speed_menu.pack(side="right", padx=(10, 0), anchor="c")

        # C. Titre & Artiste
        self.text_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.text_frame.pack(side="left", fill="x", expand=True, padx=12)

        self.lbl_title = ctk.CTkLabel(
            self.text_frame, text="En attente de VLC...", font=("Segoe UI", 15, "bold"), anchor="w"
        )
        self.lbl_title.pack(fill="x")

        self.lbl_artist = ctk.CTkLabel(
            self.text_frame, text="Activer l'interface web dans VLC (mdp: vlc)", font=("Segoe UI", 11), text_color="#aaa", anchor="w"
        )
        self.lbl_artist.pack(fill="x")

        # 2. Barre de progression & Temps
        self.slider = ctk.CTkSlider(
            self.main_frame, from_=0, to=100, command=self.on_slider_drag, height=16, progress_color="#1DB954"
        )
        self.slider.pack(fill="x", padx=20, pady=5)
        self.slider.bind("<ButtonRelease-1>", self.on_slider_release)
        self.slider.bind("<Button-1>", self.on_slider_click)

        self.time_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.time_frame.pack(fill="x", padx=20)
        self.lbl_time_curr = ctk.CTkLabel(self.time_frame, text="00:00", font=("Consolas", 10), text_color="#888")
        self.lbl_time_curr.pack(side="left")
        self.lbl_time_total = ctk.CTkLabel(self.time_frame, text="00:00", font=("Consolas", 10), text_color="#888")
        self.lbl_time_total.pack(side="right")

        # 3. Boutons Contrôles
        self.ctrl_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.ctrl_frame.pack(pady=(5, 15))

        self.btn_prev = ctk.CTkButton(
            self.ctrl_frame,
            text="",
            image=self.icon_prev,
            width=45,
            height=32,
            corner_radius=16,
            fg_color="#444",
            hover_color="#555",
            command=lambda: self.send("pl_previous"),
        )
        self.btn_prev.pack(side="left", padx=12)

        self.btn_pp = ctk.CTkButton(
            self.ctrl_frame,
            text="",
            image=self.icon_play,
            width=60,
            height=38,
            corner_radius=19,
            fg_color="#1DB954",
            hover_color="#1ed760",
            command=lambda: self.send("pl_pause"),
        )
        self.btn_pp.pack(side="left", padx=12)

        self.btn_next = ctk.CTkButton(
            self.ctrl_frame,
            text="",
            image=self.icon_next,
            width=45,
            height=32,
            corner_radius=16,
            fg_color="#444",
            hover_color="#555",
            command=lambda: self.send("pl_next"),
        )
        self.btn_next.pack(side="left", padx=12)

        # Bindings Déplacement et Molette (Volume)
        widgets_to_bind = [
            self.main_frame,
            self.info_frame,
            self.text_frame,
            self.lbl_title,
            self.lbl_artist,
            self.ctrl_frame,
            self.time_frame,
        ]

        for w in widgets_to_bind:
            w.bind("<Button-1>", self.start_move)
            w.bind("<B1-Motion>", self.do_move)
            w.bind("<MouseWheel>", self.on_scroll)

        self.bind("<Enter>", self.on_mouse_enter)
        self.bind("<Leave>", self.on_mouse_leave)

        # Worker de détection
        try:
            keyboard.add_hotkey(HOTKEY, self.show_ui)
        except Exception:
            pass

        self.monitor_thread = threading.Thread(target=self.poll_vlc, daemon=True)
        self.monitor_thread.start()
        self.reset_timer()

    def create_icon(self, name, color, size):
        img = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        if name == "play":
            draw.polygon([(size * 0.7, size * 0.4), (size * 1.5, size), (size * 0.7, size * 1.6)], fill=color)
        elif name == "pause":
            draw.rectangle([size * 0.6, size * 0.4, size * 0.85, size * 1.6], fill=color)
            draw.rectangle([size * 1.15, size * 0.4, size * 1.4, size * 1.6], fill=color)
        elif name == "prev":
            draw.rectangle([size * 0.4, size * 0.5, size * 0.6, size * 1.5], fill=color)
            draw.polygon([(size * 1.5, size * 0.5), (size * 0.7, size), (size * 1.5, size * 1.5)], fill=color)
        elif name == "next":
            draw.rectangle([size * 1.4, size * 0.5, size * 1.6, size * 1.5], fill=color)
            draw.polygon([(size * 0.5, size * 0.5), (size * 1.3, size), (size * 0.5, size * 1.5)], fill=color)
        return ctk.CTkImage(img, size=(size, size))

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        new_x = self.winfo_x() + deltax
        new_y = self.winfo_y() + deltay
        self.geometry(f"+{new_x}+{new_y}")

    def on_mouse_enter(self, event):
        if self.hide_timer:
            self.after_cancel(self.hide_timer)
            self.hide_timer = None

    def on_mouse_leave(self, event):
        self.reset_timer()

    def on_scroll(self, event):
        self.show_ui()
        step = 10 if event.delta > 0 else -10
        self.send(f"volume&val={'+' if step > 0 else ''}{step}")

    def show_ui(self):
        self.is_visible = True
        self.attributes("-alpha", MAX_OPACITY)
        self.reset_timer()

    def hide_ui(self):
        self.is_visible = False
        self.attributes("-alpha", 0.0)

    def reset_timer(self):
        if self.hide_timer:
            self.after_cancel(self.hide_timer)
        self.hide_timer = self.after(AUTO_HIDE_DELAY, self.hide_ui)

    def send(self, command):
        self.reset_timer()
        threading.Thread(
            target=lambda: requests.get(f"{VLC_HOST}?command={command}", auth=self.auth, timeout=1),
            daemon=True,
        ).start()

    def change_speed(self, value):
        self.send(f"rate&val={value}")

    def on_slider_drag(self, value):
        self.is_dragging_slider = True
        self.reset_timer()

    def on_slider_click(self, event):
        self.is_dragging_slider = True

    def on_slider_release(self, event):
        target_val = self.slider.get()
        self.send(f"seek&val={int(target_val)}%")
        self.is_dragging_slider = False

    def poll_vlc(self):
        last_art_url = None
        while True:
            try:
                r = requests.get(VLC_HOST, auth=self.auth, timeout=1)
                if r.status_code == 200:
                    data = r.json()
                    info = data.get("information", {}).get("category", {}).get("meta", {})
                    title = info.get("title", data.get("information", {}).get("title", "Aucun média"))
                    artist = info.get("artist", "")
                    state = data.get("state", "stopped")
                    time_pos = data.get("time", 0)
                    length = data.get("length", 1)
                    rate = str(data.get("rate", 1.0))

                    if not self.first_connection_made:
                        self.first_connection_made = True
                        self.after(0, self.show_ui)

                    if title != self.current_title or state != self.last_state:
                        self.current_title = title
                        self.last_state = state
                        if state == "playing":
                            self.after(0, self.show_ui)

                    art_url = info.get("artwork_url", None)
                    if art_url and art_url != last_art_url:
                        last_art_url = art_url
                        threading.Thread(target=self.fetch_cover, daemon=True).start()
                    elif not art_url:
                        self.after(0, self.reset_cover)

                    self.after(0, lambda: self.update_ui(title, artist, state, time_pos, length, rate))
            except Exception:
                pass
            time.sleep(0.5)

    def fetch_cover(self):
        try:
            r = requests.get(VLC_ART_ROOT, auth=self.auth, timeout=2)
            if r.status_code == 200:
                raw_img = Image.open(BytesIO(r.content))
                img = ctk.CTkImage(raw_img, size=(55, 55))
                self.after(0, lambda: self.cover_label.configure(image=img, text=""))
        except Exception:
            pass

    def reset_cover(self):
        self.cover_label.configure(image="", text="🎵")

    def update_ui(self, title, artist, state, time_pos, length, rate):
        if len(title) > 35:
            title = title[:32] + "..."
        self.lbl_title.configure(text=title)
        self.lbl_artist.configure(text=artist)

        if not self.is_dragging_slider and length > 0:
            self.slider.set((time_pos / length) * 100)
            self.lbl_time_curr.configure(text=self.fmt_time(time_pos))
            self.lbl_time_total.configure(text=self.fmt_time(length))

        if state == "playing":
            self.btn_pp.configure(image=self.icon_pause)
        else:
            self.btn_pp.configure(image=self.icon_play)

        if rate in self.speed_menu._values:
            self.speed_var.set(rate)

    def fmt_time(self, s):
        m, s = divmod(int(s), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def main():
    app = VLCOverlay()
    app.mainloop()


if __name__ == "__main__":
    main()
