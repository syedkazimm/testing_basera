"""Forms for the accounts app."""

from django import forms
from django.contrib.auth.forms import (AuthenticationForm, PasswordChangeForm, PasswordResetForm,
                                       SetPasswordForm)
from django.contrib.auth.password_validation import validate_password

from basera.forms import BootstrapFormMixin

from .models import User


class SignupForm(BootstrapFormMixin, forms.ModelForm):
    """US-01: sign-up form. Admin accounts can never be created here."""

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput,
                                help_text="At least 8 characters, not all numbers, not a common password.")
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "role"]
        labels = {"role": "I want to join as a"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # First and last name are required on sign-up (blank on the model for admins).
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        password1, password2 = cleaned.get("password1"), cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The two passwords do not match.")
        elif password1:
            # Build an unsaved user so the "too similar to your details" check works.
            candidate = User(first_name=cleaned.get("first_name", ""), last_name=cleaned.get("last_name", ""),
                             email=cleaned.get("email", ""))
            try:
                validate_password(password1, candidate)
            except forms.ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    """US-02: log in with email. One generic error so we never reveal which field was wrong."""

    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))
    error_messages = {
        "invalid_login": "Incorrect email or password.",
        "inactive": "Incorrect email or password.",
    }

    def clean_username(self):
        # Emails are stored lower-case, so compare in lower-case.
        return self.cleaned_data["username"].lower()


class ResetRequestForm(BootstrapFormMixin, PasswordResetForm):
    """US-03: ask for a password-reset email."""


class ResetConfirmForm(BootstrapFormMixin, SetPasswordForm):
    """US-03: choose a new password (same rules as sign-up)."""


class ChangePasswordForm(BootstrapFormMixin, PasswordChangeForm):
    """US-04: change password; the current password must be right."""
