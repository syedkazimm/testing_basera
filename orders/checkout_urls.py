"""URL routes for checkout (mounted at /checkout/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.CheckoutView.as_view(), name="checkout"),
    path("summary/", views.CheckoutSummaryView.as_view(), name="checkout_summary"),
    path("place/", views.PlaceOrderView.as_view(), name="checkout_place"),
]
