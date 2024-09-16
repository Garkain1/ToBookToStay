from django.contrib import admin
from ..models import Listing
from ..actions import make_active, make_deactivated, make_deleted
from ..forms import ListingAdminForm
from ..mixins import StatusMixin, SoftDeleteMixin


@admin.register(Listing)
class ListingAdmin(StatusMixin, SoftDeleteMixin, admin.ModelAdmin):
    form = ListingAdminForm
    list_display = ('title', 'owner', 'price', 'property_type', 'location', 'status_display', 'is_soft_deleted')
    list_filter = ('status', 'location', 'rooms', 'property_type', 'status_changed_at', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('title', 'description')}),
        ('Owner', {'fields': ('owner',)}),
        ('Listing Details', {'fields': ('price', 'rooms', 'property_type')}),
        ('Listing Location', {'fields': ('location', 'address')}),
        ('Status', {'fields': ('status_choice', 'is_soft_deleted', 'status_changed_at')}),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )
    search_fields = ('title', 'description', 'owner__username', 'location', 'address')
    actions = [make_active, make_deactivated, make_deleted]
    readonly_fields = ('status_changed_at', 'created_at', 'updated_at')
