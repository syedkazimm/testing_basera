"""URL routes for accounts (mounted at /accounts/)."""

from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.BaseraLoginView.as_view(), name="login"),
    # Logging out is a POST (Django 5 requirement); it ends the session and lands on home.
    path("logout/", LogoutView.as_view(), name="logout"),
    path("signup/", views.SignupView.as_view(), name="signup"),
]
