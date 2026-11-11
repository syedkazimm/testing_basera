"""Seller forms for species listings (US-13, US-14, US-15)."""

from django import forms

from basera.forms import BootstrapFormMixin
from growprofiles.models import Purpose, Region

from .models import Species

MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB
ALLOWED_IMAGE_FORMATS = ("JPEG", "PNG")


class SpeciesForm(BootstrapFormMixin, forms.ModelForm):
    """Create or edit a listing. Sellers can never set `is_invasive` (admin only) or `seller`."""

    purposes = forms.MultipleChoiceField(
        choices=Purpose.choices, widget=forms.CheckboxSelectMultiple,
        help_text="Tick every purpose this plant is good for.",
    )
    regions = forms.ModelMultipleChoiceField(
        queryset=Region.objects.all(), widget=forms.CheckboxSelectMultiple,
        label="Native regions", help_text="Choose at least one region where this plant is native.",
    )

    class Meta:
        model = Species
        fields = [
            "common_name", "scientific_name", "description", "image", "price", "stock", "status",
            "sunlight", "water", "soil", "setting", "plant_type", "purposes",
            "ecological_benefit", "regions",
        ]
        labels = {"sunlight": "Preferred sunlight", "water": "Water needed", "soil": "Preferred soil",
                  "setting": "Grows", "plant_type": "Plant type", "image": "Photo",
                  "stock": "Stock (plants in hand)", "status": "Availability"}
        help_texts = {
            "image": "JPG or PNG, up to 2 MB. A placeholder is shown if you skip this.",
            "soil": "Choose loam if the plant is adaptable to most soils.",
            "price": "In Pakistani rupees.",
            "stock": "Set to 0 to show \"Out of stock\". Stock goes down automatically when orders are placed.",
            "status": "Inactive listings are hidden from customers; switch back to Active any time.",
        }
        widgets = {"description": forms.Textarea(attrs={"rows": 4}),
                   "ecological_benefit": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # The model stores purposes as "FOOD,POLLINATOR"; the checkboxes want a list.
            self.initial["purposes"] = self.instance.purposes_list
        self.fields["price"].min_value = None  # validated by clean_price below with a clearer message

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Price must be more than zero.")
        return price

    def clean_purposes(self):
        return ",".join(self.cleaned_data["purposes"])

    def clean_image(self):
        """Only JPG/PNG pictures up to 2 MB. (No new upload, or "clear", passes straight through.)"""
        image = self.cleaned_data.get("image")
        if not image or not hasattr(image, "image"):  # empty, cleared, or the existing file
            return image
        if image.size > MAX_IMAGE_BYTES:
            raise forms.ValidationError("The image is larger than 2 MB.")
        if image.image.format not in ALLOWED_IMAGE_FORMATS:
            raise forms.ValidationError("Only JPG or PNG images are allowed.")
        return image
