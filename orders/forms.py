"""Checkout forms (US-21)."""

from django import forms

from accounts.validators import phone_validator
from basera.forms import BootstrapFormMixin


class DeliveryForm(BootstrapFormMixin, forms.Form):
    """Where the plants go. Prefilled from the customer's profile; payment is always Cash on Delivery."""

    name = forms.CharField(label="Full name", max_length=120)
    address = forms.CharField(label="Delivery address", widget=forms.Textarea(attrs={"rows": 3}))
    city = forms.CharField(max_length=60)
    phone = forms.CharField(
        label="Mobile number", max_length=20, validators=[phone_validator],
        help_text="For example 03001234567 or +923001234567.",
    )
