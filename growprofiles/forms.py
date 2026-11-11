"""Forms for grow profiles (US-06)."""

from django import forms

from basera.forms import BootstrapFormMixin

from .models import GrowProfile


class GrowProfileForm(BootstrapFormMixin, forms.ModelForm):
    """Name, region and the growing conditions. The customer is set by the view, never by the form."""

    class Meta:
        model = GrowProfile
        fields = ["name", "region", "space_type", "sunlight", "soil", "water", "purpose"]
