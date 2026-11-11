"""Views for the accounts app."""

from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView

from .forms import LoginForm, SignupForm


class SignupView(CreateView):
    """US-01: create a customer or seller account.

    HTMX: the form lives in a partial. Errors re-render just the partial (status 200);
    success redirects to the login page (HX-Redirect when the request came from HTMX).
    """

    form_class = SignupForm
    template_name = "accounts/signup.html"

    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return ["accounts/_signup_form.html"]
        return [self.template_name]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Account created. Please log in.")
        if self.request.headers.get("HX-Request"):
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse("login")
            return response
        return redirect("login")


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
