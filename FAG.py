import sys
import re
import time
import requests

# Проверка и установка зависимостей
try:
    import ipywidgets as widgets
    from IPython.display import display, clear_output
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    import subprocess
    subprocess.check_call(["apt-get", "update", "-y", "-q"])
    subprocess.check_call(["apt-get", "install", "-y", "-q", "chromium-chromedriver"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ipywidgets", "selenium"])
    import ipywidgets as widgets
    from IPython.display import display, clear_output
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://hdmn.cloud"
CONFIG_URL = "https://safeclick.email/faq/vpn/vpn-installation-and-configuration/third-party-applications/wireguard-for-windows/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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

        print("⏳ Настраиваем фоновый браузер Chrome...")
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(CONFIG_URL)
            wait = WebDriverWait(driver, 15)

            print("⏳ Находим поле кода и жмем «Продолжить»...")
            input_box = wait.until(EC.presence_of_element_locator((By.XPATH, "//input[contains(@placeholder, 'Код доступа')] | //input[@type='text']")))
            input_box.clear()
            input_box.send_keys(code)

            btn_continue = driver.find_element(By.XPATH, "//button[contains(text(), 'Продолжить')] | //a[contains(text(), 'Продолжить')]")
            btn_continue.click()

            print("⏳ Ждем появления селекторов (3 сек)...")
            time.sleep(3.5)

            # Выбор дропдаунов на JS-странице
            selects = driver.find_elements(By.TAG_NAME, "select")
            if len(selects) >= 2:
                # 1. Версия
                sel_ver = Select(selects[0])
                for opt in sel_ver.options:
                    if version_select.value in opt.text:
                        sel_ver.select_by_visible_text(opt.text)
                        break
                
                # 2. Локация
                sel_loc = Select(selects[1])
                for opt in sel_loc.options:
                    if location_select.value in opt.text:
                        sel_loc.select_by_visible_text(opt.text)
                        break

            btn_create = driver.find_element(By.XPATH, "//button[contains(text(), 'Создать конфиг')] | //a[contains(text(), 'Создать конфиг')]")
            btn_create.click()

            print("⏳ Сборка конфига...")
            time.sleep(2)

            textarea = wait.until(EC.presence_of_element_locator((By.TAG_NAME, "textarea")))
            config_text = textarea.get_attribute("value") or textarea.text

            if "Interface" in config_text or "PrivateKey" in config_text:
                config_text = re.sub(r"AllowedIPs\s*=.*", "AllowedIPs = 0.0.0.0/1, 128.0.0.0/1", config_text)
                print("🎉 ГОТОВЫЙ КОНФИГ:\n")
                print(config_text)
            else:
                print("⚠️ Поле конфига пустое. Проверь верность кода доступа.")

        except Exception as e:
            print(f"❌ Ошибка эмуляции браузера: {e}")
        finally:
            if driver:
                driver.quit()

btn_send_email.on_click(send_email_request)
btn_gen_config.on_click(generate_config_request)

# --- ВЕРСТКА ---

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
