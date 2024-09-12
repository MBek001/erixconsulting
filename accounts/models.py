from datetime import timezone, datetime

import django
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, first_name, email, last_name=None, password=None, phone_number=None, role=None):
        if not email:
            raise ValueError('The Email field is required')
        if not first_name:
            raise ValueError('The First Name field is required')

        email = self.normalize_email(email)
        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, email, last_name=None, password=None):
        user = self.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures', blank=True, null=True)
    join_date = models.DateTimeField(default= django.utils.timezone.now)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


class TeamMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    role = models.CharField(max_length=50)
    description = models.TextField(max_length=500, blank=True, null=True)
    instagram = models.URLField(max_length=200, blank=True, null=True)
    twitter = models.URLField(max_length=200, blank=True, null=True)
    facebook = models.URLField(max_length=200, blank=True, null=True)
    youtube = models.URLField(max_length=200, blank=True, null=True)
    linkedin = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.role}"

class Service(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(TeamMembership)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='comments', blank=True, null=True)

    def __str__(self):
        return f"Comment by {self.user.email} at {self.created_at}"


class Conversation(models.Model):
    user = models.ForeignKey(User, related_name='user_conversations', on_delete=models.CASCADE)
    staff = models.ForeignKey(TeamMembership, related_name='manager_conversations', on_delete=models.SET_NULL, null=True, blank=True)
    conversation_file = models.FileField(upload_to='conversations/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation between {self.user.email} and {self.staff.user.email if self.staff else 'Unassigned'}"


class About(models.Model):
    company_name = models.CharField(max_length=100)
    mission = models.TextField(blank=True, null=True)
    description = models.TextField()
    services_overview = models.TextField(blank=True, null=True)
    team_description = models.TextField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    image = models.ImageField(upload_to='about/', blank=True, null=True)

    def __str__(self):
        return self.company_name

class BlogPost(models.Model):
    theme = models.CharField(max_length=100)
    content = models.TextField()
    file = models.FileField(upload_to='blog', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.theme