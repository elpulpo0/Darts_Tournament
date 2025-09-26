import requests
from utils.logger_config import configure_logger
from dotenv import load_dotenv
import os

load_dotenv()
logger = configure_logger()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


class NotifyUserRegistration:
    def __init__(self, nickname, tournamentName, type):
        self.nickname = nickname
        self.tournamentName = tournamentName
        self.type = type


class NotifyUserCreate:
    def __init__(self, name, email, role, type):
        self.name = name
        self.email = email
        self.role = role
        self.type = type


class NotifyUserLogin:
    def __init__(self, name, role, scopes, type):
        self.name = name
        self.role = role
        self.scopes = scopes
        self.type = type


def notify_telegram(user):
    if user.type == "userCreate":
        message = (
            "<b>🧩 New user created!</b>\n\n"
            f"<b>👤 Name:</b> {user.name}\n"
            f"<b>📧 Email:</b> {user.email}\n"
            f"<b>🛡️ Role:</b> {user.role}\n"
        )
    elif user.type == "login":
        message = (
            "<b>🔐 New login detected!</b>\n\n"
            f"<b>👤 Name:</b> {user.name}\n"
            f"<b>🛡️ Role:</b> {user.role}\n"
            f"<b>🔑 Scopes:</b> {', '.join(user.scopes)}"
        )
    elif user.type == "userRegister":
        message = (
            "<b>📝 New registration detected!</b>\n\n"
            f"<b>👤 Name:</b> {user.nickname}\n"
            f"<b>🏆 Tournament:</b> {user.tournamentName}\n"
        )
    else:
        logger.error(f"Unknown user type: {user.type}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram notification error: {e}")
