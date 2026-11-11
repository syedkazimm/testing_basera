"""Cart and order models (CartItem: US-19; Order and OrderItem: US-22)."""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Species
from growprofiles.models import GrowProfile


class CartItem(models.Model):
    """One species in a customer's cart. Quantity may never exceed the species' stock."""

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("customer", "species")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.customer}: {self.quantity} x {self.species}"

    @property
    def line_total(self):
        return self.species.price * self.quantity

    @property
    def unavailable(self):
        """True if this species can no longer be bought (removed, inactive, invasive or sold out)."""
        sp = self.species
        return sp.is_deleted or sp.status != Species.Status.ACTIVE or sp.is_invasive or sp.stock < 1

    @property
    def over_stock(self):
        """True if the cart asks for more plants than the seller now has."""
        return not self.unavailable and self.quantity > self.species.stock


class Order(models.Model):
    """A placed order (US-22). Delivery details are copied in, so later profile edits never change it."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    class PaymentMethod(models.TextChoices):
        COD = "COD", "Cash on Delivery"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    # The grow profile that led to this purchase, if any. Deleting the profile keeps the order.
    grow_profile = models.ForeignKey(GrowProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="orders")
    delivery_name = models.CharField(max_length=120)
    delivery_address = models.TextField()
    delivery_city = models.CharField(max_length=60)
    delivery_phone = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.number

    @property
    def next_status(self):
        """The one status this order may move to next (None for DELIVERED and CANCELLED)."""
        order = [self.Status.PENDING, self.Status.CONFIRMED, self.Status.SHIPPED, self.Status.DELIVERED]
        if self.status in order[:-1]:
            return order[order.index(self.status) + 1]
        return None

    @property
    def number(self):
        """The order number shown to people, e.g. BSR-000123."""
        return f"BSR-{self.pk:06d}"


class OrderItem(models.Model):
    """One line of an order. Name and price are copied from the species when the order is placed."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    species = models.ForeignKey(Species, on_delete=models.PROTECT, related_name="order_items")
    species_name = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.species_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
