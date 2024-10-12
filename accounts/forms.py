from accounts.models import User, Comment
from django.forms import CharField, PasswordInput, TextInput, Form
from django import forms

class LoginForm(Form):
    email = CharField(label='Email', widget=TextInput(attrs={
        'class': 'form-control',
        'id': 'email',
        'placeholder': 'Email'
    }))
    password = CharField(label='Password', widget=PasswordInput(attrs={
        'class': 'form-control',
        'id': 'password',
        'placeholder': 'Enter your password'
    }))

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'email', 'email']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'Write your comment here...', 'rows': 3}),
        }