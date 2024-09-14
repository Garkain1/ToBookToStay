from django.core.exceptions import ValidationError


def validate_alphanumeric(value):
    if not value.isalnum():
        raise ValidationError("Username must contain only letters and numbers.")
