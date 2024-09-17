from rest_framework.permissions import BasePermission


class IsBusinessAccount(BasePermission):
    message = 'You must have a business account to perform this action.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_business_account
