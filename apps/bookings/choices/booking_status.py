from django.db import models


class BookingStatusChoices(models.IntegerChoices):
    PENDING = 1, 'Pending'
    REQUEST = 2, 'Request'
    CONFIRMED = 3, 'Confirmed'
    COMPLETED = 4, 'Completed'
    CANCELED = 5, 'Canceled'
    DELETED = 6, 'Deleted'


class BookingStatusColors(models.IntegerChoices):
    YELLOW = 1, 'yellow'
    BLUE = 2, 'blue'
    GREEN = 3, 'green'
    GRAY = 4, 'gray'
    RED = 5, 'red'
