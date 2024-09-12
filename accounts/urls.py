from django.urls import path
from .views import *


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
]
