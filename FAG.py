import requests

url = 'https://hdmn.cloud/ru/demo/'

try:
    response = requests.get(url, timeout=10)
    response.encoding = 'utf-8'

    if response.status_code == 200:
        if 'Ваша электронная почта' in response.text:
            email = input('📧 Введите электронную почту: ').strip()

            try:
                # Отправка формы на актуальный эндпоинт
                res_post = requests.post(
                    'https://hdmn.cloud/ru/demo/success/',
                    data={'demo_mail': email},
                    timeout=10
                )
                res_post.encoding = 'utf-8'

                if res_post.status_code == 200 and 'Ваш код выслан на почту' in res_post.text:
                    print('\033[1;32mВаш код уже в пути! Проверьте свой почтовый ящик.\033[0m')
                else:
                    print('\033[1;31mУказанная почта не подходит для получения тестового периода.\033[0m')

            except requests.RequestException as e:
                print(f'\033[1;31mОшибка при отправке почты: {e}\033[0m')
        else:
            print('\033[1;31mОтключитесь от среды выполнения и удалите её.\033[0m')
    else:
        print(f'\033[1;31mОшибка при запросе к странице. Код ответа: {response.status_code}\033[0m')

except requests.RequestException as e:
        print(f'\033[1;31mОшибка при запросе к сайту: {e}\033[0m')
