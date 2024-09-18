from django.contrib import admin
from ..actions import make_requested, make_confirmed, make_completed, make_canceled, make_deleted
from ..models import Booking
from ..forms import BookingAdminForm
from ..mixins import StatusMixin, SoftDeleteMixin


@admin.register(Booking)
class BookingAdmin(StatusMixin, SoftDeleteMixin, admin.ModelAdmin):
    form = BookingAdminForm
    list_display = ('__str__', 'listing', 'user', 'start_date', 'end_date', 'status_display', 'total_price', 'is_soft_deleted', 'created_at')
    list_filter = ('status', 'created_at', 'listing__owner')
    search_fields = ('listing__title', 'user__username', 'listing__owner__username')
    readonly_fields = ('total_price', 'status_changed_at', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('listing', 'user', 'start_date', 'end_date')}),
        ('Price', {'fields': ('total_price',)}),
        ('Status', {'fields': ('status_choice', 'is_soft_deleted', 'status_changed_at')}),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )
    actions = [make_requested, make_confirmed, make_completed, make_canceled, make_deleted]
