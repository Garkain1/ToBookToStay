from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MinLengthValidator
from ..choices import ListingStatusChoices, PropertyTypeChoices


class Listing(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='listings',
        on_delete=models.CASCADE,
        limit_choices_to={'is_business_account': True}
    )
    title = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(10)]
    )
    description = models.CharField(max_length=500)
    location = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    property_type = models.CharField(
        max_length=20,
        choices=PropertyTypeChoices.ordered_choices(),
        default=PropertyTypeChoices.OTHER
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    rooms = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.IntegerField(
        choices=ListingStatusChoices.choices,
        default=ListingStatusChoices.DRAFT,
        db_index=True
    )
    status_changed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['price']),
            models.Index(fields=['location']),
            models.Index(fields=['rooms']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return self.title

    def soft_delete(self):
        self._change_status(ListingStatusChoices.DELETED)

    def activate(self):
        self._change_status(ListingStatusChoices.ACTIVE)

    def deactivate(self):
        self._change_status(ListingStatusChoices.DEACTIVATED)

    def _change_status(self, new_status):
        if self.status != new_status:
            self.status = new_status
            self.save()
