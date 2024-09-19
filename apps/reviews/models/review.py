from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from dirtyfields import DirtyFieldsMixin
from apps.bookings.choices import BookingStatusChoices
from apps.listings.models import Listing
from ..choices import ReviewStatusChoices


class Review(DirtyFieldsMixin, models.Model):
    listing = models.ForeignKey(
        Listing,
        related_name='reviews',
        on_delete=models.CASCADE
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='reviews',
        on_delete=models.CASCADE
    )
    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ],
        null=True,
        blank=True
    )
    comment = models.CharField(max_length=1000, blank=True, null=True)
    status = models.PositiveSmallIntegerField(
        choices=ReviewStatusChoices.choices,
        default=ReviewStatusChoices.VISIBLE,
        db_index=True
    )
    status_changed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['listing', 'reviewer'],
                name='unique_review_per_user_per_listing'
            ),
            models.CheckConstraint(
                check=Q(rating__gte=1) & Q(rating__lte=5),
                name='rating_range_valid'
            )
        ]
        indexes = [
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['listing', 'status']),
        ]
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'

    def __str__(self):
        return f'Review by {self.reviewer.username} for {self.listing.title}'

    def clean(self):
        # Проверка на отсутствие и rating, и comment
        if not self.rating and not self.comment:
            raise ValidationError('Either a rating or a comment is required.')

    def save(self, *args, **kwargs):
        dirty_fields = self.get_dirty_fields()

        # Проверяем, изменился ли статус
        if 'status' in dirty_fields:
            self.status_changed_at = timezone.now()

        super().save(*args, **kwargs)

    def apply_shadow_ban(self):
        self._change_status(ReviewStatusChoices.SHADOW_BANNED)

    def soft_delete(self):
        self._change_status(ReviewStatusChoices.DELETED)

    def _change_status(self, new_status):
        if self.status != new_status:
            self.status = new_status
            self.status_changed_at = timezone.now()  # Обновляем дату изменения статуса
            super().save(update_fields=['status', 'status_changed_at'])

    @classmethod
    def can_user_review(cls, user, listing):
        """Проверяет, может ли пользователь оставить отзыв для данного листинга."""
        has_completed_booking = user.bookings.filter(
            listing=listing,
            status=BookingStatusChoices.COMPLETED
        ).exists()
        has_reviewed = cls.objects.filter(
            listing=listing,
            reviewer=user
        ).exists()
        return has_completed_booking and not has_reviewed
