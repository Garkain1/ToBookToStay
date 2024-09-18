from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from ..choices import BookingStatusChoices


class Booking(models.Model):
    listing = models.ForeignKey(
        'listings.Listing',
        related_name='bookings',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='bookings',
        on_delete=models.CASCADE
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.PositiveSmallIntegerField(
        choices=BookingStatusChoices.choices,
        default=BookingStatusChoices.PENDING,
        db_index=True
    )
    status_changed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)  # Новое поле

    class Meta:
        indexes = [
            models.Index(fields=['listing', 'start_date', 'end_date', 'status']),
        ]
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def __str__(self):
        return f'Booking {self.id} for {self.listing.title}'

    def clean(self):
        if not self.listing_id:
            raise ValidationError("Booking must be associated with a listing.")

        # Проверка последовательности дат
        if self.start_date >= self.end_date:
            raise ValidationError('Start date must be before end date.')

        # Проверка, что дата начала не в прошлом
        if self.start_date < timezone.now().date():
            raise ValidationError('Start date cannot be in the past.')

        # Проверка на 90 дней вперед
        max_booking_date = timezone.now().date() + timedelta(days=90)
        if self.start_date > max_booking_date:
            raise ValidationError('Start date cannot be more than 90 days from today.')

        # Проверка доступности
        if not self.listing.is_available(self.start_date, self.end_date, exclude_booking_id=self.id):
            raise ValidationError('Selected dates are not available.')

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = Booking.objects.get(pk=self.pk)

            # Проверка изменения статуса
            if old_instance.status != self.status:
                self.status_changed_at = timezone.now()

            # Проверка изменения дат или цены
            if old_instance.start_date != self.start_date or old_instance.end_date != self.end_date:
                self.listing.refresh_from_db()
                num_days = (self.end_date - self.start_date).days
                self.total_price = self.listing.price * num_days
        else:
            # Новый объект, всегда рассчитываем total_price
            num_days = (self.end_date - self.start_date).days
            self.total_price = self.listing.price * num_days

        # Проверка и сохранение
        self.full_clean()
        super().save(*args, **kwargs)

    def request(self):
        self._change_status(BookingStatusChoices.REQUEST)

    def confirm(self):
        self._change_status(BookingStatusChoices.CONFIRMED)

    def complete(self):
        self._change_status(BookingStatusChoices.COMPLETED)

    def cancel(self):
        self._change_status(BookingStatusChoices.CANCELED)

    def soft_delete(self):
        self._change_status(BookingStatusChoices.DELETED)

    # Приватный метод для изменения статуса
    def _change_status(self, new_status):
        if self.status != new_status:
            self.status = new_status
            self.status_changed_at = timezone.now()  # Обновляем дату изменения статуса
            super().save(update_fields=['status', 'status_changed_at'])
