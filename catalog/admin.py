"""Admin for species so seeded data can be inspected and invasive species flagged (EN-02)."""

from django.contrib import admin

from .models import Species, SpeciesRegion


class SpeciesRegionInline(admin.TabularInline):
    model = SpeciesRegion
    extra = 1


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ["common_name", "scientific_name", "seller", "price", "stock", "status", "is_invasive", "is_deleted"]
    list_filter = ["status", "is_invasive", "is_deleted", "plant_type", "regions"]
    search_fields = ["common_name", "scientific_name"]
    inlines = [SpeciesRegionInline]
    exclude = []
