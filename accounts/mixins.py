"""Permission mixins (SPEC 6.5).

Not logged in  -> redirect to login with ?next= (Django's default).
Wrong role     -> 403 page.
"""

from django.contrib.auth.mixins import UserPassesTestMixin


class CustomerRequiredMixin(UserPassesTestMixin):
    """Only logged-in customers. Sellers and admins get a 403."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_customer


class SellerRequiredMixin(UserPassesTestMixin):
    """Only logged-in sellers. Customers and admins get a 403."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_seller
