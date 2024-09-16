from django.db import models


class ListingStatusChoices(models.IntegerChoices):
    DRAFT = 0, 'Draft'
    ACTIVE = 1, 'Active'
    DEACTIVATED = 2, 'Deactivated'
    DELETED = 3, 'Deleted'


class ListingStatusColors(models.IntegerChoices):
    GRAY = 0, 'gray'
    GREEN = 1, 'green'
    RED = 2, 'red'
