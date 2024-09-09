from traceback import print_tb

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login,logout

from accounts.forms import LoginForm
from .models import User, Service
from .utils import EmailBackend


# from django.contrib.auth.models import User


class RegisterView(View):
    template_name = 'register.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password1 = request.POST.get('password')
        password2 = request.POST.get('confirm_password')

        if not first_name:
            messages.error(request, "First name is required.")
            return redirect('/register')

        if not phone_number:
            messages.error(request, "Phone number is required.")
            return redirect('/register')

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('/register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email already exists")
            return redirect('/register')

        is_first_user = not User.objects.exists()

        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            password=make_password(password1),
            is_superuser=is_first_user,
            is_staff=is_first_user
        )
        user.save()
        login(request, user)

        return redirect('/')


class LoginView(View):
    template = "login.html"
    context = {}

    def get(self, request):
        form = LoginForm()
        self.context.update({'form': form})
        return render(request, self.template, self.context)

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = EmailBackend.authenticate(request,email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
            else:
                messages.error(request, "Username or password is wrong !")

        return redirect('/login')


class LogoutView(View):

    def get(self, request):
        logout(request)
        return redirect('/login')


def service_list(request):
    services = Service.objects.all()
    context = {
        'services': services
    }
    return render(request, 'service_list.html', context)

def index_en(request):
    return render(request, 'index_en.html')
#

def profile(request):
    return render(request, 'profile.html')
#
# def index_uz(request):
#     return render(request, 'index_uz.html')
