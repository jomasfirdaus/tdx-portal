import re

from django.core.exceptions import ValidationError


class ComplexityValidator:
    """Require at least one uppercase, one lowercase, one digit, one symbol."""

    def validate(self, password, user=None):
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must contain at least one uppercase letter.", code="password_no_upper")
        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must contain at least one lowercase letter.", code="password_no_lower")
        if not re.search(r"[0-9]", password):
            raise ValidationError("Password must contain at least one digit.", code="password_no_digit")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError("Password must contain at least one symbol.", code="password_no_symbol")

    def get_help_text(self):
        return "Your password must include upper- and lower-case letters, a digit, and a symbol."
