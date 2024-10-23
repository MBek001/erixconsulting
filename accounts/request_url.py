from django.urls import path

from accounts.chat_history import fetch_messages_history, fetch_users_history, chat_page
from accounts.request import request_page
from accounts.status import check_chat_status
from accounts.web_bot import close_chat

urlpatterns = [
    path('requests/', request_page, name='request_messages'),
    path('close_chat/', close_chat, name='close_chat'),
    path('check-chat-status/', check_chat_status, name='chat_status'),
    path('chats-history/', fetch_messages_history, name='fetch_messages_history'),
    path('fetch-users-history/', fetch_users_history, name='fetch_users_history'),
    path('chat_history/', chat_page, name='chat_history')
]