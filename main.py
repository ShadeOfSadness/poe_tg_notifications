import requests
import time
import threading
import regex as re
import configparser


config = configparser.ConfigParser()
config.read('config.ini')

TELEGRAM_BOT_TOKEN = config['Telegram']['BOT_TOKEN']
TELEGRAM_CHAT_ID = config['Telegram']['CHAT_ID']
log_path = config['Log']['LOG_PATH']


# Переменная для отслеживания последней прочитанной строки
last_position = 0


# Функция для отправки сообщения в Telegram
def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    response = requests.post(url, json=data)
    return response.json()


# Функция для определения последней строки в файле логов
def get_last_line_position():
    try:
        with open(log_path, 'rb') as file:
            file.seek(0, 2)  # Переходим в конец файла
            file_size = file.tell()
            position = max(0, file_size - 1024)  # Читаем последние 1024 байта файла
            file.seek(position)
            lines = file.readlines()
            for i in range(len(lines) - 1, -1, -1):
                if b'[INFO Client' in lines[i]:
                    return position + sum(len(line) for line in lines[:i + 1])
    except Exception as e:
        print(f"Error: {e}")
    return 0


# Определяем начальное значение last_position
last_position = get_last_line_position()


# Функция для мониторинга логов
def monitor_logs():
    global last_position
    while True:
        try:
            with open(log_path, 'r', encoding='utf-8') as file:
                file.seek(last_position)
                new_lines = file.readlines()
                for line in new_lines:
                    if '[INFO Client' in line and 'Hi, I would like to buy' in line:
                        match = re.search(r'@From\s+<[^>]+>\s(.*?):\sHi, I would like to buy your (.*?) listed for (.*?) in', line)
                        if match:
                            sender = match.group(1)
                            item_name = match.group(2)
                            price = match.group(3)
                            notification = f"Пользователь {sender} хочет купить {item_name} за {price}."
                            print(notification)
                            send_telegram_message(notification)
                last_position = file.tell()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

# Запускаем мониторинг логов в отдельном потоке
monitor_thread = threading.Thread(target=monitor_logs)
monitor_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
