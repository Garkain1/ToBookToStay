from django.contrib import admin
from ..models import Review
from ..forms import ReviewAdminForm
from ..mixins import StatusMixin, SoftDeleteMixin
from ..actions import make_shadow_banned, make_deleted


@admin.register(Review)
class ReviewAdmin(StatusMixin, SoftDeleteMixin, admin.ModelAdmin):
    form = ReviewAdminForm
    list_display = ('__str__', 'reviewer', 'listing', 'rating', 'status_display', 'is_soft_deleted')
    list_filter = ('status', 'rating', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('reviewer', 'listing', 'rating', 'comment')}),
        ('Status', {'fields': ('status_choice', 'is_soft_deleted', 'status_changed_at')}),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )
    search_fields = ('reviewer__username', 'listing__title', 'comment')
    actions = [make_shadow_banned, make_deleted]
    readonly_fields = ('status_changed_at', 'created_at', 'updated_at')
