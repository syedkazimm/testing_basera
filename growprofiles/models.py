"""Regions and the shared choice lists used by grow profiles and species (EN-02)."""

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
