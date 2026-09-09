import sys
import re
import requests

try:
    import ipywidgets as widgets
    from IPython.display import display, clear_output
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ipywidgets"])
    import ipywidgets as widgets
    from IPython.display import display, clear_output

# Основные параметры
BASE_URL = "https://hdmn.cloud"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/ru/demo/"
}

# --- ЭЛЕМЕНТЫ ИНТЕРФЕЙСА ---

# Шаг 1: Запрос кода
email_input = widgets.Text(placeholder="vash_mail@gmail.com", layout=widgets.Layout(width='280px'))
btn_send_email = widgets.Button(description="1. Запросить код", button_style="primary", icon="paper-plane", layout=widgets.Layout(width='180px'))

# Шаг 2: Генерация конфига
code_input = widgets.Text(placeholder="Вставь код из письма", layout=widgets.Layout(width='280px'))
version_select = widgets.Dropdown(
    options=[
        ("AmneziaWG 2.0 (С обфускацией)", "amnezia_2"),
        ("AmneziaWG 1.0 (С обфускацией)", "amnezia_1")
    ],
    value="amnezia_2",
    layout=widgets.Layout(width='280px')
)
location_select = widgets.Dropdown(
    options=[
        ("Hungary, Budapest DEMO", "hu"),
        ("Belgium, Brussels DEMO", "be"),
        ("Greece, Thessaloniki DEMO", "gr"),
        ("Latvia, Riga DEMO", "lv"),
        ("Netherlands, Amsterdam DEMO", "nl"),
        ("Slovenia, Ljubljana DEMO", "si"),
        ("United Kingdom, London DEMO", "gb")
    ],
    value="hu",
    layout=widgets.Layout(width='280px')
)
btn_gen_config = widgets.Button(description="2. Создать конфиг", button_style="success", icon="key", layout=widgets.Layout(width='180px'))

# Область вывода логов и результата
output_area = widgets.Output(layout=widgets.Layout(margin='10px 0 0 0'))

# --- ЛОГИКА СЕРИАЛИЗАЦИИ И ЗАПРОСОВ ---

def send_email_request(b):
    with output_area:
        clear_output()
        email = email_input.value.strip()
        if not email:
            print("❌ Введи почту!")
            return
        
        print("⏳ Отправляем запрос на получение кода...")
        try:
            res = requests.post(
                f"{BASE_URL}/ru/demo/success/",
                data={"demo_mail": email},
                headers=HEADERS,
                timeout=10
            )
            res.encoding = 'utf-8'
            if res.status_code == 200 and ("Ваш код" in res.text or "уже в пути" in res.text):
                print("✅ Код отправлен! Проверь почтовый ящик, вставь код в поле ниже.")
            else:
                print("⚠️ Сайт отклонил запрос. Возможно, почта уже использовалась.")
        except Exception as e:
            print(f"❌ Ошибка сети: {e}")

def generate_config_request(b):
    with output_area:
        clear_output()
        code = code_input.value.strip()
        if not code:
            print("❌ Введи код из письма!")
            return

        print("⏳ Подключаемся к серверу генерации конфига...")
        try:
            payload = {
                "code": code,
                "preset": version_select.value,
                "server": location_select.value,
                "download": "1"
            }
            
            res = requests.post(f"{BASE_URL}/ru/demo/vpn-config/", data=payload, headers=HEADERS, timeout=12)
            res.encoding = 'utf-8'

            if res.status_code == 200 and ("[Interface]" in res.text or "PrivateKey" in res.text):
                config_text = res.text
                
                # Подмена AllowedIPs для полного обхода
                config_text = re.sub(
                    r"AllowedIPs\s*=.*",
                    "AllowedIPs = 0.0.0.0/1, 128.0.0.0/1",
                    config_text
                )
                
                print("🎉 ГОТОВЫЙ КОНФИГ:\n")
                print(config_text)
            else:
                print("⚠️ Не удалось получить конфиг. Проверь верность кода или выбранную локацию.")
        except Exception as e:
            print(f"❌ Ошибка при отправке: {e}")

btn_send_email.on_click(send_email_request)
btn_gen_config.on_click(generate_config_request)

# --- ВЕРСТКА КРАСИВОГО ИНТЕРФЕЙСА ---

header_widget = widgets.HTML("""
<div style="background-color: #1e1e2e; padding: 15px; border-radius: 8px; font-family: sans-serif; margin-bottom: 15px;">
    <h2 style="color: #cba6f7; margin: 0 0 5px 0;">🚀 FREE ACCESS GRABBER (FAG)</h2>
    <p style="color: #a6adc8; margin: 0; font-size: 13px;">Генератор конфигураций AmneziaWG / WireGuard</p>
</div>
""")

step1_box = widgets.VBox([
    widgets.HTML("<b>Шаг 1: Запрос тестового кода</b>"),
    widgets.HBox([email_input, btn_send_email])
], layout=widgets.Layout(padding='10px', border='1px solid #313244', border_radius='6px', margin='0 0 10px 0'))

step2_box = widgets.VBox([
    widgets.HTML("<b>Шаг 2: Сборка конфига AmneziaWG</b>"),
    widgets.HBox([code_input, version_select]),
    widgets.HBox([location_select, btn_gen_config])
], layout=widgets.Layout(padding='10px', border='1px solid #313244', border_radius='6px'))

warning_widget = widgets.HTML("""
<div style="background-color: #311b1b; border-left: 4px solid #f38ba8; padding: 10px 15px; border-radius: 4px; margin-top: 15px; font-family: sans-serif;">
    <b style="color: #f38ba8;">📌 Важное при завершении:</b>
    <ul style="color: #cdd6f4; margin: 5px 0 0 0; padding-left: 20px; font-size: 12px;">
        <li>Нажми иконку корзины <b>🗑️</b> у ячейки.</li>
        <li>Выбери: <b>Среда выполнения 🡢 Отключиться от среды выполнения и удалить её</b> (защитит Google-аккаунт).</li>
    </ul>
</div>
""")

# Отрисовка приложения
display(header_widget, step1_box, step2_box, output_area, warning_widget)
