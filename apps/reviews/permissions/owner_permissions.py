from rest_framework.permissions import BasePermission
from apps.listings.choices import ListingStatusChoices
from ..choices import ReviewStatusChoices


class IsReviewerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.listing.status != ListingStatusChoices.ACTIVE:
            return False

        # Проверяем, что статус отзыва не 'DELETE'
        if obj.status == ReviewStatusChoices.DELETE:
            return False

        return obj.reviewer == request.user or request.user.is_staff
