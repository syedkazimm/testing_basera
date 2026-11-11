"""Views for the accounts app."""

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from basera.htmx import is_htmx, redirect_to

from .forms import (ChangePasswordForm, LoginForm, ProfileForm, ResetConfirmForm, ResetRequestForm,
                    SignupForm)


class SignupView(CreateView):
    """US-01: create a customer or seller account.

    HTMX: the form lives in a partial. Errors re-render just the partial (status 200);
    success redirects to the login page (HX-Redirect when the request came from HTMX).
    """

    form_class = SignupForm
    template_name = "accounts/signup.html"

    def get_template_names(self):
        if is_htmx(self.request):
            return ["accounts/_signup_form.html"]
        return [self.template_name]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Account created. Please log in.")
        return redirect_to(self.request, reverse("login"))


class BaseraLoginView(LoginView):
    """US-02: log in, then land on the page that suits the user's role.

    If a protected page sent the user here (?next=...), Django returns them to it instead.
    """

    form_class = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        user = self.request.user
        if user.is_staff:
            return "/admin/"
        if user.role == "SELLER":
            return "/seller/listings/"  # "My Listings" (built in Sprint 2)
        return "/profiles/"  # "My Grow Profiles"


# --- US-03: forgot password (Django's built-in views with our templates and forms) ---------------
# Unknown emails get the same "check your email" page, so nobody can find out who has an account.
class PasswordResetRequestView(auth_views.PasswordResetView):
    form_class = ResetRequestForm
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class PasswordResetConfirmPageView(auth_views.PasswordResetConfirmView):
    form_class = ResetConfirmForm
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class ChangePasswordView(auth_views.PasswordChangeView):
    """US-04: change password while logged in.

    Django's view keeps the user logged in afterwards (update_session_auth_hash) and requires
    the current password. Logged-out visitors are sent to login first.
    """

    form_class = ChangePasswordForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("password_change")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been updated.")
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, UpdateView):
    """US-05: "My Profile" - view and edit your own details (any logged-in role).

    The object is always request.user, so nobody can open someone else's profile.
    HTMX: errors re-render only the form partial; success reloads the page with a message.
    """

    form_class = ProfileForm
    template_name = "accounts/profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_template_names(self):
        if is_htmx(self.request):
            return ["accounts/_profile_form.html"]
        return [self.template_name]

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your profile has been updated.")
        return redirect_to(self.request, reverse("profile"))
