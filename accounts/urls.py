from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from .views import *
urlpatterns = [
    path('index_en', index_en, name='index'),
    path('index_ru', index_ru, name='index'),
    path('index_uz', index_uz, name='index'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
