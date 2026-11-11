"""URL routes for matching (mounted at /match/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("<int:profile_id>/", views.MatchView.as_view(), name="match"),
]
