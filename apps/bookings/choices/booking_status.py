from django.db import models


class BookingStatusChoices(models.IntegerChoices):
    PENDING = 1, 'Pending'
    REQUEST = 2, 'Request'
    CONFIRMED = 3, 'Confirmed'
    COMPLETED = 4, 'Completed'
    CANCELED = 5, 'Canceled'
    DELETED = 6, 'Deleted'
