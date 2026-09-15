import time

import requests


TOKEN_FILE = r'C:\Users\MainUser\Desktop\telegram_bot_token.txt'
CHAT_ID_FILE = r'C:\Users\MainUser\Desktop\telegram_chat_id.txt'


with open(TOKEN_FILE, 'r', encoding='utf-8') as file:
    token = file.read().strip()

with open(CHAT_ID_FILE, 'r', encoding='utf-8') as file:
    chat_id = file.read().strip()


def send_telegram_message(message: str) -> float:
    url = f'https://api.telegram.org/bot{token}/sendMessage'

    started_at = time.perf_counter()

    response = requests.post(
        url,
        json={
            'chat_id': chat_id,
            'text': message,
        },
        timeout=10,
    )

    response.raise_for_status()

    return time.perf_counter() - started_at