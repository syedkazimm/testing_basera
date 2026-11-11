"""Admin for regions (EN-02; friendly delete handling is added in US-17)."""

from django.contrib import admin

from .models import Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]
