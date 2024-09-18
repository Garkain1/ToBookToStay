from django.contrib import admin
from ..choices import BookingStatusChoices


@admin.action(description='Mark selected bookings as Requested')
def make_requested(modeladmin, request, queryset):
    queryset.update(status=BookingStatusChoices.REQUEST)
    modeladmin.message_user(request, "Selected bookings have been marked as Requested.")


@admin.action(description='Confirm selected bookings')
def make_confirmed(modeladmin, request, queryset):
    queryset.update(status=BookingStatusChoices.CONFIRMED)
    modeladmin.message_user(request, "Selected bookings have been confirmed.")


@admin.action(description='Complete selected bookings')
def make_completed(modeladmin, request, queryset):
    queryset.update(status=BookingStatusChoices.COMPLETED)
    modeladmin.message_user(request, "Selected bookings have been completed.")


@admin.action(description='Cancel selected bookings')
def make_canceled(modeladmin, request, queryset):
    queryset.update(status=BookingStatusChoices.CANCELED)
    modeladmin.message_user(request, "Selected bookings have been canceled.")


@admin.action(description='Soft delete selected bookings')
def make_deleted(modeladmin, request, queryset):
    queryset.update(status=BookingStatusChoices.DELETED)
    modeladmin.message_user(request, "Selected bookings have been soft deleted.")