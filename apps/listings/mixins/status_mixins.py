from django.utils.html import format_html
from ..choices import ListingStatusChoices, ListingStatusColors


class StatusMixin:
    def status_display(self, obj):
        colors = {key: value for key, value in ListingStatusColors.choices}
        statuses = {key: value for key, value in ListingStatusChoices.choices if key != ListingStatusChoices.DELETED}

        if obj.status == ListingStatusChoices.DELETED:
            return '-'

        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            statuses.get(obj.status, '-')
        )

    status_display.short_description = 'Status'


class SoftDeleteMixin:
    def is_soft_deleted(self, obj):
        return obj.status == ListingStatusChoices.DELETED
    is_soft_deleted.boolean = True
    is_soft_deleted.short_description = 'Soft deleted'
