"""Project URL routes. Each app owns its own urls.py (added story by story)."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("profiles/", include("growprofiles.urls")),
    path("match/", include("matching.urls")),
    path("", include("catalog.urls")),
    # Home page (EN-01)
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]

# Serve uploaded images during local development only.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
