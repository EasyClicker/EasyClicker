import time
import random
import threading
import ctypes
import os
import sys
import json
import math
from PIL import Image, ImageDraw
import customtkinter as ctk
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, KeyCode, Controller as KeyboardController

# Уникальный ID процесса для привязки иконки к панели задач Windows
try:
    myappid = 'EasyClicker.AutoClicker.App.1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# Настройки темы
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "easyclicker_config.json"


# Функция для точного поиска файлов в папке программы (в .py и в .exe)
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


# Установка иконки для окна
def set_window_icon(window):
    icon_path = get_resource_path("icon.ico")
    if os.path.exists(icon_path):
        try:
            window.iconbitmap(icon_path)
        except Exception:
            pass


# Генерация четкой векторной шестеренки без использования шрифтов/эмодзи
def create_gear_icon(size=(16, 16), color="#E2E8F0"):
    img_size = 128
    img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
    center = img_size / 2

    # Зубья шестерни (4 скругленных прямоугольника, повернутые под разными углами)
    tooth_len = 56
    tooth_w = 18
    for angle in [0, 45, 90, 135]:
        rect = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(rect)
        draw.rounded_rectangle(
            [center - tooth_w / 2, center - tooth_len, center + tooth_w / 2, center + tooth_len],
            radius=5, fill=color
        )
        rotated = rect.rotate(angle, resample=Image.BICUBIC, center=(center, center))
        img = Image.alpha_composite(img, rotated)

    draw = ImageDraw.Draw(img)
    # Основное тело шестерни (круг)
    body_r = 42
    draw.ellipse([center - body_r, center - body_r, center + body_r, center + body_r], fill=color)

    # Отверстие в центре
    hole_r = 18
    draw.ellipse([center - hole_r, center - hole_r, center + hole_r, center + hole_r], fill=(0, 0, 0, 0))

    return ctk.CTkImage(light_image=img, dark_image=img, size=size)


# Карта раскладки RU -> EN
RU_TO_EN = {
    'й': 'Q', 'ц': 'W', 'у': 'E', 'к': 'R', 'е': 'T', 'н': 'Y', 'г': 'U', 'ш': 'I', 'щ': 'O', 'з': 'P', 'х': '[', 'ъ': ']',
    'ф': 'A', 'ы': 'S', 'в': 'D', 'а': 'F', 'п': 'G', 'р': 'H', 'о': 'J', 'л': 'K', 'д': 'L', 'ж': ';', 'э': "'",
    'я': 'Z', 'ч': 'X', 'с': 'C', 'м': 'V', 'и': 'B', 'т': 'N', 'ь': 'M', 'б': ',', 'ю': '.',
    'Й': 'Q', 'Ц': 'W', 'У': 'E', 'К': 'R', 'Е': 'T', 'Н': 'Y', 'Г': 'U', 'Ш': 'I', 'Щ': 'O', 'З': 'P', 'Х': '[', 'Ъ': ']',
    'Ф': 'A', 'Ы': 'S', 'В': 'D', 'А': 'F', 'П': 'G', 'Р': 'H', 'О': 'J', 'Л': 'K', 'Д': 'L', 'Ж': ';', 'Э': "'",
    'Я': 'Z', 'Ч': 'X', 'С': 'C', 'М': 'V', 'И': 'B', 'Т': 'N', 'Ь': 'M', 'Б': ',', 'Ю': '.'
}

# Numpad VK-коды
NUMPAD_VK_MAP = {
    96: "NUM 0", 97: "NUM 1", 98: "NUM 2", 99: "NUM 3", 100: "NUM 4",
    101: "NUM 5", 102: "NUM 6", 103: "NUM 7", 104: "NUM 8", 105: "NUM 9",
    106: "NUM *", 107: "NUM +", 109: "NUM -", 110: "NUM .", 111: "NUM /"
}


