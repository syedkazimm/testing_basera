"""Matching views (US-08, US-09, US-10)."""

from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from accounts.mixins import CustomerRequiredMixin
from basera.htmx import is_htmx
from growprofiles.models import GrowProfile

from .services import find_matches


class MatchView(CustomerRequiredMixin, TemplateView):
    """US-08: the ranked shortlist for one of the customer's grow profiles.

    Another customer's profile gives a 404. The results are a partial so HTMX can swap only the
    shortlist (filters arrive in US-11).
    """

    template_name = "matching/match.html"

    def get_template_names(self):
        if is_htmx(self.request):
            return ["matching/_results.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(
            GrowProfile.objects.select_related("region"), pk=self.kwargs["profile_id"], customer=self.request.user
        )
        context["profile"] = profile
        context["results"] = find_matches(profile)
        return context
