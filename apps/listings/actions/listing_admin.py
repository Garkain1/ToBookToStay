from django.contrib import admin
from ..choices import ListingStatusChoices


@admin.action(description='Mark selected listings as Active')
def make_active(modeladmin, request, queryset):
    queryset.update(status=ListingStatusChoices.ACTIVE)
    modeladmin.message_user(request, "Selected listings have been marked as Active.")


@admin.action(description='Mark selected listings as Deactivated')
def make_deactivated(modeladmin, request, queryset):
    queryset.update(status=ListingStatusChoices.DEACTIVATED)
    modeladmin.message_user(request, "Selected listings have been marked as Deactivated.")


@admin.action(description='Soft delete selected listings')
def make_deleted(modeladmin, request, queryset):
    queryset.update(status=ListingStatusChoices.DELETED)
    modeladmin.message_user(request, "Selected listings have been soft deleted.")

