import time
import threading
import requests
import customtkinter as ctk
import keyboard
import subprocess
import os
from PIL import Image, ImageDraw
from io import BytesIO

# --- CONFIGURATION ---
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

        # --- Fenêtre ---
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.0)
        
        self.config(bg='#000001')
        self.attributes('-transparentcolor', '#000001')

        # --- Positionnement ---
        self.update_idletasks() 
        width = 500
        height = 170
        screen_width = self.winfo_screenwidth()
        x_pos = (screen_width - width) // 2
        y_pos = 10 
        self.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

        # --- Variables ---
        self.auth = ('', VLC_PASSWORD)
        self.hide_timer = None
        self.is_dragging_slider = False
        self.current_title = ""
        self.last_state = "stopped"
        self.duration = 1
        self.is_visible = False
        self.first_connection_made = False
        
        # --- Icônes ---
        self.icon_play = self.create_icon("play", "white", 24)
        self.icon_prev = self.create_icon("prev", "#dddddd", 20)
        self.icon_next = self.create_icon("next", "#dddddd", 20)

        # --- UI Structure ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color="#1a1a1a", bg_color="#000001")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 1. Zone Info (Haut)
        self.info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.info_frame.pack(fill="x", padx=15, pady=(15, 5))

        # A. Cover (Gauche) - Plus de curseur main ni de binding
        self.cover_label = ctk.CTkLabel(self.info_frame, text="🎵", width=55, height=55, fg_color="#333", corner_radius=10, font=("Arial", 24))
        self.cover_label.pack(side="left")

        # B. Menu Vitesse (Droite)
        self.speed_var = ctk.StringVar(value="1.0")
        self.speed_menu = ctk.CTkOptionMenu(self.info_frame, values=["0.5", "1.0", "1.25", "1.5", "1.7", "2.0"],
                                            command=self.change_speed, width=65, height=24, variable=self.speed_var,
                                            fg_color="#333", button_color="#444", button_hover_color="#555")
        self.speed_menu.pack(side="right", padx=(10, 0), anchor="c")

        # C. Texte
        self.text_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.text_frame.pack(side="left", fill="x", expand=True, padx=12)

        self.lbl_title = ctk.CTkLabel(self.text_frame, text="Recherche VLC...", font=("Segoe UI", 15, "bold"), anchor="w")
        self.lbl_title.pack(fill="x")

        self.lbl_artist = ctk.CTkLabel(self.text_frame, text="", font=("Segoe UI", 12), text_color="#aaa", anchor="w")
        self.lbl_artist.pack(fill="x")

        # 2. Slider & Temps (Milieu)
        self.slider = ctk.CTkSlider(self.main_frame, from_=0, to=100, command=self.on_slider_drag, height=16, progress_color="#1DB954")
        self.slider.pack(fill="x", padx=20, pady=5)
        self.slider.bind("<ButtonRelease-1>", self.on_slider_release)
        self.slider.bind("<Button-1>", self.on_slider_click)

        self.time_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.time_frame.pack(fill="x", padx=20)
        self.lbl_time_curr = ctk.CTkLabel(self.time_frame, text="00:00", font=("Consolas", 10), text_color="#888")
        self.lbl_time_curr.pack(side="left")
        self.lbl_time_total = ctk.CTkLabel(self.time_frame, text="00:00", font=("Consolas", 10), text_color="#888")
        self.lbl_time_total.pack(side="right")

        # 3. Contrôles (Bas)
        self.ctrl_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.ctrl_frame.pack(pady=(5, 15))

        self.btn_prev = ctk.CTkButton(self.ctrl_frame, text="", image=self.icon_prev, width=45, height=32, corner_radius=16, 
                                      fg_color="#444", hover_color="#555", 
                                      command=lambda: self.send("pl_previous"))
        self.btn_prev.pack(side="left", padx=12)

        self.btn_pp = ctk.CTkButton(self.ctrl_frame, text="", image=self.icon_play, width=60, height=38, corner_radius=19, 
                                    fg_color="#1DB954", hover_color="#1ed760", 
                                    command=lambda: self.send("pl_pause"))
        self.btn_pp.pack(side="left", padx=12)

        self.btn_next = ctk.CTkButton(self.ctrl_frame, text="", image=self.icon_next, width=45, height=32, corner_radius=16, 
                                      fg_color="#444", hover_color="#555", 
                                      command=lambda: self.send("pl_next"))
        self.btn_next.pack(side="left", padx=12)

        # --- BINDINGS ---
        widgets_to_bind = [self.main_frame, self.info_frame, self.text_frame, self.lbl_title, 
                           self.lbl_artist, self.ctrl_frame, self.time_frame]
        
        for w in widgets_to_bind:
            w.bind("<Button-1>", self.start_move)
            w.bind("<B1-Motion>", self.do_move)
            w.bind("<MouseWheel>", self.on_scroll)

        self.bind("<Enter>", self.on_mouse_enter)
        self.bind("<Leave>", self.on_mouse_leave)

        # Workers
        keyboard.add_hotkey(HOTKEY, self.show_ui)
        self.monitor_thread = threading.Thread(target=self.poll_vlc, daemon=True)
        self.monitor_thread.start()
        self.reset_timer()

    # --- GENERATEUR ICONES ---
    def create_icon(self, name, color, size):
        img = Image.new("RGBA", (size*2, size*2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        w, h = size*2, size*2
        
        if name == "play":
            draw.polygon([(w*0.35, h*0.2), (w*0.35, h*0.8), (w*0.8, h*0.5)], fill=color)
        elif name == "prev":
            draw.rectangle([w*0.2, h*0.25, w*0.3, h*0.75], fill=color)
            draw.polygon([(w*0.8, h*0.2), (w*0.8, h*0.8), (w*0.35, h*0.5)], fill=color)
        elif name == "next":
            draw.polygon([(w*0.2, h*0.2), (w*0.2, h*0.8), (w*0.65, h*0.5)], fill=color)
            draw.rectangle([w*0.7, h*0.25, w*0.8, h*0.75], fill=color)

        return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))

    # --- GESTION SOURIS ---
    def on_mouse_enter(self, event):
        if self.hide_timer:
            self.after_cancel(self.hide_timer)
            self.hide_timer = None

    def on_mouse_leave(self, event):
        try:
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
            if widget and str(widget).startswith(str(self)): return
        except: pass
        self.reset_timer()

    # --- LOGIQUE VLC ---
    def poll_vlc(self, force_refresh=False):
        while True:
            try:
                resp = requests.get(VLC_HOST, auth=self.auth, timeout=2)
                data = resp.json()
                
                if not self.first_connection_made:
                    self.first_connection_made = True
                    self.show_ui()

                info = data.get('information', {})
                meta = info.get('category', {}).get('meta', {})
                title = meta.get('title', meta.get('filename', 'Lecture en cours'))
                artist = meta.get('artist', '')
                length = data.get('length', 1)
                time_pos = data.get('time', 0)
                state = data.get('state', 'stopped')
                
                self.duration = length if length > 0 else 1
                
                # Update Info
                if title != self.current_title and title != "Lecture en cours":
                    self.current_title = title
                    
                    disp_title = title
                    if len(disp_title) > 30: disp_title = disp_title[:27] + "..."
                    self.lbl_title.configure(text=disp_title)
                    
                    disp_artist = artist
                    if len(disp_artist) > 35: disp_artist = disp_artist[:32] + "..."
                    self.lbl_artist.configure(text=disp_artist)
                    
                    art_url = meta.get('artwork_url', '')
                    if art_url: self.update_cover(VLC_ART_ROOT)
                    else: self.cover_label.configure(image=None, text="🎵")
                        
                    self.show_ui()

                if state != self.last_state:
                    if state in ["paused", "playing"]:
                        self.show_ui()
                    self.last_state = state

                if not self.is_dragging_slider:
                    self.lbl_time_curr.configure(text=self.fmt_time(time_pos))
                    self.lbl_time_total.configure(text=self.fmt_time(length))
                    if length > 0: self.slider.set((time_pos / length) * 100)

            except: pass
            
            if force_refresh: break
            time.sleep(0.5)

    def update_cover(self, art_url):
        try:
            resp = requests.get(art_url, auth=self.auth, stream=True, timeout=1)
            if resp.status_code == 200:
                img_data = Image.open(BytesIO(resp.content))
                ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(55, 55))
                self.cover_label.configure(image=ctk_img, text="")
            else: raise Exception
        except: self.cover_label.configure(image=None, text="🎵")

    def change_speed(self, choice):
        val = choice.replace("x", "")
        self.send("rate", val=val)

    def on_scroll(self, event):
        direction = 1 if event.delta > 0 else -1
        if direction > 0: keyboard.send("volume up")
        else: keyboard.send("volume down")
        
        self.lbl_artist.configure(text="Volume Système")
        self.show_ui()
        self.after(1000, lambda: self.lbl_artist.configure(text=self.current_title[:30] + "..." if len(self.current_title)>30 else self.current_title))

    def show_ui(self):
        self.deiconify()
        self.reset_timer()
        if not self.is_visible:
            self.is_visible = True
            self.fade_in()

    def fade_in(self):
        if not self.is_visible: return
        alpha = self.attributes("-alpha")
        if alpha < MAX_OPACITY:
            self.attributes("-alpha", alpha + 0.08)
            self.after(15, self.fade_in)
        else:
            self.attributes("-alpha", MAX_OPACITY)

    def fade_out(self):
        try:
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
            if widget and str(widget).startswith(str(self)):
                self.on_mouse_enter(None)
                return
        except: pass

        alpha = self.attributes("-alpha")
        if alpha > 0:
            self.attributes("-alpha", alpha - 0.05)
            self.after(15, self.fade_out)
        else:
            self.withdraw()
            self.is_visible = False

    def reset_timer(self):
        if self.hide_timer: self.after_cancel(self.hide_timer)
        self.hide_timer = self.after(AUTO_HIDE_DELAY, self.start_fade_out)
    
    def start_fade_out(self):
        self.fade_out()

    def send(self, cmd, val=None):
        try:
            params = {'command': cmd}
            if val: params['val'] = val
            requests.get(VLC_HOST, params=params, auth=self.auth, timeout=0.2)
            self.reset_timer()
        except: pass

    def on_slider_click(self, event): self.is_dragging_slider = True
    def on_slider_drag(self, value):
        self.is_dragging_slider = True
        current_secs = (value / 100) * self.duration
        self.lbl_time_curr.configure(text=self.fmt_time(current_secs))

    def on_slider_release(self, event):
        self.send("seek", f"{self.slider.get()}%")
        self.after(500, lambda: setattr(self, 'is_dragging_slider', False))

    def fmt_time(self, s): return f"{int(s//60):02}:{int(s%60):02}"
    def start_move(self, e): self.x, self.y = e.x, e.y
    def do_move(self, e): self.geometry(f"+{self.winfo_x() + (e.x - self.x)}+{self.winfo_y() + (e.y - self.y)}")

if __name__ == "__main__":
    app = VLCOverlay()
    app.mainloop()