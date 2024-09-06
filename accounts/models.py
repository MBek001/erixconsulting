from django.contrib.admindocs.utils import ROLES
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, first_name, surname, email, password=None, phone_number=None, role=None):
        if not email:
            raise ValueError('The Email field is required')
        if not first_name:
            raise ValueError('The First Name field is required')

        email = self.normalize_email(email)
        user = self.model(
            first_name=first_name,
            surname=surname,
            email=email,
            phone_number=phone_number,
            role=role
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, surname, email, password=None):
        user = self.create_user(
            first_name=first_name,
            surname=surname,
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
    surname = models.CharField(max_length=50)
    email = models.EmailField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',  # related_name ni o'zgartirish
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  # related_name ni o'zgartirish
        blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'sur_name']

    def __str__(self):
        return self.email