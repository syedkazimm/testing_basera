"""User model for Basera (US-01): log in with email, with a CUSTOMER or SELLER role."""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from .validators import phone_validator


class UserManager(BaseUserManager):
    """Manager that uses the email address as the identifier instead of a username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # stores a salted hash, never the raw password
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """A Basera account. Admins are simply users with is_staff=True."""

    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        SELLER = "SELLER", "Seller"

    username = None  # not used; the email is the login name
    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    default_address = models.TextField(blank=True)
    default_city = models.CharField(max_length=60, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def save(self, *args, **kwargs):
        # Emails are always stored lower-case so they are unique regardless of case.
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER and not self.is_staff

    @property
    def is_seller(self):
        return self.role == self.Role.SELLER and not self.is_staff

    def __str__(self):
        return self.email
