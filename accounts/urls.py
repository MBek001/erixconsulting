from django.urls import path

from accounts.aiview import ChatWithBotView
from accounts.request import save_message
from accounts.views import *
from accounts.web_bot import chat_page, send_message_to_bot, fetch_messages, fetch_users, mark_messages_as_read
from accounts import admin_views

urlpatterns = [
    path('', home_view, name='home'),
    # path('about', about_view, name='about'),
    path('service', service_list, name='service'),
    # path('blog', blog_view, name='blog'),
    path('profile', Profile.as_view(), name='profile'),
    path('delete-profile-picture/', delete_profile_picture, name='delete_profile_picture'),
    path('contact', contact_us, name='contact'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('chat-bot', ChatWithBotView.as_view(), name='chat_with_bot'),
    path('save-message', save_message, name='save_message'),
    path('chat/', chat_page, name='chat_page'),
    path('send-message-to-bot/', send_message_to_bot, name='send_message_to_bot'),
    path('fetch_messages/', fetch_messages, name='fetch_messages'),
    path('fetch_users/', fetch_users, name='fetch_users'),
    path('mark_messages_as_read/', mark_messages_as_read, name='mark_messages_as_read'),

    # Custom Admin Panel
    path('custom-admin/', admin_views.admin_dashboard, name='admin_dashboard'),

    # Team Management
    path('custom-admin/team/', admin_views.team_member_list, name='team_member_list'),
    path('custom-admin/team/add/', admin_views.team_member_add, name='team_member_add'),
    path('custom-admin/team/<int:pk>/edit/', admin_views.team_member_edit, name='team_member_edit'),
    path('custom-admin/team/<int:pk>/delete/', admin_views.team_member_delete, name='team_member_delete'),

    # Service Management
    path('custom-admin/services/', admin_views.service_list, name='service_list_admin'),
    path('custom-admin/services/add/', admin_views.service_add, name='service_add'),
    path('custom-admin/services/<int:pk>/edit/', admin_views.service_edit, name='service_edit'),
    path('custom-admin/services/<int:pk>/delete/', admin_views.service_delete, name='service_delete'),

    # User Management
    path('custom-admin/users/', admin_views.user_list, name='user_list_admin'),

    # Messages
    path('custom-admin/messages/', admin_views.message_list, name='message_list_admin'),
    path('custom-admin/messages/<int:pk>/delete/', admin_views.message_delete, name='message_delete'),

    # Comments
    path('custom-admin/comments/', admin_views.comment_list, name='comment_list_admin'),
    path('custom-admin/comments/<int:pk>/delete/', admin_views.comment_delete, name='comment_delete'),

    # Blogs
    path('custom-admin/blogs/', admin_views.blog_list, name='blog_list_admin'),
    path('custom-admin/blogs/add/', admin_views.blog_add, name='blog_add'),
    path('custom-admin/blogs/<int:pk>/edit/', admin_views.blog_edit, name='blog_edit'),
    path('custom-admin/blogs/<int:pk>/delete/', admin_views.blog_delete, name='blog_delete'),
]
