import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordValidator:
    """
    Enforces: minimum 6 characters, at least one uppercase, one lowercase,
    and one numeric digit. Plugs into AUTH_PASSWORD_VALIDATORS so it runs
    automatically anywhere Django's validate_password() is called
    (signup, password reset, admin, allauth).
    """

    def __init__(self, min_length=6):
        self.min_length = min_length

    def validate(self, password, user=None):
        errors = []
        if len(password) < self.min_length:
            errors.append(_(f"Password must be at least {self.min_length} characters long."))
        if not re.search(r'[A-Z]', password):
            errors.append(_("Password must contain at least one uppercase letter."))
        if not re.search(r'[a-z]', password):
            errors.append(_("Password must contain at least one lowercase letter."))
        if not re.search(r'\d', password):
            errors.append(_("Password must contain at least one number."))
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            f"Your password must be at least {self.min_length} characters long and include "
            "one uppercase letter, one lowercase letter, and one number."
        )


def normalize_username(username: str) -> str:
    """Canonical lowercase form used for case-insensitive uniqueness checks."""
    return (username or "").strip().lower()


def username_taken(username: str, exclude_pk=None) -> bool:
    """Case-insensitive username existence check (SQLite has no native citext)."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    qs = User.objects.filter(username__iexact=username.strip())
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def email_taken(email: str, exclude_pk=None) -> bool:
    """Case-insensitive email existence check."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    qs = User.objects.filter(email__iexact=email.strip())
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
