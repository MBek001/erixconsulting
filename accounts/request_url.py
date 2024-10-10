# urls.py
from django.urls import path

from accounts.request import request_page
from accounts.status import check_chat_status
from accounts.web_bot import close_chat

urlpatterns = [
    path('requests/', request_page, name='request_messages'),
    path('close_chat/', close_chat, name='close_chat'),
    path('check-chat-status/', check_chat_status, name='chat_status'),
]