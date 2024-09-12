from traceback import print_tb

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django.views import View
from django.contrib.auth import authenticate, login,logout

from accounts.forms import LoginForm, CommentForm
from .models import User, Service, About, TeamMembership, Comment, BlogPost
from .utils import EmailBackend, send_mail_for_contact_us


# from django.contrib.auth.models import User
def about_view(request):
    team_members = TeamMembership.objects.select_related('user').all()
    context = {'team_members': team_members,
               'active_page': 'about'
               }
    return render(request, 'about.html', context,)

def blog_view(request):
    blogs = BlogPost.objects.all().order_by('-created_at')
    context = {'blogs': blogs,
               'active_page': 'blog'
               }
    return render(request,'blogs.html',context,)


def service_list(request):
    services = Service.objects.all()
    context = {
        'services': services,
        'active_page': 'services'
    }
    return render(request, 'service_list.html', context,)


def contact_us(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            # For authenticated users
            user_name = f"{request.user.first_name} {request.user.last_name}"
            email = request.user.email
            phone_number = User.objects.get(email=email).phone_number
        else:
            # For unauthenticated users
            user_name = request.POST.get('name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')

        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Call the custom send_mail function
        send_mail_for_contact_us(email, phone_number, subject, message, user_name)
        response = format_html('''
            <html>
            <head>
                <meta http-equiv="refresh" content="4;url=contact" />
                <title>Success</title>
                <script type="text/javascript">
                    window.onload = function() {{
                        let timeLeft = 3;
                        const countdownElement = document.getElementById('countdown');
                        const countdown = setInterval(function() {{
                            if (timeLeft <= 0) {{
                                clearInterval(countdown);
                            }} else {{
                                countdownElement.innerHTML = timeLeft;
                            }}
                            timeLeft -= 1;
                        }}, 999);
                    }};
                </script>
            </head>
            <body>
                <div style="text-align: center; margin-top: 100px;">
                    <h3>Your message has been sent successfully!</h3>
                    <p>You will be redirected in <span id="countdown">3</span> seconds...</p>
                </div>
            </body>
            </html>
        ''')

        return HttpResponse(response)

    # Render the contact form template for GET requests
    return render(request, 'contact_us.html')



def home_view(request):
    # Fetch all comments and pass them to the home page
    comments = Comment.objects.select_related('user').order_by('-created_at')

    if request.method == 'POST':
        if request.user.is_authenticated:
            form = CommentForm(request.POST)
            if form.is_valid():
                # Create a new comment and associate it with the current user
                comment = form.save(commit=False)
                comment.user = request.user
                comment.service = Service.objects.first()  # You can modify to link it to a particular service
                comment.save()
                return redirect('home')
        else:
            # If not authenticated, redirect to login page or show a message
            return redirect('login')

    else:
        form = CommentForm()

    context = {
        'comments': comments,
        'form': form,
        'active_page': 'home',  # For highlighting the navbar
    }
    return render(request, 'index_en.html', context)


def tes(request):
    team_members = TeamMembership.objects.select_related('user').all()
    context = {'team_members': team_members}
    return render(request, 'test.html', context)



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



class Profile(LoginRequiredMixin, View):
    template_name = 'profile.html'

    def get(self, request):
        user = request.user
        context = {
            'firstname': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'profile_picture': user.profile_picture
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        photo = request.FILES.get('photo')

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        if email:
            if not User.objects.filter(email=email).exclude(pk=user.pk).exists():
                user.email = email
            else:
                messages.error(request, "This email is already taken.")
                return redirect('profile')

        if photo:
            user.profile_picture = photo

        user.save()
        messages.success(request, "Your profile has been updated!")
        return redirect('profile',)




@login_required
def delete_profile_picture(request):
    user = request.user  # This fetches the current logged-in user
    try:
        if user.profile_picture:
            # Delete the profile picture
            user.profile_picture.delete(save=False)
            user.profile_picture = None
            user.save()

            messages.error(request, "Profile picture deleted successfully.")
        else:
            messages.info(request, "No profile picture to delete.")
    except User.DoesNotExist:
        messages.warning(request, "Profile does not exist.")

    return redirect('profile')
