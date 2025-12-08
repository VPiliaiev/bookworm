import requests
from django.conf import settings


def send_telegram_message(chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5).raise_for_status()
    except Exception as e:
        print("Telegram message failed:", e)
