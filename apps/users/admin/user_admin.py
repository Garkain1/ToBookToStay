from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from ..models import User
from ..forms import UserAdminForm
from ..mixins import PasswordMixin, StatusMixin, SoftDeleteMixin
from ..actions import make_active, make_pending, make_deactivated, make_deleted


@admin.register(User)
class UserAdmin(StatusMixin, SoftDeleteMixin, PasswordMixin, BaseUserAdmin):
    form = UserAdminForm
    change_password_form = AdminPasswordChangeForm
    list_display = ('email', 'username', 'is_business_account', 'is_staff', 'status_display', 'is_soft_deleted')
    list_filter = ('is_staff', 'status', 'is_business_account')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username',)}),
        ('Permissions', {'fields': ('is_staff', 'is_business_account')}),
        ('Status', {'fields': ('status_choice', 'is_soft_deleted', 'status_changed_at')}),
        ('Metadata', {'fields': ('last_login', 'created_at')}),
    )
    readonly_fields = ('status_changed_at', 'last_login', 'created_at',)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'username')
    ordering = ('email',)
    actions = [make_active, make_pending, make_deactivated, make_deleted]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
