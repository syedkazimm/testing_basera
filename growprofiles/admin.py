"""Admin for regions (US-17).

Admins add and edit regions here; new regions show up at once in the grow profile and listing
forms because those forms read the Region table. A region that profiles or species still use
cannot be deleted (their foreign keys are PROTECT) and the admin explains why.
"""

from django.contrib import admin, messages
from django.db.models import Count
from django.db.models.deletion import ProtectedError

from .models import Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "profile_count", "species_count"]
    search_fields = ["name"]

    def get_queryset(self, request):
        # Counts are computed in the same query as the list.
        return super().get_queryset(request).annotate(
            _profiles=Count("grow_profiles", distinct=True), _species=Count("species", distinct=True)
        )

    @admin.display(description="Grow profiles", ordering="_profiles")
    def profile_count(self, obj):
        return obj._profiles

    @admin.display(description="Species", ordering="_species")
    def species_count(self, obj):
        return obj._species

    # Django's delete page already refuses protected regions; these two methods are a safety net so a
    # ProtectedError can never become a 500 error page.
    def delete_model(self, request, obj):
        try:
            super().delete_model(request, obj)
        except ProtectedError:
            self.message_user(
                request, f"Region “{obj}” is still used by grow profiles or species and cannot be deleted.",
                level=messages.ERROR,
            )

    def delete_queryset(self, request, queryset):
        try:
            super().delete_queryset(request, queryset)
        except ProtectedError:
            self.message_user(
                request, "Some of these regions are still used by grow profiles or species and cannot be deleted.",
                level=messages.ERROR,
            )
