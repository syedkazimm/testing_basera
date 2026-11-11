"""Species listings (EN-02). A Species is one seller's plant listing."""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.templatetags.static import static

from growprofiles.models import Purpose, Region, Soil, Sunlight, Water


class SpeciesQuerySet(models.QuerySet):
    def visible(self):
        """Species the public may see: active and not removed. Used by every public page and by matching."""
        return self.filter(status=Species.Status.ACTIVE, is_deleted=False)


class Species(models.Model):
    class Setting(models.TextChoices):
        INDOOR = "INDOOR", "Indoor"
        OUTDOOR = "OUTDOOR", "Outdoor"
        BOTH = "BOTH", "Indoor or outdoor"

    class PlantType(models.TextChoices):
        TREE = "TREE", "Tree"
        SHRUB = "SHRUB", "Shrub"
        HERB = "HERB", "Herb"
        CLIMBER = "CLIMBER", "Climber"
        GRASS = "GRASS", "Grass"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="species")
    common_name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=150)
    description = models.TextField()
    image = models.ImageField(upload_to="species/", blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    stock = models.PositiveIntegerField(default=0)

    # Suitability attributes (same codes as the grow profile).
    sunlight = models.CharField(max_length=20, choices=Sunlight.choices)
    water = models.CharField(max_length=10, choices=Water.choices)
    soil = models.CharField(max_length=10, choices=Soil.choices)
    setting = models.CharField(max_length=10, choices=Setting.choices)
    plant_type = models.CharField(max_length=10, choices=PlantType.choices)
    purposes = models.CharField(max_length=200, help_text="Comma-separated purpose codes.")
    ecological_benefit = models.TextField()

    regions = models.ManyToManyField(Region, through="SpeciesRegion", related_name="species")
    is_invasive = models.BooleanField(default=False, help_text="Only an admin can set this.")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    is_deleted = models.BooleanField(default=False)  # soft delete: past orders keep pointing here
    created_at = models.DateTimeField(auto_now_add=True)

    objects = SpeciesQuerySet.as_manager()

    class Meta:
        ordering = ["common_name"]
        verbose_name_plural = "species"

    def __str__(self):
        return self.common_name

    @property
    def purposes_list(self):
        """The purpose codes as a list, e.g. ["FOOD", "POLLINATOR"]."""
        return [code.strip() for code in self.purposes.split(",") if code.strip()]

    @property
    def purposes_display(self):
        """Human-readable purpose labels, e.g. "Food, Pollinator support"."""
        labels = dict(Purpose.choices)
        return ", ".join(labels.get(code, code) for code in self.purposes_list)

    @property
    def image_url(self):
        """The uploaded image, or the placeholder when there is none."""
        return self.image.url if self.image else static("img/placeholder.png")

    @property
    def in_stock(self):
        return self.stock > 0


class SpeciesRegion(models.Model):
    """Links a species to a region it is native to."""

    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("species", "region")

    def __str__(self):
        return f"{self.species} - {self.region}"
