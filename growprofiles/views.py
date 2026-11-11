"""Customer views for grow profiles (US-06, US-07)."""

from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.mixins import CustomerRequiredMixin
from basera.htmx import is_htmx, redirect_to

from .forms import GrowProfileForm
from .models import GrowProfile


class OwnProfilesMixin(CustomerRequiredMixin):
    """Always filter by owner: someone else's profile is simply not found (404)."""

    def get_queryset(self):
        return GrowProfile.objects.filter(customer=self.request.user).select_related("region")


class ProfileListView(OwnProfilesMixin, ListView):
    """US-06 / US-07: the customer's own grow profiles."""

    template_name = "growprofiles/profile_list.html"
    context_object_name = "profiles"


class ProfileFormMixin(OwnProfilesMixin):
    """Shared by create (US-06) and edit (US-07).

    HTMX: validation errors re-render only the form partial; success redirects to the list.
    """

    form_class = GrowProfileForm
    template_name = "growprofiles/profile_form.html"
    success_url = reverse_lazy("profile_list")
    heading = ""

    def get_template_names(self):
        if is_htmx(self.request):
            return ["growprofiles/_profile_form.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = self.heading
        context["form_action"] = self.request.path
        return context

    def form_valid(self, form):
        form.instance.customer = self.request.user  # never taken from the form
        form.save()
        messages.success(self.request, "Grow profile saved.")
        return redirect_to(self.request, str(self.success_url))


class ProfileCreateView(ProfileFormMixin, CreateView):
    """US-06: create a grow profile under the logged-in customer."""

    heading = "New grow profile"


class ProfileUpdateView(ProfileFormMixin, UpdateView):
    """US-07: edit one of my profiles. Orders already placed are not affected."""

    heading = "Edit grow profile"


class ProfileDeleteView(OwnProfilesMixin, DeleteView):
    """US-07: delete one of my profiles (orders keep existing; their link is cleared).

    GET shows a confirmation page. HTMX users get a browser confirm instead (hx-confirm) and the
    row simply disappears: the view answers an HTMX delete with an empty body.
    """

    template_name = "growprofiles/profile_confirm_delete.html"
    success_url = reverse_lazy("profile_list")
    context_object_name = "profile"

    def form_valid(self, form):
        name = self.object.name
        self.object.delete()
        if is_htmx(self.request):
            return HttpResponse("")  # swapped in place of the table row
        messages.success(self.request, f"Grow profile “{name}” deleted.")
        return redirect_to(self.request, str(self.success_url))
