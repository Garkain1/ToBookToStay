from django.template.response import TemplateResponse
from django.utils.html import escape
from django.contrib.admin.utils import unquote
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import helpers
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.urls import path


def get_custom_urls(admin_instance):
    return [
        path(
            '<id>/password/',
            admin_instance.admin_site.admin_view(admin_instance.change_password),
            name='auth_user_password_change',
        ),
    ]


def change_password(admin_instance, request, id, form_url=''):
    if not admin_instance.has_change_permission(request):
        raise PermissionDenied
    user = admin_instance.get_object(request, unquote(id))
    if user is None:
        raise Http404(_('The user with the specified key %(key)r does not exist.') % {'key': escape(id)})

    if request.method == 'POST':
        form = admin_instance.change_password_form(user, request.POST)
        if form.is_valid():
            form.save()
            msg = _('Password has been successfully changed.')
            messages.success(request, msg)
            return HttpResponseRedirect(reverse(
                '%s:%s_%s_change' % (admin_instance.admin_site.name,
                                     admin_instance.model._meta.app_label,
                                     admin_instance.model._meta.model_name),
                args=(user.pk,),
                ))
    else:
        form = admin_instance.change_password_form(user)

    fieldsets = [(None, {'fields': list(form.base_fields)})]
    admin_form = helpers.AdminForm(form, fieldsets, {})

    context = {
        **admin_instance.admin_site.each_context(request),
        'title': _('Change password: %s') % escape(user.get_username()),
        'adminForm': admin_form,
        'form_url': form_url,
        'form': form,
        'is_popup': '_popup' in request.GET,
        'add': False,
        'change': False,
        'has_view_permission': admin_instance.has_view_permission(request, user),
        'has_add_permission': admin_instance.has_add_permission(request),
        'has_change_permission': admin_instance.has_change_permission(request, user),
        'has_delete_permission': admin_instance.has_delete_permission(request, user),
        'opts': admin_instance.model._meta,
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
