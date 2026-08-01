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


def disable_maximize_button(window):
    """ Completely disables the Maximize button via Windows API """
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()
        GWL_STYLE = -16
        WS_MAXIMIZEBOX = 0x00010000
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
        style &= ~WS_MAXIMIZEBOX
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)
    except Exception:
        pass


# --- 23+ LANGUAGES LOCALIZATION ---
LANG_MAPPING = {
    "English": "EN",
    "Русский": "RU",
    "Español": "ES",
    "Deutsch": "DE",
    "Français": "FR",
    "中文": "ZH",
    "日本語": "JA",
    "한국어": "KO",
    "Português": "PT",
    "Italiano": "IT",
    "Polski": "PL",
    "Türkçe": "TR",
    "Українська": "UK",
    "Nederlands": "NL",
    "العربية": "AR",
    "हिन्दी": "HI",
    "Tiếng Việt": "VI",
    "ไทย": "TH",
    "Bahasa Indonesia": "ID",
    "Čeština": "CS",
    "Magyar": "HU",
    "Română": "RO",
    "Svenska": "SV"
}

CODE_TO_LANG = {v: k for k, v in LANG_MAPPING.items()}

TRANSLATIONS = {
    'EN': {
        'settings': ' Settings', 'settings_title': 'Settings', 'app_settings': 'Application Settings',
        'always_on_top': 'Always on Top', 'app_theme': 'App Theme:', 'app_lang': 'Language:', 'close': 'Close',
        'theme_dark': 'Dark', 'theme_light': 'Light', 'theme_system': 'System',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Click Target:', 'click_interval': 'Click Interval (ms):',
        'random_offset': 'Random Offset (± ms):', 'hotkey': 'Global Start/Stop Hotkey:', 'hold_mode': '✊ HOLD MODE',
        'hold_target': 'Hold Target:', 'hold_type': 'Hold Type:', 'hold_duration': 'Hold Duration (sec):',
        'pause_interval': 'Pause Interval (sec):', 'status_stopped': 'Status: STOPPED', 'status_active': 'Status: ACTIVE',
        'click_to_set': 'Click to Set', 'press_key_mouse': '>> PRESS ANY KEY / MOUSE <<', 'press_hotkey': '>> PRESS HOTKEY <<',
        'continuous_hold': 'Continuous Hold', 'interval_hold': 'Interval Hold'
    },
    'RU': {
        'settings': ' Настройки', 'settings_title': 'Настройки', 'app_settings': 'Настройки приложения',
        'always_on_top': 'Поверх всех окон', 'app_theme': 'Тема оформления:', 'app_lang': 'Язык интерфейса:', 'close': 'Закрыть',
        'theme_dark': 'Тёмная', 'theme_light': 'Светлая', 'theme_system': 'Системная',
        'autoclicker': '⚡ АВТОКЛИКЕР', 'click_target': 'Цель клика:', 'click_interval': 'Интервал клика (мс):',
        'random_offset': 'Разброс (± мс):', 'hotkey': 'Горячая клавиша:', 'hold_mode': '✊ РЕЖИМ УДЕРЖАНИЯ',
        'hold_target': 'Цель зажатия:', 'hold_type': 'Тип зажатия:', 'hold_duration': 'Длительность (сек):',
        'pause_interval': 'Пауза (сек):', 'status_stopped': 'Статус: ОСТАНОВЛЕН', 'status_active': 'Статус: АКТИВЕН',
        'click_to_set': 'Клик для выбора', 'press_key_mouse': '>> НАЖМИТЕ КЛАВИШУ / МЫШЬ <<', 'press_hotkey': '>> НАЖМИТЕ ХОТКЕЙ <<',
        'continuous_hold': 'Зажатие', 'interval_hold': 'Интервальное зажатие'
    },
    'ES': {
        'settings': ' Ajustes', 'settings_title': 'Ajustes', 'app_settings': 'Ajustes de la aplicación',
        'always_on_top': 'Siempre visible', 'app_theme': 'Tema:', 'app_lang': 'Idioma:', 'close': 'Cerrar',
        'theme_dark': 'Oscuro', 'theme_light': 'Claro', 'theme_system': 'Sistema',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Objetivo del clic:', 'click_interval': 'Intervalo (ms):',
        'random_offset': 'Variación (± ms):', 'hotkey': 'Tecla de inicio/paro:', 'hold_mode': '✊ MODO MANTENER',
        'hold_target': 'Objetivo de pulsación:', 'hold_type': 'Tipo de pulsación:', 'hold_duration': 'Duración (seg):',
        'pause_interval': 'Pausa (seg):', 'status_stopped': 'Estado: DETENIDO', 'status_active': 'Estado: ACTIVO',
        'click_to_set': 'Clic para definir', 'press_key_mouse': '>> PRESIONE TECLA / MOUSE <<', 'press_hotkey': '>> PRESIONE TECLA <<',
        'continuous_hold': 'Pulsación continua', 'interval_hold': 'Pulsación por intervalos'
    },
    'DE': {
        'settings': ' Einstellungen', 'settings_title': 'Einstellungen', 'app_settings': 'Anwendungseinstellungen',
        'always_on_top': 'Immer im Vordergrund', 'app_theme': 'Design:', 'app_lang': 'Sprache:', 'close': 'Schließen',
        'theme_dark': 'Dunkel', 'theme_light': 'Hell', 'theme_system': 'System',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Klick-Ziel:', 'click_interval': 'Klick-Intervall (ms):',
        'random_offset': 'Zufalls-Offset (± ms):', 'hotkey': 'Start/Stopp Hotkey:', 'hold_mode': '✊ HALTE-MODUS',
        'hold_target': 'Halte-Ziel:', 'hold_type': 'Halte-Typ:', 'hold_duration': 'Dauer (Sek):',
        'pause_interval': 'Pause (Sek):', 'status_stopped': 'Status: GESTOPPT', 'status_active': 'Status: AKTIV',
        'click_to_set': 'Klick zum Festlegen', 'press_key_mouse': '>> TASTE / MAUS DRÜCKEN <<', 'press_hotkey': '>> HOTKEY DRÜCKEN <<',
        'continuous_hold': 'Dauerhaftes Halten', 'interval_hold': 'Intervall-Halten'
    },
    'FR': {
        'settings': ' Options', 'settings_title': 'Options', 'app_settings': "Paramètres de l'application",
        'always_on_top': 'Toujours au-dessus', 'app_theme': 'Thème:', 'app_lang': 'Langue:', 'close': 'Fermer',
        'theme_dark': 'Sombre', 'theme_light': 'Clair', 'theme_system': 'Système',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Cible du clic:', 'click_interval': 'Intervalle (ms):',
        'random_offset': 'Décalage (± ms):', 'hotkey': 'Raccourci Début/Fin:', 'hold_mode': '✊ MODE MAINTIEN',
        'hold_target': 'Cible de maintien:', 'hold_type': 'Type de maintien:', 'hold_duration': 'Durée (sec):',
        'pause_interval': 'Pause (sec):', 'status_stopped': 'Statut: ARRÊTÉ', 'status_active': 'Statut: ACTIF',
        'click_to_set': 'Cliquer pour régler', 'press_key_mouse': '>> APPUYER TOUCHE / SOURIS <<', 'press_hotkey': '>> APPUYER RACCOURCI <<',
        'continuous_hold': 'Maintien continu', 'interval_hold': 'Maintien par intervalle'
    },
    'ZH': {
        'settings': ' 设置', 'settings_title': '设置', 'app_settings': '应用程序设置',
        'always_on_top': '窗口置顶', 'app_theme': '主题:', 'app_lang': '语言:', 'close': '关闭',
        'theme_dark': '深色', 'theme_light': '浅色', 'theme_system': '跟随系统',
        'autoclicker': '⚡ 自动点击器', 'click_target': '点击目标:', 'click_interval': '点击间隔 (毫秒):',
        'random_offset': '随机偏差 (± 毫秒):', 'hotkey': '全局启动/停止热键:', 'hold_mode': '✊ 长按模式',
        'hold_target': '长按目标:', 'hold_type': '长按类型:', 'hold_duration': '持续时间 (秒):',
        'pause_interval': '暂停间隔 (秒):', 'status_stopped': '状态: 已停止', 'status_active': '状态: 运行中',
        'click_to_set': '点击设置', 'press_key_mouse': '>> 请按下任意按键或鼠标 <<', 'press_hotkey': '>> 请按下热键 <<',
        'continuous_hold': '连续长按', 'interval_hold': '间隔长按'
    },
    'JA': {
        'settings': ' 設定', 'settings_title': '設定', 'app_settings': 'アプリ設定',
        'always_on_top': '最前線に表示', 'app_theme': 'テーマ:', 'app_lang': '言語:', 'close': '閉じる',
        'theme_dark': 'ダーク', 'theme_light': 'ライト', 'theme_system': 'システム',
        'autoclicker': '⚡ オートクリッカー', 'click_target': 'クリック対象:', 'click_interval': '間隔 (ミリ秒):',
        'random_offset': 'ランダム偏差 (± ms):', 'hotkey': '開始/停止ホットキー:', 'hold_mode': '✊ ホールドモード',
        'hold_target': 'ホールド対象:', 'hold_type': 'ホールドタイプ:', 'hold_duration': '保持時間 (秒):',
        'pause_interval': '停止時間 (秒):', 'status_stopped': 'ステータス: 停止中', 'status_active': 'ステータス: 動作中',
        'click_to_set': 'クリックして設定', 'press_key_mouse': '>> キーまたはマウスを押してください <<', 'press_hotkey': '>> ホットキーを押してください <<',
        'continuous_hold': '継続ホールド', 'interval_hold': 'インターバルホールド'
    },
    'KO': {
        'settings': ' 설정', 'settings_title': '설정', 'app_settings': '애플리케이션 설정',
        'always_on_top': '항상 위', 'app_theme': '테마:', 'app_lang': '언어:', 'close': '닫기',
        'theme_dark': '다크', 'theme_light': '라이트', 'theme_system': '시스템',
        'autoclicker': '⚡ 오토클리커', 'click_target': '클릭 대상:', 'click_interval': '클릭 간격 (ms):',
        'random_offset': '무작위 오차 (± ms):', 'hotkey': '시작/중지 단축키:', 'hold_mode': '✊ 홀드 모드',
        'hold_target': '홀드 대상:', 'hold_type': '홀드 유형:', 'hold_duration': '유지 시간 (초):',
        'pause_interval': '일시중지 (초):', 'status_stopped': '상태: 정지됨', 'status_active': '상태: 작동 중',
        'click_to_set': '클릭하여 설정', 'press_key_mouse': '>> 키 또는 마우스를 누르세요 <<', 'press_hotkey': '>> 단축키를 누르세요 <<',
        'continuous_hold': '연속 홀드', 'interval_hold': '간격 홀드'
    },
    'PT': {
        'settings': ' Configurações', 'settings_title': 'Configurações', 'app_settings': 'Configurações do Aplicativo',
        'always_on_top': 'Sempre no topo', 'app_theme': 'Tema:', 'app_lang': 'Idioma:', 'close': 'Fechar',
        'theme_dark': 'Escuro', 'theme_light': 'Claro', 'theme_system': 'Sistema',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Alvo do clique:', 'click_interval': 'Intervalo (ms):',
        'random_offset': 'Variação (± ms):', 'hotkey': 'Atalho Iniciar/Parar:', 'hold_mode': '✊ MODO MANTER',
        'hold_target': 'Alvo da pressão:', 'hold_type': 'Tipo de pressão:', 'hold_duration': 'Duração (seg):',
        'pause_interval': 'Pausa (seg):', 'status_stopped': 'Status: PARADO', 'status_active': 'Status: ATIVO',
        'click_to_set': 'Clique para definir', 'press_key_mouse': '>> PRESSIONE TECLA / MOUSE <<', 'press_hotkey': '>> PRESSIONE O ATALHO <<',
        'continuous_hold': 'Pressão contínua', 'interval_hold': 'Pressão por intervalo'
    },
    'IT': {
        'settings': ' Impostazioni', 'settings_title': 'Impostazioni', 'app_settings': "Impostazioni dell'applicazione",
        'always_on_top': 'Sempre in primo piano', 'app_theme': 'Tema:', 'app_lang': 'Lingua:', 'close': 'Chiudi',
        'theme_dark': 'Scuro', 'theme_light': 'Chiaro', 'theme_system': 'Sistema',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Obiettivo click:', 'click_interval': 'Intervallo (ms):',
        'random_offset': 'Variazione (± ms):', 'hotkey': 'Tasto Avvio/Arresto:', 'hold_mode': '✊ MODALITÀ PRESSIONE',
        'hold_target': 'Obiettivo pressione:', 'hold_type': 'Tipo pressione:', 'hold_duration': 'Durata (sec):',
        'pause_interval': 'Pausa (sec):', 'status_stopped': 'Stato: FERMATO', 'status_active': 'Stato: ATTIVO',
        'click_to_set': 'Clicca per impostare', 'press_key_mouse': '>> PREMI UN TASTO / MOUSE <<', 'press_hotkey': '>> PREMI IL TASTO RAPIDO <<',
        'continuous_hold': 'Pressione continua', 'interval_hold': 'Pressione a intervalli'
    },
    'PL': {
        'settings': ' Ustawienia', 'settings_title': 'Ustawienia', 'app_settings': 'Ustawienia aplikacji',
        'always_on_top': 'Zawsze na wierzchu', 'app_theme': 'Motyw:', 'app_lang': 'Język:', 'close': 'Zamknij',
        'theme_dark': 'Ciemny', 'theme_light': 'Jasny', 'theme_system': 'Systemowy',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Cel kliknięcia:', 'click_interval': 'Interwał (ms):',
        'random_offset': 'Odchylenie (± ms):', 'hotkey': 'Skrót Start/Stop:', 'hold_mode': '✊ TRYB PRZYTRZYMANIA',
        'hold_target': 'Cel przytrzymania:', 'hold_type': 'Typ przytrzymania:', 'hold_duration': 'Czas trwania (sek):',
        'pause_interval': 'Pauza (sek):', 'status_stopped': 'Status: ZATRZYMANY', 'status_active': 'Status: AKTYWNY',
        'click_to_set': 'Kliknij, aby ustawić', 'press_key_mouse': '>> NACIŚNIJ KLAWISZ / MYSZ <<', 'press_hotkey': '>> NACIŚNIJ SKRÓT <<',
        'continuous_hold': 'Ciągłe przytrzymanie', 'interval_hold': 'Interwałowe przytrzymanie'
    },
    'TR': {
        'settings': ' Ayarlar', 'settings_title': 'Ayarlar', 'app_settings': 'Uygulama Ayarları',
        'always_on_top': 'Her zaman üstte', 'app_theme': 'Tema:', 'app_lang': 'Dil:', 'close': 'Kapat',
        'theme_dark': 'Karanlık', 'theme_light': 'Aydınlık', 'theme_system': 'Sistem',
        'autoclicker': '⚡ OTOMATİK TIKLAYICI', 'click_target': 'Tıklama Hedefi:', 'click_interval': 'Aralık (ms):',
        'random_offset': 'Rastgele Sapma (± ms):', 'hotkey': 'Başlat/Durdur Kısayolu:', 'hold_mode': '✊ BASILI TUTMA MODU',
        'hold_target': 'Tutma Hedefi:', 'hold_type': 'Tutma Türü:', 'hold_duration': 'Süre (sn):',
        'pause_interval': 'Duraklatma (sn):', 'status_stopped': 'Durum: DURDURULDU', 'status_active': 'Durum: AKTİF',
        'click_to_set': 'Ayarlamak için tıkla', 'press_key_mouse': '>> TUŞA VEYA FAREYE BASIN <<', 'press_hotkey': '>> KISAYOL TUŞUNA BASIN <<',
        'continuous_hold': 'Sürekli Tutma', 'interval_hold': 'Aralıklı Tutma'
    },
    'UK': {
        'settings': ' Налаштування', 'settings_title': 'Налаштування', 'app_settings': 'Налаштування програми',
        'always_on_top': 'Поверх усіх вікон', 'app_theme': 'Тема:', 'app_lang': 'Мова:', 'close': 'Закрити',
        'theme_dark': 'Темна', 'theme_light': 'Світла', 'theme_system': 'Системна',
        'autoclicker': '⚡ АВТОКЛІКЕР', 'click_target': 'Ціль кліку:', 'click_interval': 'Інтервал кліку (мс):',
        'random_offset': 'Розкид (± мс):', 'hotkey': 'Гаряча клавіша:', 'hold_mode': '✊ РЕЖИМ УТРИМАННЯ',
        'hold_target': 'Ціль утримання:', 'hold_type': 'Тип утримання:', 'hold_duration': 'Тривалість (сек):',
        'pause_interval': 'Пауза (сек):', 'status_stopped': 'Статус: ЗУПИНЕНО', 'status_active': 'Статус: АКТИВНИЙ',
        'click_to_set': 'Клік для вибору', 'press_key_mouse': '>> НАТИСНІТЬ КЛАВІШУ / МИШУ <<', 'press_hotkey': '>> НАТИСНІТЬ ХОТКЕЙ <<',
        'continuous_hold': 'Утримання', 'interval_hold': 'Інтервальне утримання'
    },
    'NL': {
        'settings': ' Instellingen', 'settings_title': 'Instellingen', 'app_settings': 'Applicatie-instellingen',
        'always_on_top': 'Altijd bovenaan', 'app_theme': 'Thema:', 'app_lang': 'Taal:', 'close': 'Sluiten',
        'theme_dark': 'Donker', 'theme_light': 'Licht', 'theme_system': 'Systeem',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Klikdoel:', 'click_interval': 'Interval (ms):',
        'random_offset': 'Willekeurige afwijking (± ms):', 'hotkey': 'Start/Stop Sneltoets:', 'hold_mode': '✊ VASTHOUDMODUS',
        'hold_target': 'Vasthoud-doel:', 'hold_type': 'Vasthoud-type:', 'hold_duration': 'Duur (sec):',
        'pause_interval': 'Pauze (sec):', 'status_stopped': 'Status: GESTOPT', 'status_active': 'Status: ACTIEF',
        'click_to_set': 'Klik om in te stellen', 'press_key_mouse': '>> DRUK OP EEN TOETS / MUIS <<', 'press_hotkey': '>> DRUK OP SNELTOETS <<',
        'continuous_hold': 'Continu vasthouden', 'interval_hold': 'Interval vasthouden'
    },
    'AR': {
        'settings': ' الإعدادات', 'settings_title': 'الإعدادات', 'app_settings': 'إعدادات التطبيق',
        'always_on_top': 'دائماً في المقدمة', 'app_theme': 'المظهر:', 'app_lang': 'اللغة:', 'close': 'إغلاق',
        'theme_dark': 'داكن', 'theme_light': 'فاتح', 'theme_system': 'النظام',
        'autoclicker': '⚡ النقر التلقائي', 'click_target': 'هدف النقر:', 'click_interval': 'الفترة (مللي ثانية):',
        'random_offset': 'تفاوت عشوائي (± مللي ثانية):', 'hotkey': 'مفتاح البدء/الإيقاف:', 'hold_mode': '✊ وضع الضغط المستمر',
        'hold_target': 'هدف الضغط:', 'hold_type': 'نوع الضغط:', 'hold_duration': 'المدة (ثانية):',
        'pause_interval': 'إيقاف مؤقت (ثانية):', 'status_stopped': 'الحالة: متوقف', 'status_active': 'الحالة: نشط',
        'click_to_set': 'انقر للتعيين', 'press_key_mouse': '>> اضغط على أي زر أو الماوس <<', 'press_hotkey': '>> اضغط على مفتاح الاختصار <<',
        'continuous_hold': 'ضغط مستمر', 'interval_hold': 'ضغط متقطع'
    },
    'HI': {
        'settings': ' सेटिंग्स', 'settings_title': 'सेटिंग्स', 'app_settings': 'ऐप सेटिंग्स',
        'always_on_top': 'हमेशा ऊपर रखें', 'app_theme': 'थीम:', 'app_lang': 'भाषा:', 'close': 'बंद करें',
        'theme_dark': 'डार्क', 'theme_light': 'लाइट', 'theme_system': 'सिस्टम',
        'autoclicker': '⚡ ऑटोक्लीकर', 'click_target': 'क्लिक लक्ष्य:', 'click_interval': 'अंतराल (ms):',
        'random_offset': 'यादृच्छिक अंतर (± ms):', 'hotkey': 'शुरू/रोकें हॉटकी:', 'hold_mode': '✊ होल्ड मोड',
        'hold_target': 'होल्ड लक्ष्य:', 'hold_type': 'होल्ड प्रकार:', 'hold_duration': 'अवधि (सेकंड):',
        'pause_interval': 'विराम (सेकंड):', 'status_stopped': 'स्थिति: रुका हुआ', 'status_active': 'स्थिति: सक्रिय',
        'click_to_set': 'सेट करने के लिए क्लिक करें', 'press_key_mouse': '>> कोई कुंजी या माउस दबाएं <<', 'press_hotkey': '>> हॉटकी दबाएं <<',
        'continuous_hold': 'निरंतर होल्ड', 'interval_hold': 'अंतराल होल्ड'
    },
    'VI': {
        'settings': ' Cài đặt', 'settings_title': 'Cài đặt', 'app_settings': 'Cài đặt ứng dụng',
        'always_on_top': 'Luôn trên cùng', 'app_theme': 'Giao diện:', 'app_lang': 'Ngôn ngữ:', 'close': 'Đóng',
        'theme_dark': 'Tối', 'theme_light': 'Sáng', 'theme_system': 'Hệ thống',
        'autoclicker': '⚡ TỰ ĐỘNG CLICK', 'click_target': 'Mục tiêu click:', 'click_interval': 'Khoảng thời gian (ms):',
        'random_offset': 'Độ lệch ngẫu nhiên (± ms):', 'hotkey': 'Phím tắt Bắt đầu/Dừng:', 'hold_mode': '✊ CHẾ ĐỘ GIỮ PHÍM',
        'hold_target': 'Mục tiêu giữ:', 'hold_type': 'Loại giữ phím:', 'hold_duration': 'Thời gian giữ (giây):',
        'pause_interval': 'Tạm dừng (giây):', 'status_stopped': 'Trạng thái: ĐÃ DỪNG', 'status_active': 'Trạng thái: HOẠT ĐỘNG',
        'click_to_set': 'Nhấp để cài đặt', 'press_key_mouse': '>> NHẤN PHÍM BẤT KỲ / CHUỘT <<', 'press_hotkey': '>> NHẤN PHÍM TẮT <<',
        'continuous_hold': 'Giữ liên tục', 'interval_hold': 'Giữ theo khoảng'
    },
    'TH': {
        'settings': ' การตั้งค่า', 'settings_title': 'การตั้งค่า', 'app_settings': 'การตั้งค่าแอปพลิเคชัน',
        'always_on_top': 'แสดงอยู่ด้านบนเสมอ', 'app_theme': 'ธีม:', 'app_lang': 'ภาษา:', 'close': 'ปิด',
        'theme_dark': 'มืด', 'theme_light': 'สว่าง', 'theme_system': 'ระบบ',
        'autoclicker': '⚡ ออโต้คลิกเกอร์', 'click_target': 'เป้าหมายการคลิก:', 'click_interval': 'ช่วงเวลา (ms):',
        'random_offset': 'ค่าเบี่ยงเบน (± ms):', 'hotkey': 'ปุ่มลัด เริ่ม/หยุด:', 'hold_mode': '✊ โหมดกดค้าง',
        'hold_target': 'เป้าหมายการกดค้าง:', 'hold_type': 'รูปแบบการกดค้าง:', 'hold_duration': 'ระยะเวลากด (วินาที):',
        'pause_interval': 'หยุดพัก (วินาที):', 'status_stopped': 'สถานะ: หยุดทำงาน', 'status_active': 'สถานะ: กำลังทำงาน',
        'click_to_set': 'คลิกเพื่อตั้งค่า', 'press_key_mouse': '>> กดปุ่มใดก็ได้ หรือคลิกเมาส์ <<', 'press_hotkey': '>> กดปุ่มลัด <<',
        'continuous_hold': 'กดค้างต่อเนื่อง', 'interval_hold': 'กดค้างเป็นระยะ'
    },
    'ID': {
        'settings': ' Pengaturan', 'settings_title': 'Pengaturan', 'app_settings': 'Pengaturan Aplikasi',
        'always_on_top': 'Selalu di atas', 'app_theme': 'Tema:', 'app_lang': 'Bahasa:', 'close': 'Tutup',
        'theme_dark': 'Gelap', 'theme_light': 'Terang', 'theme_system': 'Sistem',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Target Klik:', 'click_interval': 'Interval (ms):',
        'random_offset': 'Variasi Acak (± ms):', 'hotkey': 'Pintasan Mulai/Berhenti:', 'hold_mode': '✊ MODE TAHAN',
        'hold_target': 'Target Tahan:', 'hold_type': 'Jenis Tahan:', 'hold_duration': 'Durasi (detik):',
        'pause_interval': 'Jeda (detik):', 'status_stopped': 'Status: BERHENTI', 'status_active': 'Status: AKTIF',
        'click_to_set': 'Klik untuk mengatur', 'press_key_mouse': '>> TEKAN TOMBOL / TETIKUS <<', 'press_hotkey': '>> TEKAN TOMBOL PINTASAN <<',
        'continuous_hold': 'Tahan Terus', 'interval_hold': 'Tahan Berinterval'
    },
    'CS': {
        'settings': ' Nastavení', 'settings_title': 'Nastavení', 'app_settings': 'Nastavení aplikace',
        'always_on_top': 'Vždy navrchu', 'app_theme': 'Motiv:', 'app_lang': 'Jazyk:', 'close': 'Zavřít',
        'theme_dark': 'Tmavý', 'theme_light': 'Světlý', 'theme_system': 'Systémový',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Cíl kliknutí:', 'click_interval': 'Interval (ms):',
        'random_offset': 'Náhodná odchylka (± ms):', 'hotkey': 'Klávesa Start/Stop:', 'hold_mode': '✊ REŽIM DRŽENÍ',
        'hold_target': 'Cíl držení:', 'hold_type': 'Typ držení:', 'hold_duration': 'Doba (sec):',
        'pause_interval': 'Pauza (sec):', 'status_stopped': 'Stav: ZASTAVENO', 'status_active': 'Stav: AKTIVNÍ',
        'click_to_set': 'Klikněte pro nastavení', 'press_key_mouse': '>> STISKNĚTE KLÁVESU / MYŠ <<', 'press_hotkey': '>> STISKNĚTE KLÁVESU <<',
        'continuous_hold': 'Souvislé držení', 'interval_hold': 'Intervalové držení'
    },
    'HU': {
        'settings': ' Beállítások', 'settings_title': 'Beállítások', 'app_settings': 'Alkalmazás beállításai',
        'always_on_top': 'Mindig felül', 'app_theme': 'Téma:', 'app_lang': 'Nyelv:', 'close': 'Bezárás',
        'theme_dark': 'Sötét', 'theme_light': 'Világos', 'theme_system': 'Rendszer',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Kattintás célpontja:', 'click_interval': 'Intervallum (ms):',
        'random_offset': 'Véletlenszerű eltérés (± ms):', 'hotkey': 'Indítás/Leállítás billentyű:', 'hold_mode': '✊ NYOMVATARTÁSI MÓD',
        'hold_target': 'Nyomvatartás célpontja:', 'hold_type': 'Nyomvatartás típusa:', 'hold_duration': 'Időtartam (mp):',
        'pause_interval': 'Szünet (mp):', 'status_stopped': 'Állapot: LEÁLLÍTVA', 'status_active': 'Állapot: AKTÍV',
        'click_to_set': 'Kattints a beállításhoz', 'press_key_mouse': '>> NYOMJ MEG EGY BILLENTYŰT / EGÉR <<', 'press_hotkey': '>> NYOMD MEG A GYORSBILLENTYŰT <<',
        'continuous_hold': 'Folyamatos nyomvatartás', 'interval_hold': 'Szakaszos nyomvatartás'
    },
    'RO': {
        'settings': ' Setări', 'settings_title': 'Setări', 'app_settings': 'Setările aplicației',
        'always_on_top': 'Mereu deasupra', 'app_theme': 'Temă:', 'app_lang': 'Limbă:', 'close': 'Închide',
        'theme_dark': 'Întunecat', 'theme_light': 'Luminos', 'theme_system': 'Sistem',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Țintă clic:', 'click_interval': 'Interval (ms):',
        'random_offset': 'Abatere aleatorie (± ms):', 'hotkey': 'Tastă Pornire/Oprire:', 'hold_mode': '✊ MOD MENȚINERE',
        'hold_target': 'Țintă menținere:', 'hold_type': 'Tip menținere:', 'hold_duration': 'Durată (sec):',
        'pause_interval': 'Pauză (sec):', 'status_stopped': 'Stare: OPRIT', 'status_active': 'Stare: ACTIV',
        'click_to_set': 'Apasă pentru a seta', 'press_key_mouse': '>> APASĂ O TASTĂ / MAUSUL <<', 'press_hotkey': '>> APASĂ TASTA RAPIDĂ <<',
        'continuous_hold': 'Menținere continuă', 'interval_hold': 'Menținere la intervale'
    },
    'SV': {
        'settings': ' Inställningar', 'settings_title': 'Inställningar', 'app_settings': 'Applikationsinställningar',
        'always_on_top': 'Alltid överst', 'app_theme': 'Tema:', 'app_lang': 'Språk:', 'close': 'Stäng',
        'theme_dark': 'Mörkt', 'theme_light': 'Ljust', 'theme_system': 'System',
        'autoclicker': '⚡ AUTOCLICKER', 'click_target': 'Klickmål:', 'click_interval': 'Intervall (ms):',
        'random_offset': 'Slumpmässig avvikelse (± ms):', 'hotkey': 'Start/Stopp Snabbknapp:', 'hold_mode': '✊ HÅLL-LÄGE',
        'hold_target': 'Håll-mål:', 'hold_type': 'Håll-typ:', 'hold_duration': 'Varaktighet (sek):',
        'pause_interval': 'Paus (sek):', 'status_stopped': 'Status: STOPPAD', 'status_active': 'Status: AKTIV',
        'click_to_set': 'Klicka för att ställa in', 'press_key_mouse': '>> TRYCK PÅ EN TANGENT / MUS <<', 'press_hotkey': '>> TRYCK PÅ SNABBKNAPP <<',
        'continuous_hold': 'Kontinuerlig hållning', 'interval_hold': 'Intervallhållning'
    }
}


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
    'й': 'Q', 'ц': 'W', 'у': 'E', 'к': 'R', 'е': 'T', 'н': 'Y', 'г': 'U', 'ш': 'I', 'щ': 'O', 'з': 'P', 'х': '[', 'ъ': ']',
    'ф': 'A', 'ы': 'S', 'в': 'D', 'а': 'F', 'п': 'G', 'р': 'H', 'о': 'J', 'л': 'K', 'д': 'L', 'ж': ';', 'э': "'",
    'я': 'Z', 'ч': 'X', 'с': 'C', 'м': 'V', 'и': 'B', 'т': 'N', 'ь': 'M', 'б': ',', 'ю': '.',
    'Й': 'Q', 'Ц': 'W', 'У': 'E', 'К': 'R', 'Е': 'T', 'Н': 'Y', 'Г': 'U', 'Ш': 'I', 'Щ': 'O', 'З': 'P', 'Х': '[', 'Ъ': ']',
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
        self.title(parent.tr('settings_title'))
        self.geometry("340x280")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        set_window_icon(self)
        disable_maximize_button(self)
        self.grid_columnconfigure(0, weight=1)

        self.title_lbl = ctk.CTkLabel(self, text=parent.tr('app_settings'), font=("Arial", 16, "bold"), text_color=("#0F172A", "#F3F4F6"))
        self.title_lbl.pack(pady=12)

        self.topmost_var = ctk.BooleanVar(value=parent.is_topmost)
        self.topmost_cb = ctk.CTkCheckBox(self, text=parent.tr('always_on_top'), variable=self.topmost_var, command=self._toggle_topmost, text_color=("#0F172A", "#F3F4F6"))
        self.topmost_cb.pack(pady=8, anchor="w", padx=30)

        self.theme_lbl = ctk.CTkLabel(self, text=parent.tr('app_theme'), font=("Arial", 12), text_color=("#0F172A", "#F3F4F6"))
        self.theme_lbl.pack(pady=(6, 2), anchor="w", padx=30)

        # Localized theme choices
        theme_choices = [parent.tr('theme_dark'), parent.tr('theme_light'), parent.tr('theme_system')]
        self.theme_opt = ctk.CTkOptionMenu(
            self, values=theme_choices, command=self._apply_theme,
            fg_color=("#E2E8F0", "#2B2D31"), button_color=("#CBD5E1", "#3F4147"),
            button_hover_color=("#94A3B8", "#4E5058"), text_color=("#0F172A", "#F3F4F6")
        )
        self.theme_opt.set(parent.get_localized_theme_name(parent.appearance_mode))
        self.theme_opt.pack(pady=2, fill="x", padx=30)

        self.lang_lbl = ctk.CTkLabel(self, text=parent.tr('app_lang'), font=("Arial", 12), text_color=("#0F172A", "#F3F4F6"))
        self.lang_lbl.pack(pady=(8, 2), anchor="w", padx=30)

        self.lang_opt = ctk.CTkOptionMenu(
            self, values=list(LANG_MAPPING.keys()), command=self._apply_language,
            fg_color=("#E2E8F0", "#2B2D31"), button_color=("#CBD5E1", "#3F4147"),
            button_hover_color=("#94A3B8", "#4E5058"), text_color=("#0F172A", "#F3F4F6")
        )
        self.lang_opt.set(CODE_TO_LANG.get(parent.language, "English"))
        self.lang_opt.pack(pady=2, fill="x", padx=30)

        self.close_btn = ctk.CTkButton(
            self, text=parent.tr('close'), command=self.destroy,
            fg_color=("#2563EB", "#3B82F6"), hover_color=("#1D4ED8", "#2563EB"), text_color="#FFFFFF"
        )
        self.close_btn.pack(pady=15)

    def _toggle_topmost(self):
        val = self.topmost_var.get()
        self.parent.is_topmost = val
        self.parent.attributes("-topmost", val)
        self.parent._save_config()

    def _apply_theme(self, choice):
        # Convert localized theme choice back to internal CTk theme string
        internal_theme = self.parent.parse_theme_from_choice(choice)
        self.parent.appearance_mode = internal_theme
        ctk.set_appearance_mode(internal_theme)
        self.parent._save_config()

    def _apply_language(self, choice):
        lang_code = LANG_MAPPING.get(choice, "EN")
        self.parent.language = lang_code
        self.parent.update_ui_language()

        # Update Settings Window text
        self.title(self.parent.tr('settings_title'))
        self.title_lbl.configure(text=self.parent.tr('app_settings'))
        self.topmost_cb.configure(text=self.parent.tr('always_on_top'))
        self.theme_lbl.configure(text=self.parent.tr('app_theme'))
        self.lang_lbl.configure(text=self.parent.tr('app_lang'))
        self.close_btn.configure(text=self.parent.tr('close'))

        # Dynamically update theme dropdown values to new language
        new_theme_choices = [self.parent.tr('theme_dark'), self.parent.tr('theme_light'), self.parent.tr('theme_system')]
        self.theme_opt.configure(values=new_theme_choices)
        self.theme_opt.set(self.parent.get_localized_theme_name(self.parent.appearance_mode))

        self.parent._save_config()


