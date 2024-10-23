from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django.views import View
from django.contrib.auth import login,logout

from accounts.forms import LoginForm, CommentForm
from accounts.models import User, Service, TeamMembership, Comment, BlogPost
from accounts.utils import EmailBackend, send_mail_for_contact_us, open_requests, unread_messages


def about_view(request):
    team_members = TeamMembership.objects.select_related('user').all()

    open_reqs_context = open_requests(request)
    unread_mess_context = unread_messages(request)

    context = {
        'team_members': team_members,
        'active_page': 'about',
        'open_requests': open_reqs_context['open_requests'],
        'has_unread_messages': unread_mess_context['has_unread_messages'],
    }

    return render(request, 'about.html', context)


def blog_view(request):
    blogs = BlogPost.objects.all().order_by('-created_at')
    # Call context processor functions
    open_reqs_context = open_requests(request)
    unread_mess_context = unread_messages(request)
    context = {'blogs': blogs,
               'active_page': 'blog',
               'open_requests': open_reqs_context['open_requests'],
               'has_unread_messages': unread_mess_context['has_unread_messages'],
               }
    return render(request,'blogs.html',context,)


def service_list(request):
    services = Service.objects.all()

    open_reqs_context = open_requests(request)
    unread_mess_context = unread_messages(request)
    context = {
        'services': services,
        'active_page': 'services',
        'open_requests': open_reqs_context['open_requests'],
        'has_unread_messages': unread_mess_context['has_unread_messages'],
    }
    return render(request, 'service_list.html', context,)


def contact_us(request):
    open_reqs_context = open_requests(request)
    unread_mess_context = unread_messages(request)
    context = {'active_page': 'contact',
               'open_requests': open_reqs_context['open_requests'],
               'has_unread_messages': unread_mess_context['has_unread_messages'],
               }
    if request.method == 'POST':
        if request.user.is_authenticated:
            user_name = f"{request.user.first_name} {request.user.last_name}"
            email = request.user.email
            phone_number = User.objects.get(email=email).phone_number
        else:
            user_name = request.POST.get('name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')

        subject = request.POST.get('subject')
        message = request.POST.get('message')

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

    return render(request, 'contact_us.html',context)


def home_view(request):
    comments = Comment.objects.select_related('user').order_by('-created_at')
    team_members = TeamMembership.objects.all()

    open_reqs_context = open_requests(request)
    unread_mess_context = unread_messages(request)

    if request.method == 'POST':
        if request.user.is_authenticated:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.user = request.user
                comment.save()
                return redirect('home')
        else:
            return redirect('login')
    else:
        form = CommentForm()

    context = {
        'comments': comments,
        'team_members': team_members,
        'form': form,
        'active_page': 'home',
        'open_requests': open_reqs_context['open_requests'],
        'has_unread_messages': unread_mess_context['has_unread_messages'],
    }
    return render(request, 'index_en.html', context)


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
        open_reqs_context = open_requests(request)
        unread_mess_context = unread_messages(request)
        user = request.user
        context = {
            'firstname': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'profile_picture': user.profile_picture,
            'open_requests': open_reqs_context['open_requests'],
            'has_unread_messages': unread_mess_context['has_unread_messages'],
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
    user = request.user
    try:
        if user.profile_picture:
            user.profile_picture.delete(save=False)
            user.profile_picture = None
            user.save()

            messages.error(request, "Profile picture deleted successfully.")
        else:
            messages.info(request, "No profile picture to delete.")
    except User.DoesNotExist:
        messages.warning(request, "Profile does not exist.")

    return redirect('profile')
