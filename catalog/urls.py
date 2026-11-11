"""URL routes for the public catalogue (mounted at the site root)."""

from django.urls import path

from . import views

urlpatterns = [
    path("catalogue/", views.CatalogueView.as_view(), name="catalogue"),
    path("species/<int:pk>/", views.SpeciesDetailView.as_view(), name="species_detail"),
    # Seller side (US-13 onwards)
    path("seller/listings/", views.ListingListView.as_view(), name="listing_list"),
    path("seller/listings/new/", views.ListingCreateView.as_view(), name="listing_new"),
    path("seller/listings/<int:pk>/edit/", views.ListingUpdateView.as_view(), name="listing_edit"),
    path("seller/listings/<int:pk>/delete/", views.ListingDeleteView.as_view(), name="listing_delete"),
]
