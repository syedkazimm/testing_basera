"""URL routes for seller fulfilment (mounted at /seller/orders/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.SellerOrderListView.as_view(), name="seller_order_list"),
    path("<int:pk>/advance/", views.SellerOrderAdvanceView.as_view(), name="seller_order_advance"),
]
