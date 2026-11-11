"""URL routes for the public catalogue (mounted at the site root)."""

from django.urls import path

from . import views

urlpatterns = [
    path("catalogue/", views.CatalogueView.as_view(), name="catalogue"),
    path("species/<int:pk>/", views.SpeciesDetailView.as_view(), name="species_detail"),
]
