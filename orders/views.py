"""Cart and order views (US-19 onwards)."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from accounts.mixins import CustomerRequiredMixin

from basera.htmx import is_htmx, redirect_to
from catalog.models import Species
from growprofiles.models import GrowProfile

from .forms import DeliveryForm
from .models import CartItem, Order, OrderItem


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


# --- Checkout (US-21) ---------------------------------------------------------------------------
DELIVERY_SESSION_KEY = "checkout_delivery"


class CheckoutGuardMixin(CustomerRequiredMixin):
    """Checkout needs a non-empty cart with nothing wrong in it; otherwise go back to the cart."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_customer:
            cart = cart_context(request.user)
            if not cart["items"]:
                messages.info(request, "Your cart is empty.")
                return redirect("cart")
            if cart["has_problems"]:
                messages.error(request, "Please fix the highlighted items in your cart before checking out.")
                return redirect("cart")
            self.cart = cart
        return super().dispatch(request, *args, **kwargs)


class CheckoutView(CheckoutGuardMixin, FormView):
    """US-21: delivery details, prefilled from the profile. Valid details lead to the order summary.

    HTMX: errors re-render only the form partial; success redirects with HX-Redirect.
    """

    form_class = DeliveryForm
    template_name = "orders/checkout.html"

    def get_template_names(self):
        if is_htmx(self.request):
            return ["orders/_checkout_form.html"]
        return [self.template_name]

    def get_initial(self):
        # Use what the customer typed before if they came back from the summary, else the profile.
        saved = self.request.session.get(DELIVERY_SESSION_KEY)
        if saved:
            return saved
        user = self.request.user
        return {
            "name": f"{user.first_name} {user.last_name}".strip(),
            "address": user.default_address,
            "city": user.default_city,
            "phone": user.phone,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.cart)
        return context

    def form_valid(self, form):
        self.request.session[DELIVERY_SESSION_KEY] = form.cleaned_data
        return redirect_to(self.request, reverse("checkout_summary"))


class CheckoutSummaryView(CheckoutGuardMixin, TemplateView):
    """US-21: read-only order summary with the "Place order" button (the order itself is US-22)."""

    template_name = "orders/summary.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and DELIVERY_SESSION_KEY not in request.session:
            return redirect("checkout")  # delivery details come first
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.cart)
        context["delivery"] = self.request.session[DELIVERY_SESSION_KEY]
        return context


class OrderProblem(Exception):
    """Raised inside the transaction when the cart cannot be turned into an order; it rolls everything back."""

    def __init__(self, problems):
        super().__init__("; ".join(problems))
        self.problems = problems


class PlaceOrderView(CustomerRequiredMixin, View):
    """US-22: turn the cart into an order, all inside one transaction (SPEC 6.2).

    1. lock the species rows; 2. re-check stock (if anything is short, roll back and create nothing);
    3. create the Order and OrderItems with name and price copied in; 4. lower the stock;
    5. empty the cart. After the commit: print a confirmation email and show the confirmation page.
    """

    http_method_names = ["post"]

    def post(self, request):
        delivery = request.session.get(DELIVERY_SESSION_KEY)
        if not delivery:
            return redirect("checkout")
        try:
            order = self.place_order(request.user, delivery, self.profile_for_order(request))
        except OrderProblem as problem:
            for line in problem.problems:
                messages.error(request, line)
            return redirect("cart")

        # Order placed: forget the checkout state, then confirm.
        request.session.pop(DELIVERY_SESSION_KEY, None)
        request.session.pop("grow_profile_id", None)
        return redirect(f"{reverse('order_detail', args=[order.pk])}?placed=1")

    @staticmethod
    def profile_for_order(request):
        """The grow profile the customer came from (set when adding from match results), if still theirs."""
        profile_id = request.session.get("grow_profile_id")
        return GrowProfile.objects.filter(pk=profile_id, customer=request.user).first() if profile_id else None

    @staticmethod
    def place_order(user, delivery, profile):
        with transaction.atomic():
            cart_items = list(CartItem.objects.filter(customer=user).select_related("species"))
            if not cart_items:
                raise OrderProblem(["Your cart is empty."])
            # 1. Lock the species rows so two checkouts cannot sell the same last plant.
            locked = {s.pk: s for s in Species.objects.select_for_update().filter(pk__in=[i.species_id for i in cart_items])}

            # 2. Re-check against the locked, current values.
            problems = []
            for item in cart_items:
                species = locked[item.species_id]
                if species.is_deleted or species.status != Species.Status.ACTIVE or species.is_invasive:
                    problems.append(f"{species.common_name} is no longer available. Please remove it.")
                elif item.quantity > species.stock:
                    problems.append(f"Only {species.stock} {species.common_name} left. Please lower the quantity.")
            if problems:
                raise OrderProblem(problems)  # leaves the atomic block, so nothing is saved

            # 3. Order and lines, copying the name and price paid.
            order = Order.objects.create(
                customer=user, grow_profile=profile,
                delivery_name=delivery["name"], delivery_address=delivery["address"],
                delivery_city=delivery["city"], delivery_phone=delivery["phone"],
                payment_method=Order.PaymentMethod.COD, total=0,
            )
            total = 0
            for item in cart_items:
                species = locked[item.species_id]
                OrderItem.objects.create(order=order, species=species, species_name=species.common_name,
                                         unit_price=species.price, quantity=item.quantity)
                total += species.price * item.quantity
                # 4. Lower the stock.
                species.stock -= item.quantity
                species.save(update_fields=["stock"])
            order.total = total
            order.save(update_fields=["total"])

            # 5. Empty the cart.
            CartItem.objects.filter(customer=user).delete()

            # 6. Only once the transaction has really committed, send the confirmation email.
            transaction.on_commit(lambda: send_confirmation_email(order))
        return order


def send_confirmation_email(order):
    """Print (console backend) or send the order confirmation. A mail problem never undoes an order."""
    lines = "\n".join(f"  {i.quantity} x {i.species_name} @ Rs {i.unit_price:,.0f} = Rs {i.line_total:,.0f}"
                      for i in order.items.all())
    body = (
        f"Hello {order.delivery_name},\n\nThank you for your Basera order {order.number}.\n\n{lines}\n\n"
        f"Total: Rs {order.total:,.0f} (Cash on Delivery)\n\n"
        f"Deliver to:\n  {order.delivery_name}\n  {order.delivery_address}\n  {order.delivery_city}\n"
        f"  {order.delivery_phone}\n\nThe Basera team\n"
    )
    send_mail(f"Basera order {order.number} confirmed", body, None, [order.customer.email], fail_silently=True)


class OrderListView(CustomerRequiredMixin, ListView):
    """US-23: "My Orders", newest first (only the logged-in customer's own orders)."""

    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).order_by("-created_at", "-id")


class OrderDetailView(CustomerRequiredMixin, DetailView):
    """US-23: one order - items, delivery details, status and the grow profile used (if any).

    Doubles as the confirmation page after checkout (?placed=1, US-22).
    Another customer's order is simply not found (404).
    """

    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).select_related("grow_profile__region").prefetch_related("items")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["just_placed"] = self.request.GET.get("placed") == "1"
        return context
