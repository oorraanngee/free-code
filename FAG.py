import sys
import re
import time
import requests

try:
    import ipywidgets as widgets
    from IPython.display import display, clear_output
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ipywidgets"])
    import ipywidgets as widgets
    from IPython.display import display, clear_output

# Основные URL и заголовки
BASE_URL = "https://hdmn.cloud"
CONFIG_URL = "https://safeclick.email/faq/vpn/vpn-installation-and-configuration/third-party-applications/wireguard-for-windows/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# --- ЭЛЕМЕНТЫ ИНТЕРФЕЙСА ---

# Шаг 1: Запрос кода
email_input = widgets.Text(placeholder="vash_mail@gmail.com", layout=widgets.Layout(width='280px'))
btn_send_email = widgets.Button(description="1. Запросить код", button_style="primary", icon="paper-plane", layout=widgets.Layout(width='180px'))
output_step1 = widgets.Output(layout=widgets.Layout(margin='5px 0 0 0'))

# Шаг 2: Генерация конфига
code_input = widgets.Text(placeholder="Вставь код из письма", layout=widgets.Layout(width='280px'))
version_select = widgets.Dropdown(
    options=[
        ("AmneziaWG 2.0 (С обфускацией)", "2.0"),
        ("AmneziaWG 1.0 (С обфускацией)", "1.0")
    ],
    value="2.0",
    layout=widgets.Layout(width='280px')
)
location_select = widgets.Dropdown(
    options=[
        ("Hungary, Budapest DEMO", "hu_bud_demo"),
        ("Belgium, Brussels DEMO", "be_bru_demo"),
        ("Greece, Thessaloniki DEMO", "gr_the_demo"),
        ("Latvia, Riga DEMO", "lv_rig_demo"),
        ("Netherlands, Amsterdam DEMO", "nl_ams_demo"),
        ("Slovenia, Ljubljana DEMO", "si_lju_demo"),
        ("United Kingdom, London DEMO", "gb_lon_demo")
    ],
    value="hu_bud_demo",
    layout=widgets.Layout(width='280px')
)
btn_gen_config = widgets.Button(description="2. Создать конфиг", button_style="success", icon="key", layout=widgets.Layout(width='180px'))
output_step2 = widgets.Output(layout=widgets.Layout(margin='5px 0 0 0'))

# --- ЛОГИКА ЗАПРОСОВ ---

def send_email_request(b):
    with output_step1:
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
                headers={**HEADERS, "Referer": f"{BASE_URL}/ru/demo/"},
                timeout=10
            )
            res.encoding = 'utf-8'
            if res.status_code == 200 and ("Ваш код" in res.text or "уже в пути" in res.text):
                print("✅ Код отправлен! Проверь почту и скопируй его в Шаг 2.")
            else:
                print("⚠️ Сайт отклонил запрос. Возможно, почта уже использовалась.")
        except Exception as e:
            print(f"❌ Ошибка сети: {e}")

def generate_config_request(b):
    with output_step2:
        clear_output()
        code = code_input.value.strip()
        if not code:
            print("❌ Введи код из письма!")
            return

        print("⏳ Этап 1/2: Передаем код доступа на страницу...")
        try:
            session = requests.Session()
            session.headers.update(HEADERS)
            
            # Эмуляция ввода кода на странице
            init_res = session.post(
                CONFIG_URL,
                data={"code": code, "action": "check_code"},
                timeout=10
            )
            
            # Пауза 3 секунды, пока сервис "проверяет" код
            print("⏳ Проверка кода сайтом (ожидание 3 сек)...")
            time.sleep(3)

            print("⏳ Этап 2/2: Запрашиваем конфиг AmneziaWG...")
            payload = {
                "code": code,
                "version": version_select.value,
                "server": location_select.value,
                "generate": "1"
            }
            
            gen_res = session.post(CONFIG_URL, data=payload, timeout=12)
            gen_res.encoding = 'utf-8'

            # Если вернулся полный конфиг
            if gen_res.status_code == 200 and ("Interface" in gen_res.text or "PrivateKey" in gen_res.text):
                config_text = gen_res.text
                
                # Замена AllowedIPs для обхода
                config_text = re.sub(
                    r"AllowedIPs\s*=.*",
                    "AllowedIPs = 0.0.0.0/1, 128.0.0.0/1",
                    config_text
                )
                
                print("🎉 ГОТОВЫЙ КОНФИГ:\n")
                print(config_text)
            else:
                # Если сырой текст конфига спрятан в теге <textarea> или <pre>
                match = re.search(r"\[Interface\][\s\S]*?(?=\n\n|\Z|</textarea>|</pre>)", gen_res.text)
                if match:
                    config_text = match.group(0)
                    config_text = re.sub(r"AllowedIPs\s*=.*", "AllowedIPs = 0.0.0.0/1, 128.0.0.0/1", config_text)
                    print("🎉 ГОТОВЫЙ КОНФИГ:\n")
                    print(config_text)
                else:
                    print("⚠️ Не удалось получить конфиг. Проверь верность кода доступа.")
        except Exception as e:
            print(f"❌ Ошибка при генерации: {e}")

btn_send_email.on_click(send_email_request)
btn_gen_config.on_click(generate_config_request)

# --- ВЕРСТКА С РАЗДЕЛЬНЫМИ ВЫВОДАМИ ---

header_widget = widgets.HTML("""
<div style="background-color: #1e1e2e; padding: 15px; border-radius: 8px; font-family: sans-serif; margin-bottom: 15px;">
    <h2 style="color: #cba6f7; margin: 0 0 5px 0;">🚀 FREE ACCESS GRABBER (FAG)</h2>
    <p style="color: #a6adc8; margin: 0; font-size: 13px;">Генератор конфигураций AmneziaWG / WireGuard</p>
</div>
""")

step1_box = widgets.VBox([
    widgets.HTML("<b>Шаг 1: Запрос тестового кода</b>"),
    widgets.HBox([email_input, btn_send_email]),
    output_step1
], layout=widgets.Layout(padding='10px', border='1px solid #313244', border_radius='6px', margin='0 0 10px 0'))

step2_box = widgets.VBox([
    widgets.HTML("<b>Шаг 2: Сборка конфига AmneziaWG</b>"),
    widgets.HBox([code_input, version_select]),
    widgets.HBox([location_select, btn_gen_config]),
    output_step2
], layout=widgets.Layout(padding='10px', border='1px solid #313244', border_radius='6px'))

warning_widget = widgets.HTML("""
<div style="background-color: #311b1b; border-left: 4px solid #f38ba8; padding: 10px 15px; border-radius: 4px; margin-top: 15px; font-family: sans-serif;">
    <b style="color: #f38ba8;">📌 Важно при завершении:</b>
    <ul style="color: #cdd6f4; margin: 5px 0 0 0; padding-left: 20px; font-size: 12px;">
        <li>Нажми иконку корзины <b>🗑️</b> у ячейки.</li>
        <li>Выбери: <b>Среда выполнения 🡢 Отключиться от среды выполнения и удалить её</b> (защитит Google-аккаунт).</li>
    </ul>
</div>
""")

display(header_widget, step1_box, step2_box, warning_widget)
