"""Puts the customer's cart count in every template (navbar badge, US-19)."""

from django.db.models import Sum

from .models import CartItem


def cart_count(request):
    user = request.user
    if not (user.is_authenticated and user.is_customer):
        return {"cart_count": 0}
    total = CartItem.objects.filter(customer=user).aggregate(total=Sum("quantity"))["total"]
    return {"cart_count": total or 0}
