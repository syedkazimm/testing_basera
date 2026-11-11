"""URL routes for the cart (mounted at /cart/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("add/<int:species_id>/", views.CartAddView.as_view(), name="cart_add"),
]
