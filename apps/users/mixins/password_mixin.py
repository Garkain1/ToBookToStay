from django.template.response import TemplateResponse
from django.utils.html import escape
from django.contrib.admin.utils import unquote
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import helpers
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.core.exceptions import PermissionDenied


class PasswordMixin:
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<id>/password/',
                self.admin_site.admin_view(self.change_password),
                name='auth_user_password_change',
            ),
        ]
        return custom_urls + urls

    def change_password(self, request, id, form_url=''):
        if not self.has_change_permission(request):
            raise PermissionDenied
        user = self.get_object(request, unquote(id))
        if user is None:
            raise Http404(_('The user with the specified key %(key)r does not exist.') % {'key': escape(id)})

        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                msg = _('Password has been successfully changed.')
                messages.success(request, msg)
                return HttpResponseRedirect(reverse(
                    '%s:%s_%s_change' % (self.admin_site.name, self.model._meta.app_label, self.model._meta.model_name),
                    args=(user.pk,),
                ))
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {'fields': list(form.base_fields)})]
        admin_form = helpers.AdminForm(form, fieldsets, {})

        context = {
            **self.admin_site.each_context(request),
            'title': _('Change password: %s') % escape(user.get_username()),
            'adminForm': admin_form,
            'form_url': form_url,
            'form': form,
            'is_popup': '_popup' in request.GET,
            'add': False,
            'change': False,
            'has_view_permission': self.has_view_permission(request, user),
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, user),
            'has_delete_permission': self.has_delete_permission(request, user),
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
            'inline_admin_formsets': [],
        }
        return TemplateResponse(
            request,
            'admin/auth/user/change_password.html',
            context,
        )
