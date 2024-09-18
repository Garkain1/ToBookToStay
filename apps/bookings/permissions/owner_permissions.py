from rest_framework.permissions import BasePermission


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
    Разрешает доступ к бронированию только владельцу листинга, к которому оно относится.
    """

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
