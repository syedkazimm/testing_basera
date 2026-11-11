"""Tiny helpers for the HTMX pattern in SPEC 8.1: one URL serves a full page or a partial."""

from django.http import HttpResponse
from django.shortcuts import redirect


def is_htmx(request):
    """True when the request was made by HTMX (so only a partial should be rendered)."""
    return bool(request.headers.get("HX-Request"))


def redirect_to(request, url):
    """Redirect normally, or with the HX-Redirect header when the request came from HTMX."""
    if is_htmx(request):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = url
        return response
    return redirect(url)
