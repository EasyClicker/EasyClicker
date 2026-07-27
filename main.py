import time
import random
import threading
import ctypes
import os
import sys
import json
from PIL import Image, ImageDraw
import customtkinter as ctk
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, KeyCode, Controller as KeyboardController

# === SINGLE INSTANCE CHECK ===
ERROR_ALREADY_EXISTS = 183
mutex_name = "EasyClicker_Unique_App_Mutex_2026"
kernel32 = ctypes.windll.kernel32
mutex_handle = kernel32.CreateMutexW(None, False, mutex_name)

if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
    sys.exit(0)

# Set explicit AppUserModelID for Windows taskbar icon binding
try:
    myappid = 'EasyClicker.AutoClicker.App.1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# Default theme configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# --- CONFIG & CACHE DIRECTORY IN APPDATA ---
def get_app_dir():
    appdata_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'EasyClicker')
    os.makedirs(appdata_dir, exist_ok=True)
    return appdata_dir


APP_DIR = get_app_dir()
CONFIG_FILE = os.path.join(APP_DIR, 'easyclicker_config.json')

# --- GLOBAL RESOURCE CACHE IN MEMORY ---
_RESOURCE_PATH_CACHE = {}
_GEAR_ICON_CACHE = None


def get_resource_path(relative_path):
    if relative_path in _RESOURCE_PATH_CACHE:
        return _RESOURCE_PATH_CACHE[relative_path]

    if hasattr(sys, '_MEIPASS'):
        path = os.path.join(sys._MEIPASS, relative_path)
    elif getattr(sys, 'frozen', False):
        path = os.path.join(os.path.dirname(sys.executable), relative_path)
    else:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

    _RESOURCE_PATH_CACHE[relative_path] = path
    return path


def set_window_icon(window):
    icon_path = get_resource_path("icon.ico")
    if os.path.exists(icon_path):
        try:
            window.iconbitmap(icon_path)
        except Exception:
            pass


# Adaptive gear icon generation with two-tier cache
def create_gear_icon(size=(16, 16)):
    global _GEAR_ICON_CACHE
    if _GEAR_ICON_CACHE is not None:
        return _GEAR_ICON_CACHE

    cache_light_file = os.path.join(APP_DIR, "gear_light_cache.png")
    cache_dark_file = os.path.join(APP_DIR, "gear_dark_cache.png")

    if os.path.exists(cache_light_file) and os.path.exists(cache_dark_file):
        try:
            img_light = Image.open(cache_light_file)
            img_dark = Image.open(cache_dark_file)
            _GEAR_ICON_CACHE = ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=size)
            return _GEAR_ICON_CACHE
        except Exception:
            pass

    def draw_gear(color):
        img_size = 128
        img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        center = img_size / 2

        tooth_len, tooth_w = 56, 18
        for angle in (0, 45, 90, 135):
            rect = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(rect)
            draw.rounded_rectangle(
                [center - tooth_w / 2, center - tooth_len, center + tooth_w / 2, center + tooth_len],
                radius=5, fill=color
            )
            rotated = rect.rotate(angle, resample=Image.BICUBIC, center=(center, center))
            img = Image.alpha_composite(img, rotated)

        draw = ImageDraw.Draw(img)
        body_r = 42
        draw.ellipse([center - body_r, center - body_r, center + body_r, center + body_r], fill=color)

        hole_r = 18
        draw.ellipse([center - hole_r, center - hole_r, center + hole_r, center + hole_r], fill=(0, 0, 0, 0))
        return img

    img_light_mode = draw_gear("#0F172A")
    img_dark_mode = draw_gear("#F3F4F6")

    try:
        img_light_mode.save(cache_light_file, "PNG")
        img_dark_mode.save(cache_dark_file, "PNG")
    except Exception:
        pass

    _GEAR_ICON_CACHE = ctk.CTkImage(light_image=img_light_mode, dark_image=img_dark_mode, size=size)
    return _GEAR_ICON_CACHE


