from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        # Both email and password are required — no optional password allowed
        if not email:
            raise ValueError("Email is required")
        if not password:
            raise ValueError("Password is required")
        if not extra_fields.get('full_name'):
            raise ValueError("Full name is required")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, **extra_fields):
        # Superuser must also have a password
        if not password:
            raise ValueError("Superuser must have a password")

        # Superusers are always admins in this system
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(
            email,
            password,
            **extra_fields,
        )

class ActiveUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)

class User(AbstractUser):
    class Role(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Admin"

    username = None

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=False)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)


    objects = UserManager()
    active = ActiveUserManager()


    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        # Ensure email is always normalized (lowercase)
        from django.contrib.auth.models import BaseUserManager
        self.email = BaseUserManager.normalize_email(self.email)
        super().save(*args, **kwargs)
