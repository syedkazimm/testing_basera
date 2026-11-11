"""Tiny helpers for the HTMX pattern in SPEC 8.1: one URL serves a full page or a partial."""

from django.http import HttpResponse
from django.shortcuts import redirect


def is_htmx(request):
    """True when the request was made by HTMX (so only a partial should be rendered).

    When the browser's Back button restores a page, HTMX re-requests it and sends both headers;
    that needs the FULL page, so it is not treated as a partial request.
    """
    return bool(request.headers.get("HX-Request")) and not request.headers.get("HX-History-Restore-Request")


def redirect_to(request, url):
    """Redirect normally, or with the HX-Redirect header when the request came from HTMX."""
    if is_htmx(request):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = url
        return response
    return redirect(url)