# RU to EN keyboard mapping
RU_TO_EN = {
    'й': 'Q', 'ц': 'W', 'у': 'E', 'к': 'R', 'е': 'T', 'н': 'Y', 'г': 'U', 'ш': 'I', 'щ': 'O', 'з': 'P', 'х': '[',
    'ъ': ']',
    'ф': 'A', 'ы': 'S', 'в': 'D', 'а': 'F', 'п': 'G', 'р': 'H', 'о': 'J', 'л': 'K', 'д': 'L', 'ж': ';', 'э': "'",
    'я': 'Z', 'ч': 'X', 'с': 'C', 'м': 'V', 'и': 'B', 'т': 'N', 'ь': 'M', 'б': ',', 'ю': '.',
    'Й': 'Q', 'Ц': 'W', 'У': 'E', 'К': 'R', 'Е': 'T', 'Н': 'Y', 'Г': 'U', 'Ш': 'I', 'Щ': 'O', 'З': 'P', 'Х': '[',
    'Ъ': ']',
    'Ф': 'A', 'Ы': 'S', 'В': 'D', 'А': 'F', 'П': 'G', 'Р': 'H', 'О': 'J', 'Л': 'K', 'Д': 'L', 'Ж': ';', 'Э': "'",
    'Я': 'Z', 'Ч': 'X', 'С': 'C', 'М': 'V', 'И': 'B', 'Т': 'N', 'Ь': 'M', 'Б': ',', 'Ю': '.'
}

NUMPAD_VK_MAP = {
    96: "NUM 0", 97: "NUM 1", 98: "NUM 2", 99: "NUM 3", 100: "NUM 4",
    101: "NUM 5", 102: "NUM 6", 103: "NUM 7", 104: "NUM 8", 105: "NUM 9",
    106: "NUM *", 107: "NUM +", 109: "NUM -", 110: "NUM .", 111: "NUM /"
}


def serialize_input(data):
    if not data:
        return None
    t = data.get('type')
    if t == 'mouse':
        btn = data.get('button')
        return {'type': 'mouse', 'button': str(btn).split('.')[-1], 'display': data.get('display')}
    elif t == 'keyboard':
        key = data.get('key')
        if hasattr(key, 'vk') and key.vk in NUMPAD_VK_MAP:
            return {'type': 'keyboard', 'key_kind': 'vk', 'vk': key.vk, 'display': data.get('display')}
        elif isinstance(key, str):
            return {'type': 'keyboard', 'key_kind': 'char', 'char': key, 'display': data.get('display')}
        elif isinstance(key, Key):
            return {'type': 'keyboard', 'key_kind': 'special', 'name': key.name, 'display': data.get('display')}
        else:
            return {'type': 'keyboard', 'key_kind': 'char', 'char': str(key), 'display': data.get('display')}
    return None


def deserialize_input(data):
    if not data:
        return None
    t = data.get('type')
    if t == 'mouse':
        btn_name = data.get('button', 'left')
        btn = getattr(Button, btn_name, Button.left)
        return {'type': 'mouse', 'button': btn, 'display': data.get('display', 'LMB')}
    elif t == 'keyboard':
        kind = data.get('key_kind')
        if kind == 'vk':
            return {'type': 'keyboard', 'key': KeyCode(vk=data.get('vk')), 'display': data.get('display')}
        elif kind == 'special':
            return {'type': 'keyboard', 'key': getattr(Key, data.get('name'), Key.f6), 'display': data.get('display')}
        elif kind == 'char':
            return {'type': 'keyboard', 'key': data.get('char'), 'display': data.get('display')}
    return None


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        self.geometry("340x240")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        set_window_icon(self)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Application Settings", font=("Arial", 16, "bold"),
                     text_color=("#0F172A", "#F3F4F6")).pack(pady=15)

        self.topmost_var = ctk.BooleanVar(value=parent.is_topmost)
        self.topmost_cb = ctk.CTkCheckBox(self, text="Always on Top", variable=self.topmost_var,
                                          command=self._toggle_topmost, text_color=("#0F172A", "#F3F4F6"))
        self.topmost_cb.pack(pady=10, anchor="w", padx=30)

        ctk.CTkLabel(self, text="App Theme:", font=("Arial", 12), text_color=("#0F172A", "#F3F4F6")).pack(pady=(10, 2),
                                                                                                          anchor="w",
                                                                                                          padx=30)
        self.theme_opt = ctk.CTkOptionMenu(
            self, values=["Dark", "Light", "System"], command=self._apply_theme,
            fg_color=("#E2E8F0", "#2B2D31"), button_color=("#CBD5E1", "#3F4147"),
            button_hover_color=("#94A3B8", "#4E5058"), text_color=("#0F172A", "#F3F4F6")
        )
        self.theme_opt.set(parent.appearance_mode)
        self.theme_opt.pack(pady=5, fill="x", padx=30)

        ctk.CTkButton(
            self, text="Close", command=self.destroy,
            fg_color=("#2563EB", "#3B82F6"), hover_color=("#1D4ED8", "#2563EB"), text_color="#FFFFFF"
        ).pack(pady=15)

    def _toggle_topmost(self):
        val = self.topmost_var.get()
        self.parent.is_topmost = val
        self.parent.attributes("-topmost", val)
        self.parent._save_config()

    def _apply_theme(self, choice):
        self.parent.appearance_mode = choice
        ctk.set_appearance_mode(choice)
        self.parent._save_config()