# --- ФУНКЦИИ СЕРИАЛИЗАЦИИ ДЛЯ СОХРАНЕНИЯ НАСТРОЕК ---
def serialize_input(data):
    if not data:
        return None
    t = data.get('type')
    if t == 'mouse':
        btn = data.get('button')
        btn_str = str(btn).split('.')[-1]
        return {'type': 'mouse', 'button': btn_str, 'display': data.get('display')}
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
            vk = data.get('vk')
            return {'type': 'keyboard', 'key': KeyCode(vk=vk), 'display': data.get('display')}
        elif kind == 'special':
            name = data.get('name')
            return {'type': 'keyboard', 'key': getattr(Key, name, Key.f6), 'display': data.get('display')}
        elif kind == 'char':
            char = data.get('char')
            return {'type': 'keyboard', 'key': char, 'display': data.get('display')}
    return None


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        self.geometry("340x240")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Применение иконки
        set_window_icon(self)
        self.after(100, lambda: set_window_icon(self))

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Application Settings", font=("Arial", 16, "bold")).pack(pady=15)

        # Галочка Always on Top
        self.topmost_var = ctk.BooleanVar(value=parent.is_topmost)
        self.topmost_cb = ctk.CTkCheckBox(self, text="Always on Top", variable=self.topmost_var, command=self._toggle_topmost)
        self.topmost_cb.pack(pady=10, anchor="w", padx=30)

        # Выбор пресета скорости
        ctk.CTkLabel(self, text="Default Click Speed Preset:", font=("Arial", 12)).pack(pady=(10, 2), anchor="w", padx=30)
        self.preset_opt = ctk.CTkOptionMenu(self, values=["Fast (50ms)", "Normal (100ms)", "Slow (250ms)"], command=self._apply_preset)
        self.preset_opt.set(parent.selected_preset)
        self.preset_opt.pack(pady=5, fill="x", padx=30)

        ctk.CTkButton(self, text="Close", command=self.destroy, fg_color="#3B82F6").pack(pady=15)

    def _toggle_topmost(self):
        val = self.topmost_var.get()
        self.parent.is_topmost = val
        self.parent.attributes("-topmost", val)
        self.parent._save_config()

    def _apply_preset(self, choice):
        self.parent.selected_preset = choice
        if "Fast" in choice:
            self.parent.ac_interval.delete(0, 'end')
            self.parent.ac_interval.insert(0, "50")
        elif "Normal" in choice:
            self.parent.ac_interval.delete(0, 'end')
            self.parent.ac_interval.insert(0, "100")
        elif "Slow" in choice:
            self.parent.ac_interval.delete(0, 'end')
            self.parent.ac_interval.insert(0, "250")
        self.parent._save_config()


