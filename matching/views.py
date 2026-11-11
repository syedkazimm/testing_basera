"""Matching views (US-08, US-09, US-10, US-11)."""

from urllib.parse import urlencode

from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from accounts.mixins import CustomerRequiredMixin
from basera.htmx import is_htmx
from growprofiles.models import GrowProfile, Purpose

from .services import FILTER_LABELS, SORTS, apply_filters, find_matches, parse_filters, relax_suggestions


class MatchView(CustomerRequiredMixin, TemplateView):
    """US-08: the ranked shortlist for one of the customer's grow profiles, with US-11 filters.

    Another customer's profile gives a 404. HTMX requests get a partial: just the shortlist when
    a filter control changed (HX-Target "results"), or the filters plus shortlist when the
    "Clear filters" link or a chip was clicked (HX-Target "shortlist") so the controls reset too.
    """

    template_name = "matching/match.html"

    def get_template_names(self):
        if is_htmx(self.request):
            if self.request.headers.get("HX-Target") == "results":
                return ["matching/_results.html"]
            return ["matching/_shortlist.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(
            GrowProfile.objects.select_related("region"), pk=self.kwargs["profile_id"], customer=self.request.user
        )
        filters = parse_filters(self.request.GET)
        sort = self.request.GET.get("sort", "score")
        sort = sort if sort in SORTS else "score"

        all_results = find_matches(profile)  # scored once, then filtered
        results = apply_filters(all_results, filters, sort)
        context.update(
            profile=profile,
            results=results,
            filters=filters,
            sort=sort,
            chips=self.build_chips(filters, sort),
            suggestions=relax_suggestions(all_results, filters) if filters and not results else [],
            total_count=len(all_results),
            purposes=Purpose.choices,
            max_price_value=self.request.GET.get("max_price", "") if "max_price" in filters else "",
        )
        return context

    def build_chips(self, filters, sort):
        """One removable chip per active filter: its label and the URL without that filter."""
        chips = []
        for key, value in filters.items():
            keep = {k: v for k, v in filters.items() if k != key}
            if sort != "score":
                keep["sort"] = sort
            if key == "purpose":
                text = f"Purpose: {Purpose(value).label}"
            elif key == "setting":
                text = f"{value.title()} only"
            else:
                text = f"Up to Rs {value:,.0f}"
            chips.append({"text": text, "url": "?" + urlencode(keep)})
        return chips
