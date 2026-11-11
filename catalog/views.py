"""Catalogue views: public browsing (US-18, US-12) and the seller's listings (US-13 onwards)."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import SellerRequiredMixin
from basera.htmx import is_htmx, redirect_to

from .forms import SpeciesForm
from .models import Species


class CatalogueView(ListView):
    """US-18 (+ US-10 warning): browse and search visible species, 12 per page.

    The results block is its own partial so HTMX can swap only that block (added in the
    Sprint 1 wrap-up); a normal request renders the full page that includes the same partial.
    """

    paginate_by = 12
    context_object_name = "species_list"

    def get_queryset(self):
        queryset = Species.objects.visible().order_by("common_name")
        self.query = self.request.GET.get("q", "").strip()
        if self.query:
            queryset = queryset.filter(
                Q(common_name__icontains=self.query) | Q(scientific_name__icontains=self.query)
            )
        return queryset

    def get_template_names(self):
        if is_htmx(self.request):
            return ["catalog/_species_results.html"]
        return ["catalog/catalogue.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        return context


class SpeciesDetailView(DetailView):
    """US-12: details of one species. Inactive or removed species give a 404.

    Invasive species get a warning banner and (in Sprint 2) no add-to-cart button.
    """

    context_object_name = "species"
    template_name = "catalog/species_detail.html"

    def get_queryset(self):
        return Species.objects.visible().select_related("seller").prefetch_related("regions")


# --- Seller side ---------------------------------------------------------------------------------
class OwnListingMixin(SellerRequiredMixin):
    """Loads one listing for a seller. Removed listings are a 404; another seller's is a 403."""

    def get_object(self, queryset=None):
        listing = get_object_or_404(Species, pk=self.kwargs["pk"], is_deleted=False)
        if listing.seller_id != self.request.user.pk:
            raise PermissionDenied
        return listing


class ListingListView(SellerRequiredMixin, ListView):
    """US-13 / US-16: "My Listings" - only the logged-in seller's own, non-removed listings."""

    template_name = "catalog/seller_listing_list.html"
    context_object_name = "listings"

    def get_queryset(self):
        return Species.objects.filter(seller=self.request.user, is_deleted=False).order_by("common_name")


class ListingFormMixin:
    """Shared by create (US-13) and edit (US-14).

    HTMX: validation errors re-render only the form partial (status 200); success redirects.
    """

    form_class = SpeciesForm
    template_name = "catalog/listing_form.html"
    success_url = reverse_lazy("listing_list")
    heading = ""

    def get_template_names(self):
        if is_htmx(self.request):
            return ["catalog/_listing_form.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = self.heading
        context["form_action"] = self.request.path
        return context

    def form_valid(self, form):
        form.instance.seller = self.request.user  # never taken from the form
        form.save()
        messages.success(self.request, "Listing saved.")
        return redirect_to(self.request, str(self.success_url))


class ListingCreateView(SellerRequiredMixin, ListingFormMixin, CreateView):
    """US-13: create a listing. It starts ACTIVE and is visible in the catalogue at once."""

    heading = "New listing"
