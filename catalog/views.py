"""Public catalogue views (US-18, US-12)."""

from django.db.models import Q
from django.views.generic import DetailView, ListView

from basera.htmx import is_htmx

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
