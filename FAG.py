import sys
import os

# Автоматически ставим cloudscraper, если его нет в окружении Colab
try:
    import cloudscraper
except ImportError:
    os.system("pip install cloudscraper -q")
    import cloudscraper

def grab_code():
    # Запрашиваем твою почту
    email = input("Введи свою почту: ").strip()
    if not email:
        print("Почта не введена.")
        return

    # Создаем скрапер для обхода Cloudflare/защиты формы
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    url = "https://hidemy.name/ru/demo/"
    
    headers = {
        "Origin": "https://hidemy.name",
        "Referer": "https://hidemy.name/ru/demo/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    payload = {
        "email": email,
        "demo": "1"
    }

    print(f"Отправляем запрос для {email} через IP Google Colab...")

    try:
        response = scraper.post(url, data=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            if "Код выслан" in response.text or "success" in response.url or "проверьте" in response.text.lower():
                print("УСПЕХ! Запрос ушел. Чекай письмо на почте.")
            else:
                print("Запрос прошел (200), но проверь ответы формы. Возможно, вылезла капча.")
        else:
            print(f"Ошибка HTTP {response.status_code}. Возможно, IP заблокирован.")

    except Exception as e:
        print(f"Сбой при отправке: {e}")

if __name__ == "__main__":
    grab_code()
