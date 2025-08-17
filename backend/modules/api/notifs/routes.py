from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from utils.logger_config import configure_logger
from dotenv import load_dotenv
import os

load_dotenv()
logger = configure_logger()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class TelegramMessage(BaseModel):
    message: str

def format_message(raw: str) -> str:
    cleaned = raw.strip()
    formatted = f"📢 <b>Notification</b>\n\n<pre>{cleaned}</pre>"
    return formatted

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": format_message(message),
        "parse_mode": "HTML",
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur notification Telegram: {e}")
        if 'response' in locals() and response is not None:
            logger.info(f"Response: {response.text}")
        raise

notifs_router = APIRouter()

@notifs_router.post("/notify", response_model=dict)
def notify(message: TelegramMessage):
    try:
        send_telegram_message(message.message)
        return {"message": "Notification sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")
