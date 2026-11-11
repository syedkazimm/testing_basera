"""Cart and order models (US-19 adds CartItem; Order and OrderItem arrive with US-22)."""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Species


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
