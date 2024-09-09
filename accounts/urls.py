from operator import index

from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from setuptools.extern import names

from .views import *
urlpatterns = [
    path('', index_en, name='home'),
    path('about',index_en, name='about'), # have to changeeee
    path('service',index_en, name='service'), ## have to changeee
    path('members',index_en, name='members'), # have to chngeeee
    path('profile',profile, name='profile'), # have to chngeeee
    path('contact',index_en, name='contact'), # have to chngeeee
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('services/', service_list, name='service_list'),
    # path('ru', index_ru, name='ru'),
    # path('uz', index_uz, name='uz'),
]
