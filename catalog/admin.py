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
    list_editable = ["is_invasive", "status"]  # quick moderation: flag invasive, deactivate
    actions = ["deactivate", "flag_invasive"]

    @admin.action(description="Deactivate selected listings")
    def deactivate(self, request, queryset):
        updated = queryset.update(status=Species.Status.INACTIVE)
        self.message_user(request, f"{updated} listing(s) deactivated.")

    @admin.action(description="Flag selected species as invasive")
    def flag_invasive(self, request, queryset):
        updated = queryset.update(is_invasive=True)
        self.message_user(request, f"{updated} species flagged as invasive.")
