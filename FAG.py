import sys
import re
import requests

# Проверяем и устанавливаем ipywidgets для интерактивного интерфейса
try:
    import ipywidgets as widgets
    from IPython.display import display, clear_output
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ipywidgets"])
    import ipywidgets as widgets
    from IPython.display import display, clear_output

BASE_URL = "https://hdmn.cloud"
CONFIG_GEN_URL = "https://safeclick.email/faq/vpn/vpn-installation-and-configuration/third-party-applications/wireguard-for-windows/"

# --- Виджеты интерфейса ---
email_input = widgets.Text(description="Почта:", placeholder="your_email@gmail.com")
btn_send_email = widgets.Button(description="1. Запросить код", button_style="primary", icon="paper-plane")

code_input = widgets.Text(description="Код:", placeholder="Вставь код из письма")
version_select = widgets.Dropdown(
    options=[
        ("С обфускацией (AmneziaWG 2.0 client)", "2.0"),
        ("С обфускацией (AmneziaWG 1.0 client)", "1.0")
    ],
    value="2.0",
    description="Версия:"
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
    description="Локация:"
)
btn_gen_config = widgets.Button(description="2. Создать конфиг", button_style="success", icon="key")

output_area = widgets.Output()

# --- Логика запросов ---

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
                timeout=10
            )
            res.encoding = 'utf-8'
            if res.status_code == 200 and "Ваш код выслан" in res.text:
                print("✅ Код отправлен! Проверь ящик, скопируй его и вставь в поле ниже.")
            else:
                print("⚠️ Ошибка отправки или почта уже использовалась.")
        except Exception as e:
            print(f"❌ Сбой сети: {e}")

def generate_config_request(b):
    with output_area:
        clear_output()
        code = code_input.value.strip()
        if not code:
            print("❌ Введи код из письма!")
            return

        print("⏳ Генерируем конфиг WireGuard/AmneziaWG...")
        try:
            payload = {
                "code": code,
                "version": version_select.value,
                "server": location_select.value
            }
            res = requests.post(CONFIG_GEN_URL, data=payload, timeout=12)
            res.encoding = 'utf-8'

            if res.status_code == 200 and "Interface" in res.text:
                # Меняем строчку AllowedIPs на нужный обход
                config_text = res.text
                config_text = re.sub(
                    r"AllowedIPs\s*=.*",
                    "AllowedIPs = 0.0.0.0/1, 128.0.0.0/1",
                    config_text
                )
                print("🎉 ГОТОВЫЙ КОНФИГ:\n")
                print(config_text)
            else:
                print("⚠️ Не удалось сформировать конфиг. Проверь правильность кода доступа.")
        except Exception as e:
            print(f"❌ Ошибка при генерации конфига: {e}")

btn_send_email.on_click(send_email_request)
btn_gen_config.on_click(generate_config_request)

# --- Отрисовка формы ---
print("==================================================")
print("«FREE ACCESS GRABBER» (FAG) — AmneziaWG Generator")
print("==================================================\n")

display(email_input, btn_send_email)
print("-" * 50)
display(code_input, version_select, location_select, btn_gen_config)
print("-" * 50)
display(output_area)

# Напоминалка в самом конце выполнения
print("\n" + "!" * 50)
print("📌 ВАЖНО ПОСЛЕ ЗАВЕРШЕНИЯ РАБОТЫ:")
print("1. Нажми иконку корзины 🗑️ у ячейки выполнения.")
print("2. Перейди в меню: Среда выполнения 🡢 Отключиться от среды выполнения и удалить её.")
print("Это полностью затрет логи и защитит аккаунт Google от бана!")
print("!" * 50)
