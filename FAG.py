import sys
import re
import time
import requests

try:
    import ipywidgets as widgets
    from IPython.display import display, clear_output
    from playwright.sync_api import sync_playwright
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ipywidgets", "playwright"])
    subprocess.check_call(["playwright", "install", "chromium", "--with-deps"])
    import ipywidgets as widgets
    from IPython.display import display, clear_output
    from playwright.sync_api import sync_playwright

BASE_URL = "https://hdmn.cloud"
CONFIG_URL = "https://safeclick.email/faq/vpn/vpn-installation-and-configuration/third-party-applications/wireguard-for-windows/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

# --- ИНТЕРФЕЙС ---

email_input = widgets.Text(placeholder="vash_mail@gmail.com", layout=widgets.Layout(width='280px'))
btn_send_email = widgets.Button(description="1. Запросить код", button_style="primary", icon="paper-plane", layout=widgets.Layout(width='180px'))
output_step1 = widgets.Output(layout=widgets.Layout(margin='5px 0 0 0'))

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
        ("Hungary, Budapest DEMO", "Hungary"),
        ("Belgium, Brussels DEMO", "Belgium"),
        ("Greece, Thessaloniki DEMO", "Greece"),
        ("Latvia, Riga DEMO", "Latvia"),
        ("Netherlands, Amsterdam DEMO", "Netherlands"),
        ("Slovenia, Ljubljana DEMO", "Slovenia"),
        ("United Kingdom, London DEMO", "United Kingdom")
    ],
    value="Hungary",
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

        print("🚀 Запускаем Headless Chromium (Playwright)...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                print("⏳ Загружаем страницу генератора...")
                page.goto(CONFIG_URL, wait_until="networkidle", timeout=30000)

                print("⏳ Вводим код доступа...")
                # Ввод кода в инпут
                input_field = page.locator("input[placeholder*='Код'], input[type='text']").first
                input_field.fill(code)

                # Нажатие на кнопку "Продолжить"
                btn_continue = page.locator("button:has-text('Продолжить'), a:has-text('Продолжить')").first
                btn_continue.click()

                print("⏳ Выполняем JS-валидацию (4 сек)...")
                time.sleep(4)

                # Выбор элементов из Dropdown, если они появились
                selects = page.locator("select")
                if selects.count() >= 2:
                    selects.nth(0).select_option(label=re.compile(version_select.value, re.I))
                    selects.nth(1).select_option(label=re.compile(location_select.value, re.I))

                print("⏳ Нажимаем «Создать конфиг»...")
                btn_create = page.locator("button:has-text('Создать конфиг'), a:has-text('Создать конфиг')").first
                btn_create.click()

                time.sleep(3)

                # Достаем результат из textarea или предпросмотра
                config_box = page.locator("textarea").first
                config_text = config_box.input_value() or config_box.inner_text()

                if "[Interface]" in config_text or "PrivateKey" in config_text:
                    config_text = re.sub(r"AllowedIPs\s*=.*", "AllowedIPs = 0.0.0.0/1, 128.0.0.0/1", config_text)
                    print("\n🎉 ГОТОВЫЙ КОНФИГ:\n")
                    print(config_text)
                else:
                    print("⚠️ Не удалось получить конфиг из формы. Проверь код.")

                browser.close()

        except Exception as e:
            print(f"❌ Ошибка Playwright: {e}")

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
