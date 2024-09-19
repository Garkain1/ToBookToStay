from rest_framework.permissions import BasePermission
from apps.listings.models import Listing


class IsBookingOwner(BasePermission):
    """
    Разрешает доступ к бронированию только владельцу этого бронирования.
    """

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user or request.user.is_staff

    def has_permission(self, request, view):
        # Проверка для создания бронирования
        return request.user.is_authenticated


class IsListingOwner(BasePermission):
    """
    Дает доступ к бронированиям только владельцу хотя бы одного листинга.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and Listing.objects.filter(owner=request.user).exists()

    def has_object_permission(self, request, view, obj):
        return request.user == obj.listing.owner or request.user.is_staff


class IsAdminOrBookingOwnerOrListingOwner(BasePermission):
    """
    Дает доступ к бронированию только администратору, владельцу бронирования или владельцу листинга.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.user == obj.user or
            request.user == obj.listing.owner or
            request.user.is_staff
        )
