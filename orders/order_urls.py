"""URL routes for orders (mounted at /orders/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.OrderListView.as_view(), name="order_list"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("<int:pk>/cancel/", views.OrderCancelView.as_view(), name="order_cancel"),
]
