"""URL routes for the public catalogue (mounted at the site root)."""

from django.urls import path

from . import views

urlpatterns = [
    path("catalogue/", views.CatalogueView.as_view(), name="catalogue"),
    path("species/<int:pk>/", views.SpeciesDetailView.as_view(), name="species_detail"),
    # Seller side (US-13 onwards)
    path("seller/listings/", views.ListingListView.as_view(), name="listing_list"),
    path("seller/listings/new/", views.ListingCreateView.as_view(), name="listing_new"),
]
