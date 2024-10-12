import logging
import os
import requests

def escape_markdown(text):
    return text.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]").replace("`", "\\`")

def send_error_to_telegram(error_message):
    bot_token = os.getenv("ERRORS_BOT")
    chat_id = os.getenv("CHANNEL_ID")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    project_prefix = "Project: ErixConsulting:\n"
    full_message = project_prefix + error_message
    escaped_message = escape_markdown(full_message)

    payload = {
        'chat_id': chat_id,
        'text': escaped_message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logging.info("Error message sent to Telegram successfully.")
        else:
            logging.error(f"Failed to send message: {response.status_code}, {response.text}")
    except Exception as e:
        logging.error(f"Error sending message to Telegram: {e}")

