from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_positive(value):
    if value <= 0:
        raise ValidationError(
            _("%(value)s must be a positive number (greater than zero)"),
            params={"value": value},
        )
