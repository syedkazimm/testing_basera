"""Admin for carts and orders. Orders are for looking at and light moderation; status is changed by sellers."""

from django.contrib import admin

from .models import CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # Name, price and quantity are a record of what was bought, so they are read-only.
    readonly_fields = ["species", "species_name", "unit_price", "quantity"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["number", "customer", "status", "total", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["customer__email", "delivery_name", "delivery_phone"]
    readonly_fields = ["customer", "grow_profile", "total", "created_at", "payment_method"]
    inlines = [OrderItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["customer", "species", "quantity", "created_at"]
    search_fields = ["customer__email", "species__common_name"]