class EasyClicker(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EasyClicker")
        self.geometry("820x490")
        self.maxsize(820, 490)

        # Exact minimum boundary fitting only Target, Interval, and Status
        self.minsize(270, 230)
        self.resizable(True, True)

        self.is_topmost = False
        self.appearance_mode = "Dark"
        self.settings_window = None

        self.mouse_ctrl = MouseController()
        self.kb_ctrl = KeyboardController()

        self.clicker_active = False
        self.hold_active = False

        self.ac_target = {'type': 'mouse', 'button': Button.left, 'display': 'LMB'}
        self.hold_target = {'type': 'keyboard', 'key': 'w', 'display': 'W'}
        self.ac_hotkey = {'key': Key.f6, 'display': 'F6'}
        self.hold_hotkey = {'key': Key.f7, 'display': 'F7'}

        self.binding_mode = None
        self.bind_start_time = 0
        self.bind_cooldown = 0

        self._current_header_state = None
        self._current_grid_state = None
        self._current_height_level = None

        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Configure>", self._on_window_resize)

        self.after(10, self._deferred_init)

    def _deferred_init(self):
        set_window_icon(self)
        self._load_config()

        self.kb_listener = keyboard.Listener(on_press=self._on_key_press)
        self.kb_listener.start()

        self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self.mouse_listener.start()

    def _build_ui(self):
        self.header = ctk.CTkFrame(self, height=36, corner_radius=0, fg_color="transparent")

        gear_img = create_gear_icon(size=(16, 16))

        self.settings_btn = ctk.CTkButton(
            self.header, text=" Settings", image=gear_img, compound="left",
            width=90, fg_color=("#E2E8F0", "#2B2D31"), hover_color=("#CBD5E1", "#3F4147"),
            text_color=("#0F172A", "#F3F4F6"), command=self._open_settings
        )

        self.title_label = ctk.CTkLabel(self.header, text="EasyClicker", font=("Arial", 16, "bold"),
                                        text_color=("#0F172A", "#F3F4F6"))

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")

        entry_kwargs = {
            "fg_color": ("#FFFFFF", "#1E1F22"),
            "border_color": ("#94A3B8", "#3F4147"),
            "border_width": 1,
            "text_color": ("#0F172A", "#F3F4F6")
        }

        # === AUTOCLICKER ===
        self.ac_frame = ctk.CTkFrame(self.main_container, corner_radius=12, fg_color=("#FFFFFF", "#2B2D31"),
                                     border_color=("#CBD5E1", "#3F4147"), border_width=1)
        self.ac_frame.grid_columnconfigure(0, weight=1)

        self.ac_title_lbl = ctk.CTkLabel(self.ac_frame, text="⚡ AUTOCLICKER", font=("Arial", 15, "bold"),
                                         text_color=("#1D4ED8", "#60A5FA"))
        self.ac_title_lbl.grid(row=0, column=0, pady=(10, 5))

        self.ac_target_lbl = ctk.CTkLabel(self.ac_frame, text="Click Target:", font=("Arial", 11, "bold"),
                                          text_color=("#0F172A", "#F3F4F6"))
        self.ac_target_lbl.grid(row=1, column=0, pady=(2, 1), sticky="w", padx=15)

        self.ac_target_btn = ctk.CTkButton(
            self.ac_frame, text=f"[{self.ac_target['display']}]  (Click to Set)",
            fg_color="#2563EB", hover_color="#1D4ED8", text_color="#FFFFFF",
            command=lambda: self._start_binding('ac_target')
        )
        self.ac_target_btn.grid(row=2, column=0, padx=15, pady=3, sticky="ew")

        self.ac_interval_lbl = ctk.CTkLabel(self.ac_frame, text="Click Interval (ms):", font=("Arial", 10),
                                            text_color=("#334155", "#CBD5E1"))
        self.ac_interval_lbl.grid(row=3, column=0, pady=(4, 0), sticky="w", padx=15)

        self.ac_interval = ctk.CTkEntry(self.ac_frame, placeholder_text="100", **entry_kwargs)
        self.ac_interval.insert(0, "100")
        self.ac_interval.grid(row=4, column=0, padx=15, pady=1, sticky="ew")

        self.ac_offset_lbl = ctk.CTkLabel(self.ac_frame, text="Random Offset (± ms):", font=("Arial", 10),
                                          text_color=("#334155", "#CBD5E1"))
        self.ac_offset_lbl.grid(row=5, column=0, pady=(4, 0), sticky="w", padx=15)

        self.ac_offset = ctk.CTkEntry(self.ac_frame, placeholder_text="20", **entry_kwargs)
        self.ac_offset.insert(0, "20")
        self.ac_offset.grid(row=6, column=0, padx=15, pady=1, sticky="ew")

        self.ac_hotkey_lbl = ctk.CTkLabel(self.ac_frame, text="Global Start/Stop Hotkey:", font=("Arial", 11, "bold"),
                                          text_color=("#0F172A", "#F3F4F6"))
        self.ac_hotkey_lbl.grid(row=7, column=0, pady=(6, 1), sticky="w", padx=15)

        self.ac_hotkey_btn = ctk.CTkButton(
            self.ac_frame, text=f"[{self.ac_hotkey['display']}]  (Click to Set)",
            fg_color=("#E2E8F0", "#3F4147"), hover_color=("#CBD5E1", "#4E5058"),
            text_color=("#0F172A", "#F3F4F6"), command=lambda: self._start_binding('ac_hotkey')
        )
        self.ac_hotkey_btn.grid(row=8, column=0, padx=15, pady=3, sticky="ew")

        # Row 99 ensures Status snaps right below whichever row is last visible!
        self.ac_status_lbl = ctk.CTkLabel(self.ac_frame, text="Status: STOPPED", text_color=("#DC2626", "#EF4444"),
                                          font=("Arial", 12, "bold"))
        self.ac_status_lbl.grid(row=99, column=0, pady=(6, 8))

        # === HOLD MODE ===
        self.hold_frame = ctk.CTkFrame(self.main_container, corner_radius=12, fg_color=("#FFFFFF", "#2B2D31"),
                                       border_color=("#CBD5E1", "#3F4147"), border_width=1)
        self.hold_frame.grid_columnconfigure(0, weight=1)

        self.hold_title_lbl = ctk.CTkLabel(self.hold_frame, text="✊ HOLD MODE", font=("Arial", 15, "bold"),
                                           text_color=("#059669", "#34D399"))
        self.hold_title_lbl.grid(row=0, column=0, pady=(10, 5))

        self.hold_target_lbl = ctk.CTkLabel(self.hold_frame, text="Hold Target:", font=("Arial", 11, "bold"),
                                            text_color=("#0F172A", "#F3F4F6"))
        self.hold_target_lbl.grid(row=1, column=0, pady=(2, 1), sticky="w", padx=15)

        self.hold_target_btn = ctk.CTkButton(
            self.hold_frame, text=f"[{self.hold_target['display']}]  (Click to Set)",
            fg_color="#059669", hover_color="#047857", text_color="#FFFFFF",
            command=lambda: self._start_binding('hold_target')
        )
        self.hold_target_btn.grid(row=2, column=0, padx=15, pady=3, sticky="ew")

        self.hold_mode_lbl = ctk.CTkLabel(self.hold_frame, text="Hold Type:", font=("Arial", 10),
                                          text_color=("#334155", "#CBD5E1"))
        self.hold_mode_lbl.grid(row=3, column=0, pady=(4, 0), sticky="w", padx=15)

        self.hold_mode = ctk.CTkOptionMenu(
            self.hold_frame, values=["Continuous Hold", "Interval Hold"],
            fg_color=("#E2E8F0", "#059669"), button_color=("#CBD5E1", "#047857"),
            button_hover_color=("#94A3B8", "#065F46"), text_color=("#0F172A", "#FFFFFF"),
            command=self._on_hold_mode_change
        )
        self.hold_mode.set("Continuous Hold")
        self.hold_mode.grid(row=4, column=0, padx=15, pady=1, sticky="ew")

        self.fields_frame = ctk.CTkFrame(self.hold_frame, fg_color="transparent")
        self.fields_frame.grid(row=5, column=0, padx=15, pady=1, sticky="ew")
        self.fields_frame.grid_columnconfigure((0, 1), weight=1)

        self.lbl_hold_time = ctk.CTkLabel(self.fields_frame, text="Hold Duration (sec):", font=("Arial", 9),
                                          text_color=("#334155", "#CBD5E1"))
        self.lbl_hold_time.grid(row=0, column=0, sticky="w")
        self.hold_time_entry = ctk.CTkEntry(self.fields_frame, placeholder_text="2.0", **entry_kwargs)
        self.hold_time_entry.insert(0, "2.0")
        self.hold_time_entry.grid(row=1, column=0, padx=(0, 3), sticky="ew")

        self.lbl_pause_time = ctk.CTkLabel(self.fields_frame, text="Pause Interval (sec):", font=("Arial", 9),
                                           text_color=("#334155", "#CBD5E1"))
        self.lbl_pause_time.grid(row=0, column=1, sticky="w")
        self.hold_pause_entry = ctk.CTkEntry(self.fields_frame, placeholder_text="1.0", **entry_kwargs)
        self.hold_pause_entry.insert(0, "1.0")
        self.hold_pause_entry.grid(row=1, column=1, padx=(3, 0), sticky="ew")

        self._update_hold_fields_visual(enabled=False)

        self.hold_hotkey_lbl = ctk.CTkLabel(self.hold_frame, text="Global Start/Stop Hotkey:",
                                            font=("Arial", 11, "bold"), text_color=("#0F172A", "#F3F4F6"))
        self.hold_hotkey_lbl.grid(row=7, column=0, pady=(6, 1), sticky="w", padx=15)

        self.hold_hotkey_btn = ctk.CTkButton(
            self.hold_frame, text=f"[{self.hold_hotkey['display']}]  (Click to Set)",
            fg_color=("#E2E8F0", "#3F4147"), hover_color=("#CBD5E1", "#4E5058"),
            text_color=("#0F172A", "#F3F4F6"), command=lambda: self._start_binding('hold_hotkey')
        )
        self.hold_hotkey_btn.grid(row=8, column=0, padx=15, pady=3, sticky="ew")

        self.hold_status_lbl = ctk.CTkLabel(self.hold_frame, text="Status: STOPPED", text_color=("#DC2626", "#EF4444"),
                                            font=("Arial", 12, "bold"))
        self.hold_status_lbl.grid(row=99, column=0, pady=(6, 8))

        self._apply_header_state("full")
        self._apply_grid_state("side_by_side")

    def _on_window_resize(self, event):
        if event.widget != self:
            return

        w, h = event.width, event.height

        # 1. Header State
        if w >= 420:
            new_header_state = "full"
        else:
            new_header_state = "minimal"

        # 2. Side-by-Side vs AC Only
        new_grid_state = "side_by_side" if w >= 620 else "ac_only"

        # 3. Responsive Vertical Collapse
        if h >= 410:
            new_height_level = 3  # Target + Interval + Offset + Hotkey + Status
        elif h >= 320:
            new_height_level = 2  # Target + Interval + Offset + Status
        else:
            new_height_level = 1  # Target + Interval + Status (Offset & Hotkey Hidden!)

        if new_header_state != self._current_header_state:
            self._current_header_state = new_header_state
            self._apply_header_state(new_header_state)

        if new_grid_state != self._current_grid_state:
            self._current_grid_state = new_grid_state
            self._apply_grid_state(new_grid_state)

        if new_height_level != self._current_height_level:
            self._current_height_level = new_height_level
            self._apply_height_collapse(new_height_level)

    def _apply_header_state(self, state):
        self.main_container.pack_forget()
        self.header.pack(fill="x", padx=15, pady=(5, 0))
        self.main_container.pack(fill="both", expand=True, padx=8, pady=4)

        if state == "full":
            self.settings_btn.pack(side="left")
            self.title_label.pack(side="left", padx=15)
        elif state == "minimal":
            self.title_label.pack_forget()
            self.settings_btn.pack(side="left")

    def _apply_grid_state(self, state):
        if state == "side_by_side":
            self.main_container.grid_columnconfigure(0, weight=1, uniform="panels")
            self.main_container.grid_columnconfigure(1, weight=1, uniform="panels")
            self.main_container.grid_rowconfigure(0, weight=1)

            self.ac_frame.grid(row=0, column=0, padx=6, pady=4, sticky="nsew")
            self.hold_frame.grid(row=0, column=1, padx=6, pady=4, sticky="nsew")
        elif state == "ac_only":
            self.hold_frame.grid_forget()

            self.main_container.grid_columnconfigure(0, weight=1, uniform="")
            self.main_container.grid_columnconfigure(1, weight=0, uniform="")
            self.main_container.grid_rowconfigure(0, weight=1)

            self.ac_frame.grid(row=0, column=0, padx=6, pady=4, sticky="nsew")

    def _apply_height_collapse(self, level):
        ac_hotkey_widgets = (self.ac_hotkey_lbl, self.ac_hotkey_btn)
        ac_offset_widgets = (self.ac_offset_lbl, self.ac_offset)

        hold_hotkey_widgets = (self.hold_hotkey_lbl, self.hold_hotkey_btn)
        hold_offset_widgets = (self.hold_mode_lbl, self.hold_mode, self.fields_frame)

        def toggle_widgets(widgets, show):
            for w in widgets:
                if show:
                    w.grid()
                else:
                    w.grid_remove()

        # Hide Hotkey at level < 3
        toggle_widgets(ac_hotkey_widgets, level >= 3)
        toggle_widgets(hold_hotkey_widgets, level >= 3)

        # Hide Random Offset / Mode Options at level < 2 (snaps Status directly under Click Interval!)
        toggle_widgets(ac_offset_widgets, level >= 2)
        toggle_widgets(hold_offset_widgets, level >= 2)

    def _open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()

    def _on_hold_mode_change(self, choice):
        self._update_hold_fields_visual(enabled=(choice != "Continuous Hold"))

    def _update_hold_fields_visual(self, enabled: bool):
        st = "normal" if enabled else "disabled"
        bg = ("#FFFFFF", "#1E1F22") if enabled else ("#E2E8F0", "#232428")
        txt = ("#0F172A", "#F3F4F6") if enabled else ("#64748B", "#94A3B8")
        border = ("#94A3B8", "#3F4147") if enabled else ("#CBD5E1", "#2B2D31")

        self.hold_time_entry.configure(state=st, fg_color=bg, text_color=txt, border_color=border)
        self.hold_pause_entry.configure(state=st, fg_color=bg, text_color=txt, border_color=border)
        self.lbl_hold_time.configure(text_color=txt)
        self.lbl_pause_time.configure(text_color=txt)

    def _save_config(self):
        config = {
            'ac_interval': self.ac_interval.get(),
            'ac_offset': self.ac_offset.get(),
            'hold_time': self.hold_time_entry.get(),
            'hold_pause': self.hold_pause_entry.get(),
            'hold_mode': self.hold_mode.get(),
            'is_topmost': self.is_topmost,
            'appearance_mode': self.appearance_mode,
            'ac_target': serialize_input(self.ac_target),
            'hold_target': serialize_input(self.hold_target),
            'ac_hotkey': serialize_input(self.ac_hotkey),
            'hold_hotkey': serialize_input(self.hold_hotkey)
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def _load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)

            if 'ac_interval' in cfg:
                self.ac_interval.delete(0, 'end')
                self.ac_interval.insert(0, str(cfg['ac_interval']))
            if 'ac_offset' in cfg:
                self.ac_offset.delete(0, 'end')
                self.ac_offset.insert(0, str(cfg['ac_offset']))
            if 'hold_time' in cfg:
                self.hold_time_entry.delete(0, 'end')
                self.hold_time_entry.insert(0, str(cfg['hold_time']))
            if 'hold_pause' in cfg:
                self.hold_pause_entry.delete(0, 'end')
                self.hold_pause_entry.insert(0, str(cfg['hold_pause']))
            if 'hold_mode' in cfg:
                mode_val = "Interval Hold" if "Interval" in cfg['hold_mode'] else "Continuous Hold"
                self.hold_mode.set(mode_val)
                self._on_hold_mode_change(mode_val)
            if 'is_topmost' in cfg:
                self.is_topmost = cfg['is_topmost']
                self.attributes("-topmost", self.is_topmost)
            if 'appearance_mode' in cfg:
                self.appearance_mode = cfg['appearance_mode']
                ctk.set_appearance_mode(self.appearance_mode)

            targets = [('ac_target', self.ac_target_btn), ('hold_target', self.hold_target_btn),
                       ('ac_hotkey', self.ac_hotkey_btn), ('hold_hotkey', self.hold_hotkey_btn)]

            for key_name, btn in targets:
                if cfg.get(key_name):
                    des = deserialize_input(cfg[key_name])
                    if des:
                        setattr(self, key_name, des)
                        btn.configure(text=f"[{des['display']}]  (Click to Set)")
        except Exception:
            pass

    def _on_close(self):
        self._save_config()
        self.destroy()

    def _start_binding(self, mode):
        if self.binding_mode is not None or time.time() < self.bind_cooldown:
            return

        self.binding_mode = mode
        self.bind_start_time = time.time() + 0.08
        self._set_binding_buttons_state("disabled")

        btn_map = {
            'ac_target': (self.ac_target_btn, ">> PRESS ANY KEY / MOUSE <<"),
            'hold_target': (self.hold_target_btn, ">> PRESS ANY KEY / MOUSE <<"),
            'ac_hotkey': (self.ac_hotkey_btn, ">> PRESS HOTKEY <<"),
            'hold_hotkey': (self.hold_hotkey_btn, ">> PRESS HOTKEY <<")
        }

        btn, txt = btn_map[mode]
        btn.configure(text=txt, fg_color=("#D97706", "#F59E0B"), text_color="#FFFFFF")

    def _set_binding_buttons_state(self, state):
        for btn in (self.ac_target_btn, self.hold_target_btn, self.ac_hotkey_btn, self.hold_hotkey_btn):
            btn.configure(state=state)

    def _on_mouse_click(self, x, y, button, pressed):
        if not pressed or not self.binding_mode or time.time() < self.bind_start_time:
            return

        if self.binding_mode in ('ac_target', 'hold_target'):
            btn_str = str(button).split('.')[-1].upper()
            display_map = {"LEFT": "LMB", "RIGHT": "RMB", "MIDDLE": "MMB", "X1": "Mouse 4 (Back)",
                           "X2": "Mouse 5 (Forward)"}
            display = display_map.get(btn_str, f"Mouse ({btn_str})")

            self._finalize_binding({'type': 'mouse', 'button': button, 'display': display})

    def _on_key_press(self, key):
        if self.binding_mode:
            if hasattr(key, 'vk') and key.vk in NUMPAD_VK_MAP:
                display_str, char_key = NUMPAD_VK_MAP[key.vk], key
            elif hasattr(key, 'char') and key.char:
                raw_char = key.char
                eng_char = RU_TO_EN.get(raw_char, raw_char).upper()
                display_str, char_key = eng_char, eng_char.lower()
            else:
                display_str = str(key).replace("Key.", "").upper()
                char_key = key

            self._finalize_binding({'type': 'keyboard', 'key': char_key, 'display': display_str})
            return

        if self._matches_hotkey(key, self.ac_hotkey):
            self.toggle_autoclicker()
        elif self._matches_hotkey(key, self.hold_hotkey):
            self.toggle_hold()

    def _matches_hotkey(self, pressed_key, hotkey_data):
        hk = hotkey_data.get('key')
        if not hk:
            return False

        if hasattr(pressed_key, 'vk') and hasattr(hk, 'vk'):
            return pressed_key.vk == hk.vk
        if hasattr(pressed_key, 'char') and pressed_key.char:
            char = RU_TO_EN.get(pressed_key.char, pressed_key.char).lower()
            return char == str(hk).lower()

        return pressed_key == hk

    def _finalize_binding(self, data):
        color_map = {
            'ac_target': "#2563EB",
            'hold_target': "#059669",
            'ac_hotkey': ("#E2E8F0", "#3F4147"),
            'hold_hotkey': ("#E2E8F0", "#3F4147")
        }
        btn_map = {
            'ac_target': self.ac_target_btn,
            'hold_target': self.hold_target_btn,
            'ac_hotkey': self.ac_hotkey_btn,
            'hold_hotkey': self.hold_hotkey_btn
        }

        mode = self.binding_mode
        if mode in ('ac_hotkey', 'hold_hotkey') and data['type'] == 'mouse':
            self.binding_mode = None
            self.bind_cooldown = time.time() + 0.1
            self._set_binding_buttons_state("normal")
            return

        setattr(self, mode, data)
        txt_color = "#FFFFFF" if mode in ('ac_target', 'hold_target') else ("#0F172A", "#F3F4F6")
        btn_map[mode].configure(text=f"[{data['display']}]  (Click to Set)", fg_color=color_map[mode],
                                text_color=txt_color)

        self.binding_mode = None
        self.bind_cooldown = time.time() + 0.1
        self._set_binding_buttons_state("normal")
        self._save_config()

    def toggle_autoclicker(self):
        if self.hold_active: return
        self.clicker_active = not self.clicker_active
        txt, color = ("Status: ACTIVE", ("#16A34A", "#10B981")) if self.clicker_active else ("Status: STOPPED",
                                                                                             ("#DC2626", "#EF4444"))
        self.ac_status_lbl.configure(text=txt, text_color=color)

        if self.clicker_active:
            threading.Thread(target=self._autoclick_loop, daemon=True).start()

    def toggle_hold(self):
        if self.clicker_active: return
        self.hold_active = not self.hold_active
        txt, color = ("Status: ACTIVE", ("#16A34A", "#10B981")) if self.hold_active else ("Status: STOPPED",
                                                                                          ("#DC2626", "#EF4444"))
        self.hold_status_lbl.configure(text=txt, text_color=color)

        if self.hold_active:
            threading.Thread(target=self._hold_loop, daemon=True).start()

    def _autoclick_loop(self):
        while self.clicker_active:
            try:
                base_delay = float(self.ac_interval.get()) / 1000.0
                offset = float(self.ac_offset.get()) / 1000.0
            except ValueError:
                base_delay, offset = 0.1, 0.02

            actual_delay = max(0.001, base_delay + random.uniform(-offset, offset))

            if self.ac_target['type'] == 'mouse':
                self.mouse_ctrl.click(self.ac_target['button'])
            else:
                self.kb_ctrl.press(self.ac_target['key'])
                self.kb_ctrl.release(self.ac_target['key'])

            time.sleep(actual_delay)

    def _hold_loop(self):
        target = self.hold_target
        is_continuous = self.hold_mode.get() == "Continuous Hold"

        if is_continuous:
            if target['type'] == 'mouse':
                self.mouse_ctrl.press(target['button'])
            else:
                self.kb_ctrl.press(target['key'])

            while self.hold_active:
                time.sleep(0.05)

            if target['type'] == 'mouse':
                self.mouse_ctrl.release(target['button'])
            else:
                self.kb_ctrl.release(target['key'])
        else:
            try:
                hold_duration = float(self.hold_time_entry.get())
                pause_duration = float(self.hold_pause_entry.get())
            except ValueError:
                hold_duration, pause_duration = 2.0, 1.0

            while self.hold_active:
                if target['type'] == 'mouse':
                    self.mouse_ctrl.press(target['button'])
                else:
                    self.kb_ctrl.press(target['key'])

                end_time = time.time() + hold_duration
                while self.hold_active and time.time() < end_time:
                    time.sleep(0.05)

                if target['type'] == 'mouse':
                    self.mouse_ctrl.release(target['button'])
                else:
                    self.kb_ctrl.release(target['key'])

                end_time = time.time() + pause_duration
                while self.hold_active and time.time() < end_time:
                    time.sleep(0.05)


if __name__ == "__main__":
    app = EasyClicker()
    app.mainloop()

# pyinstaller --onedir --noconsole --icon=icon.ico --add-data "icon.ico;." --collect-all customtkinter --name "EasyClicker" main.py