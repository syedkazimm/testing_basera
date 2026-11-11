"""Views for the accounts app."""

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import CreateView

from .forms import SignupForm


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
            response["HX-Redirect"] = settings.LOGIN_URL
            return response
        return redirect(settings.LOGIN_URL)
