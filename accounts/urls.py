from django.urls import path

from .aiview import ChatWithBotView
from .views import *
from .web_bot import save_message, chat_page, send_message_to_bot, fetch_messages, fetch_users

urlpatterns = [
    path('', home_view, name='home'),
    path('test', tes, name='test'),
    path('about',about_view, name='about'),
    path('service',service_list, name='service'),
    path('blog',blog_view, name='blog'),
    path('profile',Profile.as_view(), name='profile'),
    path('delete-profile-picture/', delete_profile_picture, name='delete_profile_picture'),
    path('contact',contact_us, name='contact'), # have to chngeeee
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('chat-bot/', ChatWithBotView.as_view(), name='chat_with_bot'),
    path('save-message', save_message, name='save_message'),
    path('chat/', chat_page, name='chat_page'),
    path('send-message-to-bot/', send_message_to_bot, name='send_message_to_bot'),
    path('fetch_messages/', fetch_messages, name='fetch_messages'),
    path('fetch_users/', fetch_users, name='fetch_users')
]
