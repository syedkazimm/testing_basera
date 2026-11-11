"""Regions and the shared choice lists used by grow profiles and species (EN-02)."""

from django.conf import settings
from django.db import models


class SpaceType(models.TextChoices):
    INDOOR = "INDOOR", "Indoor"
    OUTDOOR = "OUTDOOR", "Outdoor"


class Sunlight(models.TextChoices):
    FULL_SUN = "FULL_SUN", "Full sun"
    PARTIAL_SHADE = "PARTIAL_SHADE", "Partial shade"
    SHADE = "SHADE", "Shade"


class Soil(models.TextChoices):
    SANDY = "SANDY", "Sandy"
    LOAM = "LOAM", "Loam"
    CLAY = "CLAY", "Clay"
    ROCKY = "ROCKY", "Rocky"


class Water(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"


class Purpose(models.TextChoices):
    SHADE_COOLING = "SHADE_COOLING", "Shade and cooling"
    FOOD = "FOOD", "Food"
    POLLINATOR = "POLLINATOR", "Pollinator support"
    EROSION_CONTROL = "EROSION_CONTROL", "Erosion control"
    ORNAMENTAL = "ORNAMENTAL", "Ornamental"
    MEDICINAL = "MEDICINAL", "Medicinal"


class Region(models.Model):
    """A growing region of Pakistan. Regions in use cannot be deleted (PROTECT on references)."""

    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class GrowProfile(models.Model):
    """A customer's description of their growing space (US-06). Used to match native species."""

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="grow_profiles")
    name = models.CharField(max_length=80, help_text='For example "Balcony" or "Backyard".')
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="grow_profiles")
    space_type = models.CharField("Indoor or outdoor", max_length=10, choices=SpaceType.choices)
    sunlight = models.CharField(max_length=20, choices=Sunlight.choices)
    soil = models.CharField(max_length=10, choices=Soil.choices)
    water = models.CharField("Water you can provide", max_length=10, choices=Water.choices)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.customer})"