class EasyClicker(ctk.CTk):
    def __init__(self):
        super().__init__()

        # DEFAULT LANGUAGE IS ENGLISH
        self.language = "EN"
        self.title("EasyClicker")
        self.geometry("820x490")
        self.maxsize(820, 490)

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

    def tr(self, key):
        """ Get localized string with fallback to EN """
        return TRANSLATIONS.get(self.language, TRANSLATIONS['EN']).get(key, '')

    def get_localized_theme_name(self, internal_mode):
        mode = str(internal_mode).lower()
        if mode == "light":
            return self.tr('theme_light')
        elif mode == "system":
            return self.tr('theme_system')
        return self.tr('theme_dark')

    def parse_theme_from_choice(self, choice):
        if choice == self.tr('theme_light'):
            return "Light"
        elif choice == self.tr('theme_system'):
            return "System"
        return "Dark"

    def _deferred_init(self):
        set_window_icon(self)
        disable_maximize_button(self)
        self._load_config()

        self.kb_listener = keyboard.Listener(on_press=self._on_key_press)
        self.kb_listener.start()

        self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self.mouse_listener.start()

    def _build_ui(self):
        self.header = ctk.CTkFrame(self, height=36, corner_radius=0, fg_color="transparent")

        gear_img = create_gear_icon(size=(16, 16))

        self.settings_btn = ctk.CTkButton(
            self.header, text=self.tr('settings'), image=gear_img, compound="left",
            width=90, fg_color=("#E2E8F0", "#2B2D31"), hover_color=("#CBD5E1", "#3F4147"),
            text_color=("#0F172A", "#F3F4F6"), command=self._open_settings
        )

        self.title_label = ctk.CTkLabel(self.header, text="EasyClicker", font=("Arial", 16, "bold"), text_color=("#0F172A", "#F3F4F6"))

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")

        entry_kwargs = {
            "fg_color": ("#FFFFFF", "#1E1F22"),
            "border_color": ("#94A3B8", "#3F4147"),
            "border_width": 1,
            "text_color": ("#0F172A", "#F3F4F6")
        }

        # === AUTOCLICKER ===
        self.ac_frame = ctk.CTkFrame(self.main_container, corner_radius=12, fg_color=("#FFFFFF", "#2B2D31"), border_color=("#CBD5E1", "#3F4147"), border_width=1)
        self.ac_frame.grid_columnconfigure(0, weight=1)

        self.ac_title_lbl = ctk.CTkLabel(self.ac_frame, text=self.tr('autoclicker'), font=("Arial", 15, "bold"), text_color=("#1D4ED8", "#60A5FA"))
        self.ac_title_lbl.grid(row=0, column=0, pady=(10, 5))

        self.ac_target_lbl = ctk.CTkLabel(self.ac_frame, text=self.tr('click_target'), font=("Arial", 11, "bold"), text_color=("#0F172A", "#F3F4F6"))
        self.ac_target_lbl.grid(row=1, column=0, pady=(2, 1), sticky="w", padx=15)

        self.ac_target_btn = ctk.CTkButton(
            self.ac_frame, text=f"[{self.ac_target['display']}]  ({self.tr('click_to_set')})",
            fg_color="#2563EB", hover_color="#1D4ED8", text_color="#FFFFFF",
            command=lambda: self._start_binding('ac_target')
        )
        self.ac_target_btn.grid(row=2, column=0, padx=15, pady=3, sticky="ew")

        self.ac_interval_lbl = ctk.CTkLabel(self.ac_frame, text=self.tr('click_interval'), font=("Arial", 10), text_color=("#334155", "#CBD5E1"))
        self.ac_interval_lbl.grid(row=3, column=0, pady=(4, 0), sticky="w", padx=15)

        self.ac_interval = ctk.CTkEntry(self.ac_frame, placeholder_text="100", **entry_kwargs)
        self.ac_interval.insert(0, "100")
        self.ac_interval.grid(row=4, column=0, padx=15, pady=1, sticky="ew")

        self.ac_offset_lbl = ctk.CTkLabel(self.ac_frame, text=self.tr('random_offset'), font=("Arial", 10), text_color=("#334155", "#CBD5E1"))
        self.ac_offset_lbl.grid(row=5, column=0, pady=(4, 0), sticky="w", padx=15)

        self.ac_offset = ctk.CTkEntry(self.ac_frame, placeholder_text="20", **entry_kwargs)
        self.ac_offset.insert(0, "20")
        self.ac_offset.grid(row=6, column=0, padx=15, pady=1, sticky="ew")

        self.ac_hotkey_lbl = ctk.CTkLabel(self.ac_frame, text=self.tr('hotkey'), font=("Arial", 11, "bold"), text_color=("#0F172A", "#F3F4F6"))
        self.ac_hotkey_lbl.grid(row=7, column=0, pady=(6, 1), sticky="w", padx=15)

        self.ac_hotkey_btn = ctk.CTkButton(
            self.ac_frame, text=f"[{self.ac_hotkey['display']}]  ({self.tr('click_to_set')})",
            fg_color=("#E2E8F0", "#3F4147"), hover_color=("#CBD5E1", "#4E5058"),
            text_color=("#0F172A", "#F3F4F6"), command=lambda: self._start_binding('ac_hotkey')
        )
        self.ac_hotkey_btn.grid(row=8, column=0, padx=15, pady=3, sticky="ew")

        self.ac_status_lbl = ctk.CTkLabel(self.ac_frame, text=self.tr('status_stopped'), text_color=("#DC2626", "#EF4444"), font=("Arial", 12, "bold"))
        self.ac_status_lbl.grid(row=99, column=0, pady=(6, 8))

        # === HOLD MODE ===
        self.hold_frame = ctk.CTkFrame(self.main_container, corner_radius=12, fg_color=("#FFFFFF", "#2B2D31"), border_color=("#CBD5E1", "#3F4147"), border_width=1)
        self.hold_frame.grid_columnconfigure(0, weight=1)

        self.hold_title_lbl = ctk.CTkLabel(self.hold_frame, text=self.tr('hold_mode'), font=("Arial", 15, "bold"), text_color=("#059669", "#34D399"))
        self.hold_title_lbl.grid(row=0, column=0, pady=(10, 5))

        self.hold_target_lbl = ctk.CTkLabel(self.hold_frame, text=self.tr('hold_target'), font=("Arial", 11, "bold"), text_color=("#0F172A", "#F3F4F6"))
        self.hold_target_lbl.grid(row=1, column=0, pady=(2, 1), sticky="w", padx=15)

        self.hold_target_btn = ctk.CTkButton(
            self.hold_frame, text=f"[{self.hold_target['display']}]  ({self.tr('click_to_set')})",
            fg_color="#059669", hover_color="#047857", text_color="#FFFFFF",
            command=lambda: self._start_binding('hold_target')
        )
        self.hold_target_btn.grid(row=2, column=0, padx=15, pady=3, sticky="ew")

        self.hold_mode_lbl = ctk.CTkLabel(self.hold_frame, text=self.tr('hold_type'), font=("Arial", 10), text_color=("#334155", "#CBD5E1"))
        self.hold_mode_lbl.grid(row=3, column=0, pady=(4, 0), sticky="w", padx=15)

        self.hold_mode = ctk.CTkOptionMenu(
            self.hold_frame, values=[self.tr('continuous_hold'), self.tr('interval_hold')],
            fg_color=("#E2E8F0", "#059669"), button_color=("#CBD5E1", "#047857"),
            button_hover_color=("#94A3B8", "#065F46"), text_color=("#0F172A", "#FFFFFF"),
            command=self._on_hold_mode_change
        )
        self.hold_mode.set(self.tr('continuous_hold'))
        self.hold_mode.grid(row=4, column=0, padx=15, pady=1, sticky="ew")

        self.fields_frame = ctk.CTkFrame(self.hold_frame, fg_color="transparent")
        self.fields_frame.grid(row=5, column=0, padx=15, pady=1, sticky="ew")
        self.fields_frame.grid_columnconfigure((0, 1), weight=1)

        self.lbl_hold_time = ctk.CTkLabel(self.fields_frame, text=self.tr('hold_duration'), font=("Arial", 9), text_color=("#334155", "#CBD5E1"))
        self.lbl_hold_time.grid(row=0, column=0, sticky="w")
        self.hold_time_entry = ctk.CTkEntry(self.fields_frame, placeholder_text="2.0", **entry_kwargs)
        self.hold_time_entry.insert(0, "2.0")
        self.hold_time_entry.grid(row=1, column=0, padx=(0, 3), sticky="ew")

        self.lbl_pause_time = ctk.CTkLabel(self.fields_frame, text=self.tr('pause_interval'), font=("Arial", 9), text_color=("#334155", "#CBD5E1"))
        self.lbl_pause_time.grid(row=0, column=1, sticky="w")
        self.hold_pause_entry = ctk.CTkEntry(self.fields_frame, placeholder_text="1.0", **entry_kwargs)
        self.hold_pause_entry.insert(0, "1.0")
        self.hold_pause_entry.grid(row=1, column=1, padx=(3, 0), sticky="ew")

        self._update_hold_fields_visual(enabled=False)

        self.hold_hotkey_lbl = ctk.CTkLabel(self.hold_frame, text=self.tr('hotkey'), font=("Arial", 11, "bold"), text_color=("#0F172A", "#F3F4F6"))
        self.hold_hotkey_lbl.grid(row=7, column=0, pady=(6, 1), sticky="w", padx=15)

        self.hold_hotkey_btn = ctk.CTkButton(
            self.hold_frame, text=f"[{self.hold_hotkey['display']}]  ({self.tr('click_to_set')})",
            fg_color=("#E2E8F0", "#3F4147"), hover_color=("#CBD5E1", "#4E5058"),
            text_color=("#0F172A", "#F3F4F6"), command=lambda: self._start_binding('hold_hotkey')
        )
        self.hold_hotkey_btn.grid(row=8, column=0, padx=15, pady=3, sticky="ew")

        self.hold_status_lbl = ctk.CTkLabel(self.hold_frame, text=self.tr('status_stopped'), text_color=("#DC2626", "#EF4444"), font=("Arial", 12, "bold"))
        self.hold_status_lbl.grid(row=99, column=0, pady=(6, 8))

        self._apply_header_state("full")
        self._apply_grid_state("side_by_side")

    def update_ui_language(self):
        """ Dynamically updates all text labels when language changes """
        self.settings_btn.configure(text=self.tr('settings'))
        self.ac_title_lbl.configure(text=self.tr('autoclicker'))
        self.ac_target_lbl.configure(text=self.tr('click_target'))
        self.ac_interval_lbl.configure(text=self.tr('click_interval'))
        self.ac_offset_lbl.configure(text=self.tr('random_offset'))
        self.ac_hotkey_lbl.configure(text=self.tr('hotkey'))

        self.hold_title_lbl.configure(text=self.tr('hold_mode'))
        self.hold_target_lbl.configure(text=self.tr('hold_target'))
        self.hold_mode_lbl.configure(text=self.tr('hold_type'))
        self.lbl_hold_time.configure(text=self.tr('hold_duration'))
        self.lbl_pause_time.configure(text=self.tr('pause_interval'))
        self.hold_hotkey_lbl.configure(text=self.tr('hotkey'))

        self.ac_target_btn.configure(text=f"[{self.ac_target['display']}]  ({self.tr('click_to_set')})")
        self.ac_hotkey_btn.configure(text=f"[{self.ac_hotkey['display']}]  ({self.tr('click_to_set')})")
        self.hold_target_btn.configure(text=f"[{self.hold_target['display']}]  ({self.tr('click_to_set')})")
        self.hold_hotkey_btn.configure(text=f"[{self.hold_hotkey['display']}]  ({self.tr('click_to_set')})")

        current_val = self.hold_mode.get()
        is_interval = any(kw in current_val for kw in ("Interval", "Интервальное", "interval", "intervalles", "간격", "间隔"))
        self.hold_mode.configure(values=[self.tr('continuous_hold'), self.tr('interval_hold')])
        self.hold_mode.set(self.tr('interval_hold') if is_interval else self.tr('continuous_hold'))

        ac_st_text = self.tr('status_active') if self.clicker_active else self.tr('status_stopped')
        hold_st_text = self.tr('status_active') if self.hold_active else self.tr('status_stopped')
        self.ac_status_lbl.configure(text=ac_st_text)
        self.hold_status_lbl.configure(text=hold_st_text)

    def _on_window_resize(self, event):
        if event.widget != self:
            return

        w, h = event.width, event.height

        new_header_state = "full" if w >= 420 else "minimal"
        new_grid_state = "side_by_side" if w >= 620 else "ac_only"

        if h >= 410:
            new_height_level = 3
        elif h >= 320:
            new_height_level = 2
        else:
            new_height_level = 1

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

        toggle_widgets(ac_hotkey_widgets, level >= 3)
        toggle_widgets(hold_hotkey_widgets, level >= 3)

        toggle_widgets(ac_offset_widgets, level >= 2)
        toggle_widgets(hold_offset_widgets, level >= 2)

    def _open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()

    def _on_hold_mode_change(self, choice):
        is_continuous = any(kw in choice for kw in ("Continuous", "Зажатие", "continu", "Sürekli", "연속", "连续", "निरंतर", "กดค้างต่อเนื่อง"))
        self._update_hold_fields_visual(enabled=not is_continuous)

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
            'language': self.language,
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

            if 'language' in cfg and cfg['language'] in TRANSLATIONS:
                self.language = cfg['language']

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

            self.update_ui_language()

            if 'hold_mode' in cfg:
                is_interval = any(kw in cfg['hold_mode'] for kw in ("Interval", "Интервальное", "interval", "intervalles", "간격", "间隔"))
                val = self.tr('interval_hold') if is_interval else self.tr('continuous_hold')
                self.hold_mode.set(val)
                self._on_hold_mode_change(val)

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
            'ac_target': (self.ac_target_btn, self.tr('press_key_mouse')),
            'hold_target': (self.hold_target_btn, self.tr('press_key_mouse')),
            'ac_hotkey': (self.ac_hotkey_btn, self.tr('press_hotkey')),
            'hold_hotkey': (self.hold_hotkey_btn, self.tr('press_hotkey'))
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
            display_map = {"LEFT": "LMB", "RIGHT": "RMB", "MIDDLE": "MMB", "X1": "Mouse 4 (Back)", "X2": "Mouse 5 (Forward)"}
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
        btn_map[mode].configure(text=f"[{data['display']}]  ({self.tr('click_to_set')})", fg_color=color_map[mode], text_color=txt_color)

        self.binding_mode = None
        self.bind_cooldown = time.time() + 0.1
        self._set_binding_buttons_state("normal")
        self._save_config()

    def toggle_autoclicker(self):
        if self.hold_active: return
        self.clicker_active = not self.clicker_active
        txt, color = (self.tr('status_active'), ("#16A34A", "#10B981")) if self.clicker_active else (self.tr('status_stopped'), ("#DC2626", "#EF4444"))
        self.ac_status_lbl.configure(text=txt, text_color=color)

        if self.clicker_active:
            threading.Thread(target=self._autoclick_loop, daemon=True).start()

    def toggle_hold(self):
        if self.clicker_active: return
        self.hold_active = not self.hold_active
        txt, color = (self.tr('status_active'), ("#16A34A", "#10B981")) if self.hold_active else (self.tr('status_stopped'), ("#DC2626", "#EF4444"))
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
        is_continuous = any(kw in self.hold_mode.get() for kw in ("Continuous", "Зажатие", "continu", "Sürekli", "연속", "连续", "निरंतर", "กดค้างต่อเนื่อง"))

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