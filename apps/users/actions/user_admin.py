from ..choices import UserStatusChoices


def make_active(modeladmin, request, queryset):
    queryset.update(status=UserStatusChoices.ACTIVE)


make_active.short_description = 'Mark selected users as Active'


def make_pending(modeladmin, request, queryset):
    queryset.update(status=UserStatusChoices.PENDING)


make_pending.short_description = 'Mark selected users as Pending'


def make_deactivated(modeladmin, request, queryset):
    queryset.update(status=UserStatusChoices.DEACTIVATED)


make_deactivated.short_description = 'Mark selected users as Deactivated'


def make_deleted(modeladmin, request, queryset):
    queryset.update(status=UserStatusChoices.DELETED)


make_deleted.short_description = 'Mark selected users as Deleted (Soft Delete)'
