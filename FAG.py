import sys
import re
import requests

try:
    import ipywidgets as widgets
    from IPython.display import display, HTML
    import nest_asyncio
    from playwright.async_api import async_playwright
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ipywidgets", "playwright", "nest_asyncio"])
    subprocess.check_call(["playwright", "install", "chromium", "--with-deps"])
    import ipywidgets as widgets
    from IPython.display import display, HTML
    import nest_asyncio
    from playwright.async_api import async_playwright

nest_asyncio.apply()

BASE_URL = "https://hdmn.cloud"
CONFIG_URL = "https://safeclick.email/faq/vpn/vpn-installation-and-configuration/third-party-applications/wireguard-for-windows/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

# --- ИНТЕРФЕЙС ---

email_input = widgets.Text(placeholder="ваша почта", layout=widgets.Layout(width='280px'))
btn_send_email = widgets.Button(description="📤 Запросить код", button_style="primary", icon="paper-plane", layout=widgets.Layout(width='180px'))
output_step1 = widgets.Output(layout=widgets.Layout(margin='5px 0 0 0'))

code_input = widgets.Text(placeholder="Вставь код из письма", layout=widgets.Layout(width='280px'))
version_select = widgets.Dropdown(
    options=[
        ("AmneziaWG 2.0 (рекомендуется)", "2.0"),
        ("AmneziaWG 1.0", "1.0")
    ],
    value="2.0",
    layout=widgets.Layout(width='280px')
)
location_select = widgets.Dropdown(
    options=[
        ("Hungary, Budapest DEMO (рекомендуется)", "Hungary"),
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
btn_gen_config = widgets.Button(description="🔏 Создать конфиг", button_style="success", icon="key", layout=widgets.Layout(width='180px'))
output_step2 = widgets.Output(layout=widgets.Layout(margin='5px 0 0 0'))

# --- ЛОГИКА ---

def send_email_request(b):
    with output_step1:
        output_step1.clear_output()
        email = email_input.value.strip()
        if not email:
            print("📭 Введите почту!")
            return
        
        print("📨 Отправляем запрос на получение кода...")
        try:
            # Используем логику из hidecode.py
            session = requests.Session()
            session.headers.update(HEADERS)
            
            url_demo = f"{BASE_URL}/ru/demo/"
            
            # 1. Сначала GET запрос
            res_get = session.get(url_demo, timeout=10)
            
            if res_get.status_code == 200:
                # 2. Затем POST запрос
                url_success = f"{BASE_URL}/ru/demo/success/"
                res_post = session.post(
                    url_success, 
                    data={"demo_mail": email},
                    headers={"Referer": url_demo},
                    timeout=10
                )
                res_post.encoding = 'utf-8'
                html = res_post.text

                # 3. Строгая проверка результата как в hidecode.py
                if res_post.status_code == 200 and 'Ваш код выслан на почту' in html:
                    print("✅ Ваш код уже в пути! Проверьте свой почтовый ящик.")
                elif res_post.status_code == 200 and ('не подходит' in html or 'одноразовые' in html):
                    print("⚠️ Указанная почта не подходит для получения тестового периода.")
                elif "запрошен ранее" in html or "уже высылали" in html:
                    print("📛 Код на эту почту уже запрашивался ранее!")
                else:
                    print("⛔ Сервер не подтвердил отправку. Возможно, почта в чёрном списке.")
            else:
                print(f"❌ Ошибка доступа к странице демо. Код ответа: {res_get.status_code}")

        except requests.RequestException as e:
            print(f"🌐❌ Ошибка сети: {e}")

async def run_browser_automation(code, version_val, location_val):
    print("🌐 Запускаем Headless Chromium...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=HEADERS["User-Agent"])
        page = await context.new_page()

        try:
            print("⏬ Загружаем страницу...")
            await page.goto(CONFIG_URL, wait_until="networkidle", timeout=30000)

            print("🔓 Раскрываем вкладку «Основной этап»...")
            tab_accordion = page.locator("text=/Основной этап/i").first
            if await tab_accordion.count() > 0:
                await tab_accordion.click()
                await page.wait_for_timeout(1000)

            print("🪪 Вводим код...")
            input_field = page.locator("input[name='code'], input[placeholder*='Код доступа']").first
            if not await input_field.is_visible():
                await input_field.evaluate(f"(el) => {{ el.value = '{code}'; el.dispatchEvent(new Event('input')); }}")
            else:
                await input_field.fill(code)

            print("🔹 Нажимаем «Продолжить»...")
            btn_continue = page.locator("button:has-text('Продолжить'), input[value*='Продолжить'], a:has-text('Продолжить')").first
            if await btn_continue.count() > 0:
                await btn_continue.click(force=True)
            else:
                await input_field.press("Enter")

            print("⏳ Ожидаем прохождения проверки (5 сек)...")
            await page.wait_for_timeout(5000)

            selects = page.locator("select")
            if await selects.count() >= 2:
                print(f"⚙️ Выбираем настройки: Версия = {version_val}, Сервер = {location_val}...")
                try:
                    s1 = selects.nth(0)
                    s2 = selects.nth(1)

                    opts1 = await s1.locator("option").all_inner_texts()
                    for idx, text in enumerate(opts1):
                        if version_val.lower() in text.lower():
                            await s1.select_option(index=idx)
                            break

                    opts2 = await s2.locator("option").all_inner_texts()
                    for idx, text in enumerate(opts2):
                        if location_val.lower() in text.lower():
                            await s2.select_option(index=idx)
                            break
                except Exception as s_err:
                    print(f"⚠️ Ошибка выпадающего списка: {s_err}")

            print("🔏 Генерируем конфиг...")
            btn_create = page.locator("button:has-text('Создать'), input[value*='Создать']").first
            if await btn_create.count() > 0:
                await btn_create.click(force=True)
                await page.wait_for_timeout(4000)

            config_text = ""
            textareas = page.locator("textarea")
            if await textareas.count() > 0:
                config_text = await textareas.first.input_value() or await textareas.first.inner_text()

            if not config_text or "[Interface]" not in config_text:
                config_text = await page.evaluate("() => document.body.innerText")

            if "[Interface]" in config_text and "[Peer]" in config_text:
                match = re.search(r"\[Interface\][\s\S]*?\[Peer\][\s\S]*?(?=\n\n\n|\Z|</textarea>)", config_text)
                final_config = match.group(0).strip() if match else config_text.strip()
                final_config = re.sub(r"AllowedIPs\s*=.*", "AllowedIPs = 0.0.0.0/1, 128.0.0.0/1", final_config)

                print("🔐 Конфигурация успешно получена!")
                
                html_code = f"""
                <div style="margin-top: 15px; font-family: monospace;">
                    <div style="display: flex; justify-content: space-between; align-items: center; background: #282a36; padding: 8px 12px; border-radius: 6px 6px 0 0; color: #f8f8f2;">
                        <b>🔒🔑 ГОТОВЫЙ КОНФИГ:</b>
                        <button onclick="navigator.clipboard.writeText(document.getElementById('config_text_area').value); this.innerText='✅ Скопировано!';" 
                                style="background: #50fa7b; color: #282a36; border: none; padding: 5px 12px; border-radius: 4px; font-weight: bold; cursor: pointer;">
                            📋 Скопировать
                        </button>
                    </div>
                    <textarea id="config_text_area" rows="18" style="width: 100%; background: #1e1e2e; color: #a6adc8; border: 1px solid #44475a; border-radius: 0 0 6px 6px; padding: 10px; font-family: monospace; resize: vertical;">{final_config}</textarea>
                </div>
                """
                display(HTML(html_code))

            else:
                print("🔍 Конфиг не найден на странице.")

        except Exception as err:
            print(f"❌ Ошибка Playwright: {err}")
        finally:
            await browser.close()

def generate_config_request(b):
    with output_step2:
        output_step2.clear_output()
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
    <h2 style="color: #cba6f7; margin: 0 0 5px 0;">📨 FREE ACCESS GRABBER (FAG)</h2>
    <p style="color: #a6adc8; margin: 0; font-size: 13px;">А так же: генератор конфигураций AmneziaWG</p>
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
        <li>Нажмите иконку корзины <b>🗑️</b> у ячейки.</li>
        <li>Выберите: <b>Среда выполнения 🡢 Отключиться от среды выполнения и удалить её</b>.</li>
    </ul>
</div>
""")

display(header_widget, step1_box, step2_box, warning_widget)
