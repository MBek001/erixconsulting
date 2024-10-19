import logging
import os
import requests
from aiogram import Bot
from flask.cli import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_INFO_BOT = os.getenv('CHANNEL_INFO_BOT')
INFO_CHANNEL_ID = os.getenv("INFO_CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)
delayed_bot = Bot(token=CHANNEL_INFO_BOT)

def send_info_to_channel(message):
    url = f"https://api.telegram.org/bot{CHANNEL_INFO_BOT}/sendMessage"
    payload = {
        'chat_id': INFO_CHANNEL_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logging.info("Assigment Message sent successfully")
        else:
            logging.error(f"Failed to send message of assigment: {response.status_code}, {response.text}")
    except Exception as e:
        logging.error(f"Error sending assigment message to Telegram: {e}")


def notify_customer(chat_id,message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logging.info(" Notify Message sent successfully")
        else:
            logging.error(f"Failed to send notify message: {response.status_code}, {response.text}")
    except Exception as e:
        logging.error(f"Error sending notify message to Telegram: {e}")