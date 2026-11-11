"""URL routes for grow profiles (mounted at /profiles/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.ProfileListView.as_view(), name="profile_list"),
    path("new/", views.ProfileCreateView.as_view(), name="profile_new"),
    path("<int:pk>/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("<int:pk>/delete/", views.ProfileDeleteView.as_view(), name="profile_delete"),
]