class EasyClicker(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EasyClicker")
        self.geometry("820x490")
        self.resizable(False, False)
        self.is_topmost = False
        self.selected_preset = "Normal (100ms)"
        self.settings_window = None

        # Установка иконки приложения
        set_window_icon(self)
        self.after(100, lambda: set_window_icon(self))

        self.mouse_ctrl = MouseController()
        self.kb_ctrl = KeyboardController()

        self.clicker_active = False
        self.hold_active = False

        # Дефолтные значения
        self.ac_target = {'type': 'mouse', 'button': Button.left, 'display': 'LMB'}
        self.hold_target = {'type': 'keyboard', 'key': 'w', 'display': 'W'}
        self.ac_hotkey = {'key': Key.f6, 'display': 'F6'}
        self.hold_hotkey = {'key': Key.f7, 'display': 'F7'}

        self.binding_mode = None
        self.bind_start_time = 0

        self._build_ui()
        self._load_config()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Фоновые слушатели событий
        self.kb_listener = keyboard.Listener(on_press=self._on_key_press)
        self.kb_listener.start()

        self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self.mouse_listener.start()

    def _build_ui(self):
        header = ctk.CTkFrame(self, height=45, corner_radius=0, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(10, 0))

        # Генерация чистой иконки шестерни для кнопки
        gear_img = create_gear_icon(size=(16, 16), color="#FFFFFF")

        self.settings_btn = ctk.CTkButton(
            header, text=" Settings", image=gear_img, compound="left",
            width=110, fg_color="#334155", hover_color="#475569", command=self._open_settings
        )
        self.settings_btn.pack(side="left")

        title_lbl = ctk.CTkLabel(header, text="EasyClicker", font=("Arial", 18, "bold"))
        title_lbl.pack(side="left", padx=20)

        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=10)

        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=1)

        # === КОЛОНКА 1: AUTOCLICKER ===
        ac_frame = ctk.CTkFrame(main_container, corner_radius=12)
        ac_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        ac_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(ac_frame, text="⚡ AUTOCLICKER", font=("Arial", 16, "bold"), text_color="#3B82F6").grid(row=0, column=0, pady=(15, 10))

        ctk.CTkLabel(ac_frame, text="Click Target:", font=("Arial", 12, "bold")).grid(row=1, column=0, pady=(5, 2), sticky="w", padx=20)
        self.ac_target_btn = ctk.CTkButton(
            ac_frame, text=f"[{self.ac_target['display']}]  (Click to Set)",
            fg_color="#2563EB", hover_color="#1D4ED8",
            command=lambda: self._start_binding('ac_target')
        )
        self.ac_target_btn.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(ac_frame, text="Click Interval (ms):", font=("Arial", 11)).grid(row=3, column=0, pady=(8, 0), sticky="w", padx=20)
        self.ac_interval = ctk.CTkEntry(ac_frame, placeholder_text="100")
        self.ac_interval.insert(0, "100")
        self.ac_interval.grid(row=4, column=0, padx=20, pady=2, sticky="ew")

        ctk.CTkLabel(ac_frame, text="Random Offset (± ms):", font=("Arial", 11)).grid(row=5, column=0, pady=(8, 0), sticky="w", padx=20)
        self.ac_offset = ctk.CTkEntry(ac_frame, placeholder_text="20")
        self.ac_offset.insert(0, "20")
        self.ac_offset.grid(row=6, column=0, padx=20, pady=2, sticky="ew")

        ctk.CTkLabel(ac_frame, text="Global Start/Stop Hotkey:", font=("Arial", 12, "bold")).grid(row=7, column=0, pady=(12, 2), sticky="w", padx=20)
        self.ac_hotkey_btn = ctk.CTkButton(
            ac_frame, text=f"[{self.ac_hotkey['display']}]  (Click to Set)",
            fg_color="#475569", hover_color="#64748B",
            command=lambda: self._start_binding('ac_hotkey')
        )
        self.ac_hotkey_btn.grid(row=8, column=0, padx=20, pady=5, sticky="ew")

        self.ac_status_lbl = ctk.CTkLabel(ac_frame, text="Status: STOPPED", text_color="#EF4444", font=("Arial", 13, "bold"))
        self.ac_status_lbl.grid(row=9, column=0, pady=15)

        # === КОЛОНКА 2: HOLD MODE ===
        hold_frame = ctk.CTkFrame(main_container, corner_radius=12)
        hold_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        hold_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hold_frame, text="✊ HOLD MODE", font=("Arial", 16, "bold"), text_color="#10B981").grid(row=0, column=0, pady=(15, 10))

        ctk.CTkLabel(hold_frame, text="Hold Target:", font=("Arial", 12, "bold")).grid(row=1, column=0, pady=(5, 2), sticky="w", padx=20)
        self.hold_target_btn = ctk.CTkButton(
            hold_frame, text=f"[{self.hold_target['display']}]  (Click to Set)",
            fg_color="#059669", hover_color="#047857",
            command=lambda: self._start_binding('hold_target')
        )
        self.hold_target_btn.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(hold_frame, text="Hold Type:", font=("Arial", 11)).grid(row=3, column=0, pady=(6, 0), sticky="w", padx=20)
        self.hold_mode = ctk.CTkOptionMenu(
            hold_frame, values=["Continuous Hold", "Interval Hold"],
            fg_color="#065F46", button_color="#047857", command=self._on_hold_mode_change
        )
        self.hold_mode.set("Continuous Hold")
        self.hold_mode.grid(row=4, column=0, padx=20, pady=2, sticky="ew")

        fields_frame = ctk.CTkFrame(hold_frame, fg_color="transparent")
        fields_frame.grid(row=5, column=0, padx=20, pady=2, sticky="ew")
        fields_frame.grid_columnconfigure(0, weight=1)
        fields_frame.grid_columnconfigure(1, weight=1)

        self.lbl_hold_time = ctk.CTkLabel(fields_frame, text="Hold Duration (sec):", font=("Arial", 10))
        self.lbl_hold_time.grid(row=0, column=0, sticky="w")
        self.hold_time_entry = ctk.CTkEntry(fields_frame, placeholder_text="2.0")
        self.hold_time_entry.insert(0, "2.0")
        self.hold_time_entry.grid(row=1, column=0, padx=(0, 5), sticky="ew")

        self.lbl_pause_time = ctk.CTkLabel(fields_frame, text="Pause Interval (sec):", font=("Arial", 10))
        self.lbl_pause_time.grid(row=0, column=1, sticky="w")
        self.hold_pause_entry = ctk.CTkEntry(fields_frame, placeholder_text="1.0")
        self.hold_pause_entry.insert(0, "1.0")
        self.hold_pause_entry.grid(row=1, column=1, padx=(5, 0), sticky="ew")

        self._update_hold_fields_visual(enabled=False)

        ctk.CTkLabel(hold_frame, text="Global Start/Stop Hotkey:", font=("Arial", 12, "bold")).grid(row=7, column=0, pady=(10, 2), sticky="w", padx=20)
        self.hold_hotkey_btn = ctk.CTkButton(
            hold_frame, text=f"[{self.hold_hotkey['display']}]  (Click to Set)",
            fg_color="#475569", hover_color="#64748B",
            command=lambda: self._start_binding('hold_hotkey')
        )
        self.hold_hotkey_btn.grid(row=8, column=0, padx=20, pady=5, sticky="ew")

        self.hold_status_lbl = ctk.CTkLabel(hold_frame, text="Status: STOPPED", text_color="#EF4444", font=("Arial", 13, "bold"))
        self.hold_status_lbl.grid(row=9, column=0, pady=15)

    def _open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()

    def _on_hold_mode_change(self, choice):
        if choice == "Continuous Hold":
            self._update_hold_fields_visual(enabled=False)
        else:
            self._update_hold_fields_visual(enabled=True)

    def _update_hold_fields_visual(self, enabled: bool):
        if enabled:
            self.hold_time_entry.configure(
                state="normal", fg_color="#0F172A", text_color="#F8FAFC", border_color="#475569"
            )
            self.hold_pause_entry.configure(
                state="normal", fg_color="#0F172A", text_color="#F8FAFC", border_color="#475569"
            )
            self.lbl_hold_time.configure(text_color="#F8FAFC")
            self.lbl_pause_time.configure(text_color="#F8FAFC")
        else:
            self.hold_time_entry.configure(
                state="disabled", fg_color="#1E293B", text_color="#64748B", border_color="#334155"
            )
            self.hold_pause_entry.configure(
                state="disabled", fg_color="#1E293B", text_color="#64748B", border_color="#334155"
            )
            self.lbl_hold_time.configure(text_color="#64748B")
            self.lbl_pause_time.configure(text_color="#64748B")

    # --- СИСТЕМА СОХРАНЕНИЯ / ЗАГРУЗКИ (JSON) ---
    def _save_config(self):
        config = {
            'ac_interval': self.ac_interval.get(),
            'ac_offset': self.ac_offset.get(),
            'hold_time': self.hold_time_entry.get(),
            'hold_pause': self.hold_pause_entry.get(),
            'hold_mode': self.hold_mode.get(),
            'is_topmost': self.is_topmost,
            'selected_preset': self.selected_preset,
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
                mode_val = cfg['hold_mode']
                if "Interval" in mode_val:
                    mode_val = "Interval Hold"
                self.hold_mode.set(mode_val)
                self._on_hold_mode_change(mode_val)

            if 'is_topmost' in cfg:
                self.is_topmost = cfg['is_topmost']
                self.attributes("-topmost", self.is_topmost)

            if 'selected_preset' in cfg:
                self.selected_preset = cfg['selected_preset']

            if cfg.get('ac_target'):
                des = deserialize_input(cfg['ac_target'])
                if des:
                    self.ac_target = des
                    self.ac_target_btn.configure(text=f"[{des['display']}]  (Click to Set)")

            if cfg.get('hold_target'):
                des = deserialize_input(cfg['hold_target'])
                if des:
                    self.hold_target = des
                    self.hold_target_btn.configure(text=f"[{des['display']}]  (Click to Set)")

            if cfg.get('ac_hotkey'):
                des = deserialize_input(cfg['ac_hotkey'])
                if des:
                    self.ac_hotkey = des
                    self.ac_hotkey_btn.configure(text=f"[{des['display']}]  (Click to Set)")

            if cfg.get('hold_hotkey'):
                des = deserialize_input(cfg['hold_hotkey'])
                if des:
                    self.hold_hotkey = des
                    self.hold_hotkey_btn.configure(text=f"[{des['display']}]  (Click to Set)")

        except Exception:
            pass

    def _on_close(self):
        self._save_config()
        self.destroy()

    # --- ЗАПИСЬ НАЖАТИЙ КЛАВИШ ---
    def _start_binding(self, mode):
        if self.binding_mode is not None:
            return

        self.binding_mode = mode
        self.bind_start_time = time.time() + 0.35
        self._set_binding_buttons_state("disabled")

        btn_text = ">> PRESS ANY KEY / MOUSE <<"
        if mode == 'ac_target':
            self.ac_target_btn.configure(text=btn_text, fg_color="#F59E0B")
        elif mode == 'hold_target':
            self.hold_target_btn.configure(text=btn_text, fg_color="#F59E0B")
        elif mode == 'ac_hotkey':
            self.ac_hotkey_btn.configure(text=">> PRESS HOTKEY <<", fg_color="#F59E0B")
        elif mode == 'hold_hotkey':
            self.hold_hotkey_btn.configure(text=">> PRESS HOTKEY <<", fg_color="#F59E0B")

    def _set_binding_buttons_state(self, state):
        self.ac_target_btn.configure(state=state)
        self.hold_target_btn.configure(state=state)
        self.ac_hotkey_btn.configure(state=state)
        self.hold_hotkey_btn.configure(state=state)

    def _on_mouse_click(self, x, y, button, pressed):
        if not pressed or not self.binding_mode:
            return

        if time.time() < self.bind_start_time:
            return

        if self.binding_mode in ['ac_target', 'hold_target']:
            btn_str = str(button).split('.')[-1].upper()

            if btn_str == "LEFT":
                display = "LMB"
            elif btn_str == "RIGHT":
                display = "RMB"
            elif btn_str == "MIDDLE":
                display = "MMB"
            elif btn_str == "X1":
                display = "Mouse 4 (Back)"
            elif btn_str == "X2":
                display = "Mouse 5 (Forward)"
            else:
                display = f"Mouse ({btn_str})"

            data = {'type': 'mouse', 'button': button, 'display': display}
            self._finalize_binding(data)

    def _on_key_press(self, key):
        if self.binding_mode:
            display_str = ""
            char_key = None

            if hasattr(key, 'vk') and key.vk in NUMPAD_VK_MAP:
                display_str = NUMPAD_VK_MAP[key.vk]
                char_key = key
            elif hasattr(key, 'char') and key.char:
                raw_char = key.char
                eng_char = RU_TO_EN.get(raw_char, raw_char).upper()
                display_str = eng_char
                char_key = eng_char.lower()
            else:
                display_str = str(key).replace("Key.", "").upper()
                char_key = key

            data = {'type': 'keyboard', 'key': char_key, 'display': display_str}
            self._finalize_binding(data)
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
        if self.binding_mode == 'ac_target':
            self.ac_target = data
            self.ac_target_btn.configure(text=f"[{data['display']}]  (Click to Set)", fg_color="#2563EB")
        elif self.binding_mode == 'hold_target':
            self.hold_target = data
            self.hold_target_btn.configure(text=f"[{data['display']}]  (Click to Set)", fg_color="#059669")
        elif self.binding_mode == 'ac_hotkey':
            if data['type'] == 'mouse':
                self._set_binding_buttons_state("normal")
                self.binding_mode = None
                return
            self.ac_hotkey = data
            self.ac_hotkey_btn.configure(text=f"[{data['display']}]  (Click to Set)", fg_color="#475569")
        elif self.binding_mode == 'hold_hotkey':
            if data['type'] == 'mouse':
                self._set_binding_buttons_state("normal")
                self.binding_mode = None
                return
            self.hold_hotkey = data
            self.hold_hotkey_btn.configure(text=f"[{data['display']}]  (Click to Set)", fg_color="#475569")

        self.binding_mode = None
        self._set_binding_buttons_state("normal")
        self._save_config()

    # --- ТРИГГЕРЫ СТАРТА / СТОПА ---
    def toggle_autoclicker(self):
        if self.hold_active: return
        self.clicker_active = not self.clicker_active
        if self.clicker_active:
            self.ac_status_lbl.configure(text="Status: ACTIVE", text_color="#10B981")
            threading.Thread(target=self._autoclick_loop, daemon=True).start()
        else:
            self.ac_status_lbl.configure(text="Status: STOPPED", text_color="#EF4444")

    def toggle_hold(self):
        if self.clicker_active: return
        self.hold_active = not self.hold_active
        if self.hold_active:
            self.hold_status_lbl.configure(text="Status: ACTIVE", text_color="#10B981")
            threading.Thread(target=self._hold_loop, daemon=True).start()
        else:
            self.hold_status_lbl.configure(text="Status: STOPPED", text_color="#EF4444")

    # --- РАБОЧИЕ ЦИКЛЫ ---
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