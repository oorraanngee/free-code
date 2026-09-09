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

BASE_URL = "https://hdmn.cloud"
CONFIG_URL = "https://safeclick.email/faq/vpn/vpn-installation-and-configuration/third-party-applications/wireguard-for-windows/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": CONFIG_URL
}

# --- ИНТЕРФЕЙС ---

# Шаг 1
email_input = widgets.Text(placeholder="vash_mail@gmail.com", layout=widgets.Layout(width='280px'))
btn_send_email = widgets.Button(description="1. Запросить код", button_style="primary", icon="paper-plane", layout=widgets.Layout(width='180px'))
output_step1 = widgets.Output(layout=widgets.Layout(margin='5px 0 0 0'))

# Шаг 2
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
output_step2 = widgets.Output(layout=widgets.Layout(margin='5px 0 0 0'))

# --- ЛОГИКА ---

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
            print(f"🔹 Статус ответа сервера: {res.status_code}")
            if res.status_code == 200:
                print("✅ Запрос отправлен! Проверь почту и скопируй код в Шаг 2.")
            else:
                print(f"⚠️ Ошибка сервера: {res.status_code}")
        except Exception as e:
            print(f"❌ Ошибка сети: {e}")

def generate_config_request(b):
    with output_step2:
        clear_output()
        code = code_input.value.strip()
        if not code:
            print("❌ Введи код из письма!")
            return

        session = requests.Session()
        session.headers.update(HEADERS)

        print("🔍 [DEBUG] 1. Загружаем страницу генератора...")
        try:
            get_res = session.get(CONFIG_URL, timeout=10)
            get_res.encoding = 'utf-8'
            print(f"🔹 HTML загружен. Статус: {get_res.status_code}")

            # Парсим все скрытые input поля на странице
            hidden_inputs = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*>', get_res.text)
            form_data = {}
            for inp in hidden_inputs:
                name_match = re.search(r'name=["\']([^"\']+)["\']', inp)
                val_match = re.search(r'value=["\']([^"\']*)["\']', inp)
                if name_match:
                    name = name_match.group(1)
                    val = val_match.group(1) if val_match else ""
                    form_data[name] = val
            
            print(f"🔹 Найденные скрытые токены формы: {form_data}")

            # Ищем правильное имя поля для ввода кода
            code_input_name = "code"
            input_matches = re.findall(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*>', get_res.text)
            for name in input_matches:
                if "code" in name.lower() or "demo" in name.lower() or "key" in name.lower():
                    code_input_name = name
                    break

            print(f"🔹 Используем имя поля для кода: '{code_input_name}'")
            
            # Собираем финальный набор данных для отправки
            form_data[code_input_name] = code
            form_data["preset"] = version_select.value
            form_data["server"] = location_select.value

            print("🔍 [DEBUG] 2. Отправляем заполненную форму на сервер...")
            post_res = session.post(CONFIG_URL, data=form_data, timeout=12)
            post_res.encoding = 'utf-8'

            print(f"🔹 Статус ответа после POST: {post_res.status_code}")
            print(f"🔹 Заголовки ответа Content-Type: {post_res.headers.get('Content-Type')}")

            raw_text = post_res.text

            # Проверка наличия файла конфигурации
            if "[Interface]" in raw_text or "PrivateKey" in raw_text:
                config_text = raw_text
                # Если ответ обернут в HTML/Textarea, вырезаем чистый конфиг
                match = re.search(r"\[Interface\][\s\S]*?(?=\n\n|\Z|</textarea>)", raw_text)
                if match:
                    config_text = match.group(0)

                config_text = re.sub(r"AllowedIPs\s*=.*", "AllowedIPs = 0.0.0.0/1, 128.0.0.0/1", config_text)
                print("\n🎉 ГОТОВЫЙ КОНФИГ:\n")
                print(config_text)
            else:
                print("\n❌ [ОШИБКА GENERATION] Конфиг не найден в ответе!")
                print("--- ПЕРВЫЕ 600 СИМВОЛОВ ОТВЕТА СЕРВЕРА ---")
                # Очищаем от лишних пробелов для читаемости
                clean_preview = re.sub(r'\s+', ' ', raw_text[:600])
                print(clean_preview)
                print("---------------------------------------")

        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")

btn_send_email.on_click(send_email_request)
btn_gen_config.on_click(generate_config_request)

# --- ИНТЕРФЕЙС ---

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
        <li>Выбери: <b>Среда выполнения 🡢 Отключиться от среды выполнения и удалить её</b>.</li>
    </ul>
</div>
""")

display(header_widget, step1_box, step2_box, warning_widget)
