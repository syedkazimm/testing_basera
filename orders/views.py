"""Cart and order views (US-19 onwards)."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import F, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView

from accounts.mixins import CustomerRequiredMixin

from basera.htmx import is_htmx
from catalog.models import Species
from growprofiles.models import GrowProfile

from .models import CartItem


def cart_total_quantity(user):
    return CartItem.objects.filter(customer=user).aggregate(total=Sum("quantity"))["total"] or 0


class CartAddView(View):
    """US-19: add one plant to the cart (POST only).

    - Guests are sent to log in and then back to the species page (not to this POST-only URL).
    - Sellers and admins get a 403: only customers shop.
    - Invasive, inactive, removed or out-of-stock species cannot be added; an existing item goes up
      by one but never above the stock.
    - HTMX: replies with the button ("Added ✔") plus the navbar badge as an out-of-band swap.
    """

    http_method_names = ["post"]

    def post(self, request, species_id):
        next_url = self.safe_next(request, default=reverse("species_detail", args=[species_id]))
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={next_url}")
        if not request.user.is_customer:
            raise PermissionDenied

        species = get_object_or_404(Species.objects.visible(), pk=species_id)  # inactive/removed: 404
        added, feedback = self.add(request.user, species)
        self.remember_profile(request)

        if is_htmx(request):
            return render(request, "orders/_add_to_cart.html", {
                "species": species, "added": added, "feedback": feedback,
                "profile": request.POST.get("profile", ""), "next": next_url,
                "cart_count": cart_total_quantity(request.user), "oob": True,
            })
        (messages.success if added else messages.error)(request, feedback)
        return HttpResponseRedirect(next_url)

    @staticmethod
    def add(user, species):
        """Apply the cart rules. Returns (added?, message)."""
        if species.is_invasive:
            return False, f"{species.common_name} is an invasive species and is not sold."
        if species.stock < 1:
            return False, f"{species.common_name} is out of stock."
        item, created = CartItem.objects.get_or_create(customer=user, species=species)
        if created:
            return True, f"Added {species.common_name} to your cart."
        if item.quantity >= species.stock:
            return False, f"Your cart already has all {species.stock} available {species.common_name}."
        item.quantity = F("quantity") + 1
        item.save(update_fields=["quantity"])
        return True, f"Added another {species.common_name} to your cart."

    @staticmethod
    def safe_next(request, default):
        """Only follow a `next` address that stays on this site."""
        candidate = request.POST.get("next", "")
        if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}):
            return candidate
        return default

    @staticmethod
    def remember_profile(request):
        """When adding from a match page, remember which grow profile led to the purchase (US-22)."""
        profile_id = request.POST.get("profile", "")
        if profile_id.isdigit() and GrowProfile.objects.filter(pk=profile_id, customer=request.user).exists():
            request.session["grow_profile_id"] = int(profile_id)


def cart_context(user, error=None):
    """Everything the cart page/partial needs: the items, the grand total and any problems."""
    items = list(CartItem.objects.filter(customer=user).select_related("species"))
    total = sum(item.line_total for item in items if not item.unavailable)
    return {
        "items": items,
        "grand_total": total,
        "has_problems": any(item.unavailable or item.over_stock for item in items),
        "cart_count": sum(item.quantity for item in items),
        "error": error,
    }


class CartView(CustomerRequiredMixin, TemplateView):
    """US-20: the cart page - items, line totals and the grand total."""

    template_name = "orders/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(cart_context(self.request.user))
        return context


class CartChangeView(CustomerRequiredMixin, View):
    """Base for the two POST actions below: find MY cart item (anyone else's is a 404), act, redraw.

    HTMX: reply with the cart block (rows, totals) plus the navbar badge out-of-band, so the page
    updates in place. Without JavaScript: redirect back to the cart with a message.
    """

    http_method_names = ["post"]

    def post(self, request, item_id):
        item = get_object_or_404(CartItem.objects.select_related("species"), pk=item_id, customer=request.user)
        error = self.change(request, item)
        if is_htmx(request):
            context = cart_context(request.user, error)
            context["oob"] = True
            return render(request, "orders/_cart.html", context)
        if error:
            messages.error(request, error)
        return redirect("cart")

    def change(self, request, item):
        raise NotImplementedError


class CartUpdateView(CartChangeView):
    """US-20: set an item's quantity (between 1 and the available stock)."""

    def change(self, request, item):
        try:
            quantity = int(request.POST.get("quantity", ""))
        except ValueError:
            return "Please enter a whole number for the quantity."
        stock = item.species.stock
        if quantity < 1:
            return "The quantity must be at least 1. Use Remove to take the plant out of your cart."
        if quantity > stock:
            return f"Only {stock} {item.species.common_name} available."
        item.quantity = quantity
        item.save(update_fields=["quantity"])
        return None


class CartRemoveView(CartChangeView):
    """US-20: remove an item from the cart."""

    def change(self, request, item):
        item.delete()
        return None
