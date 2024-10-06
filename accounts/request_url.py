# urls.py
from django.urls import path

from accounts.request import request_page

urlpatterns = [
    path('requests/', request_page, name='request_messages'),
]