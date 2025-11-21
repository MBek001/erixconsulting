"""
Unified Configuration File for ErixConsulting Project
All environment variables and settings should be loaded from .env file
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Django URLs
DJANGO_SAVE_URL = os.getenv('DJANGO_SAVE_URL', 'http://localhost:8000/save-message')
CHECK_CHAT_STATUS_URL = os.getenv('CHECK_CHAT_STATUS_URL', 'http://localhost:8000/check-chat-status/')

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
INFO_CHANNEL_ID = os.getenv('INFO_CHANNEL_ID', '')
CHANNEL_INFO_BOT = os.getenv('CHANNEL_INFO_BOT', '')
TELEGRAM_API_URL = os.getenv('TELEGRAM_API_URL', 'https://api.telegram.org')

# Directories
CONVERSATIONS_DIR = os.path.join(BASE_DIR, 'media', 'conversations')

# Create necessary directories if they don't exist
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

# Database Configuration (optional - can be moved to settings.py)
DB_NAME = os.getenv('DB_NAME', 'erixconsulting_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

# Email Configuration
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'

# Security
SECRET_KEY = os.getenv('SECRET_KEY', '')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
