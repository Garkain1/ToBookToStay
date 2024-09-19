from django.contrib import admin
from ..choices import ReviewStatusChoices


@admin.action(description='Mark selected listings as Shadow Banned')
def make_shadow_banned(modeladmin, request, queryset):
    queryset.update(status=ReviewStatusChoices.SHADOW_BANNED)
    modeladmin.message_user(request, "Selected listings have been marked as Shadow Banned.")


@admin.action(description='Soft delete selected listings')
def make_deleted(modeladmin, request, queryset):
    queryset.update(status=ReviewStatusChoices.DELETED)
    modeladmin.message_user(request, "Selected listings have been soft deleted.")
