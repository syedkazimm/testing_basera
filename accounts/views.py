"""Views for the accounts app."""

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView

from basera.htmx import is_htmx, redirect_to

from .forms import LoginForm, ResetConfirmForm, ResetRequestForm, SignupForm


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
