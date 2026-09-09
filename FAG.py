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

async def run_browser_automation(code, version_val, location_val):
    print("🚀 Запускаем Headless Chromium...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=HEADERS["User-Agent"])
        page = await context.new_page()

        try:
            print("⏳ Загружаем страницу инструкций...")
            await page.goto(CONFIG_URL, wait_until="networkidle", timeout=30000)

            # Точный поиск инпута кода доступа (исключаем строку поиска сайта)
            print("⏳ Ищем поле ввода кода доступа...")
            input_field = page.locator("input[placeholder*='код' i], input[placeholder*='code' i], input[name*='code' i]").first
            
            if await input_field.count() == 0:
                # Если с фолбэком — берем инпут, у которого рядом есть кнопка "Продолжить" / "Далее"
                input_field = page.locator("form input[type='text'], .content input[type='text']").first

            await input_field.fill(code)

            print("⏳ Нажимаем «Продолжить»...")
            btn_continue = page.locator("button:has-text('Продолжить'), input[value*='Продолжить']").first
            if await btn_continue.count() > 0:
                await btn_continue.click()
            else:
                # Нажимаем Enter в поле
                await input_field.press("Enter")

            print("⏳ Ожидание прохождения проверки / загрузки параметров (5 сек)...")
            await page.wait_for_timeout(5000)

            # Селекты версии и локации
            selects = page.locator("select")
            if await selects.count() >= 2:
                print(f"⚙️ Выбираем версию ({version_val}) и локацию ({location_val})...")
                try:
                    await selects.nth(0).select_option(label=re.compile(version_val, re.I))
                    await selects.nth(1).select_option(label=re.compile(location_val, re.I))
                except Exception as s_err:
                    print(f"⚠️ Ошибка при выборе из списка (используем по умолчанию): {s_err}")

            print("⏳ Нажимаем «Создать конфиг»...")
            btn_create = page.locator("button:has-text('Создать'), input[value*='Создать']").first
            if await btn_create.count() > 0:
                await btn_create.click()
                await page.wait_for_timeout(4000)

            # Пробуем вытащить конфиг из textarea или из блока кода
            config_text = ""
            textareas = page.locator("textarea")
            if await textareas.count() > 0:
                config_text = await textareas.first.input_value() or await textareas.first.inner_text()

            if not config_text or "[Interface]" not in config_text:
                config_text = await page.evaluate("() => document.body.innerText")

            # Делаем скриншот для отладки
            await page.screenshot(path="debug_page.png")

            if "[Interface]" in config_text or "PrivateKey" in config_text:
                match = re.search(r"\[Interface\][\s\S]*?(?=\n\n|\Z|</textarea>)", config_text)
                final_config = match.group(0) if match else config_text
                final_config = re.sub(r"AllowedIPs\s*=.*", "AllowedIPs = 0.0.0.0/1, 128.0.0.0/1", final_config)
                print("\n🎉 ГОТОВЫЙ КОНФИГ:\n")
                print(final_config)
            else:
                print("❌ Конфиг не найден в теле страницы.")
                print("📸 Скриншот сохранен в файлы Colab (`debug_page.png`).")

        except Exception as err:
            print(f"❌ Ошибка Playwright: {err}")
            await page.screenshot(path="debug_error.png")
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
        loop.run_until_complete(run_browser_automation(
            code, 
            version_select.value, 
            location_select.value
        ))

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
