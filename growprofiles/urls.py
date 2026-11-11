"""URL routes for grow profiles (mounted at /profiles/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.ProfileListView.as_view(), name="profile_list"),
    path("new/", views.ProfileCreateView.as_view(), name="profile_new"),
]
