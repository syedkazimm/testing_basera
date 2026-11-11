"""Project URL routes. Each app owns its own urls.py (added story by story)."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from django.views.generic import TemplateView

admin.site.site_header = "Basera administration"
admin.site.site_title = "Basera admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("profiles/", include("growprofiles.urls")),
    path("match/", include("matching.urls")),
    path("cart/", include("orders.urls")),
    path("checkout/", include("orders.checkout_urls")),
    path("orders/", include("orders.order_urls")),
    path("seller/orders/", include("orders.seller_urls")),
    path("", include("catalog.urls")),
    # Home page (EN-01)
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]

# Uploaded species images. A small demo site serves them straight from MEDIA_ROOT, in production too
# (the free host's disk is ephemeral, so they may vanish on redeploy - see the README).
urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]
