import sys
import re
import requests

try:
    import ipywidgets as widgets
    from IPython.display import display, clear_output
    import nest_asyncio
    from playwright.async_api import async_playwright
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ipywidgets", "playwright", "nest_asyncio"])
    subprocess.check_call(["playwright", "install", "chromium", "--with-deps"])
    import ipywidgets as widgets
    from IPython.display import display, clear_output
    import nest_asyncio
    from playwright.async_api import async_playwright

# Разрешаем вложенный asyncio в Jupyter/Colab
nest_asyncio.apply()

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
            html = res.text

            if "запрошен ранее" in html or "уже высылали" in html:
                print("⚠️ Код на эту почту уже запрашивался ранее!")
            elif "не подходит" in html or "одноразовые" in html:
                print("❌ Данная почта заблокирована сервисом.")
            elif res.status_code == 200:
                print("✅ Код отправлен! Проверь ящик.")
            else:
                print(f"⚠️ Статус сервера: {res.status_code}")
        except Exception as e:
            print(f"❌ Ошибка сети: {e}")

async def run_browser_automation(code):
    print("🚀 Запускаем браузер...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=HEADERS["User-Agent"])
        page = await context.new_page()

        try:
            print("⏳ Открываем страницу генератора...")
            await page.goto(CONFIG_URL, wait_until="domcontentloaded", timeout=20000)

            print("⏳ Ищем поле ввода...")
            # Находим первое доступное текстовое поле
            input_elem = page.locator("input[type='text'], input:not([type])").first
            await input_elem.fill(code)

            print("⏳ Нажимаем кнопку отправки кода...")
            # Кликаем по любой кнопке рядом с инпутом или с типом submit
            submit_btn = page.locator("button, input[type='submit']").first
            await submit_btn.click()

            print("⏳ Ожидание генерации (5 сек)...")
            await page.wait_for_timeout(5000)

            # Получаем весь текст страницы или содержимое textarea
            content = await page.content()
            textareas = page.locator("textarea")

            config_text = ""
            if await textareas.count() > 0:
                config_text = await textareas.first.input_value()

            if not config_text:
                config_text = await page.evaluate("() => document.body.innerText")

            if "[Interface]" in config_text or "PrivateKey" in config_text:
                match = re.search(r"\[Interface\][\s\S]*?(?=\n\n|\Z|</textarea>)", config_text)
                final_config = match.group(0) if match else config_text
                final_config = re.sub(r"AllowedIPs\s*=.*", "AllowedIPs = 0.0.0.0/1, 128.0.0.0/1", final_config)
                print("\n🎉 ГОТОВЫЙ КОНФИГ:\n")
                print(final_config)
            else:
                print("❌ Не удалось найти конфиг в ответе страницы.")
                print(f"Превью страницы: {config_text[:300]}...")

        except Exception as err:
            print(f"❌ Ошибка во время работы браузера: {err}")
        finally:
            await browser.close()

def generate_config_request(b):
    with output_step2:
        clear_output()
        code = code_input.value.strip()
        if not code:
            print("❌ Введи код из письма!")
            return

        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_browser_automation(code))

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
