"""Customer views for grow profiles (US-06)."""

from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView

from accounts.mixins import CustomerRequiredMixin
from basera.htmx import is_htmx, redirect_to

from .forms import GrowProfileForm
from .models import GrowProfile


class ProfileListView(CustomerRequiredMixin, ListView):
    """US-06 / US-07: the customer's own grow profiles (never anyone else's)."""

    template_name = "growprofiles/profile_list.html"
    context_object_name = "profiles"

    def get_queryset(self):
        return GrowProfile.objects.filter(customer=self.request.user).select_related("region")


class ProfileCreateView(CustomerRequiredMixin, CreateView):
    """US-06: create a grow profile under the logged-in customer.

    HTMX: validation errors re-render only the form partial; success redirects to the list.
    """

    form_class = GrowProfileForm
    template_name = "growprofiles/profile_form.html"
    success_url = reverse_lazy("profile_list")

    def get_template_names(self):
        if is_htmx(self.request):
            return ["growprofiles/_profile_form.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = "New grow profile"
        context["form_action"] = reverse("profile_new")
        return context

    def form_valid(self, form):
        form.instance.customer = self.request.user
        form.save()
        messages.success(self.request, "Grow profile saved.")
        return redirect_to(self.request, str(self.success_url))
