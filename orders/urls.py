"""URL routes for the cart (mounted at /cart/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.CartView.as_view(), name="cart"),
    path("update/<int:item_id>/", views.CartUpdateView.as_view(), name="cart_update"),
    path("remove/<int:item_id>/", views.CartRemoveView.as_view(), name="cart_remove"),
    path("add/<int:species_id>/", views.CartAddView.as_view(), name="cart_add"),
]
