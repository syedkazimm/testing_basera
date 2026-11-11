"""Shared validators for the accounts app (US-01)."""

from django.core.validators import RegexValidator

# Pakistani mobile number: +923001234567 or 03001234567.
phone_validator = RegexValidator(
    regex=r"^(\+92|0)3\d{9}$",
    message="Enter a Pakistani mobile number like 03001234567 or +923001234567.",
)
