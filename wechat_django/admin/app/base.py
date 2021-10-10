import base64
from urllib.parse import parse_qsl

from django import forms
from django.contrib import admin
from django.contrib.admin.filters import ChoicesFieldListFilter
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.http.response import Http404
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from wechat_django.enums import AppType
from wechat_django.models.apps import Application
from wechat_django.utils.crypto import crypto
from wechat_django.utils.form import ModelForm


BINARY_FIELDS = ("appsecret", "api_key")
ENCRYPTED_FIELDS = ("appsecret", "encoding_aes_key", "token", "api_key")


class ApplicationChangeList(ChangeList):
    def url_for_result(self, result):
        for cls in result.__class__.mro():
            if cls in self.model_admin.admin_site._registry:
                break
        return reverse("admin:{0}_{1}_change".format(cls._meta.app_label,
                                                     cls._meta.model_name),
                       args=(result.pk,))


class ParentApplicationFilter(admin.SimpleListFilter):
    parameter_name = "parent_id"
    title = _("Parent application")
    template = "admin/hidden_filter.html"

    def lookups(self, request, model_admin):
        # TODO: 权限把控
        return Application.objects.filter(
            type=model_admin.parent_type
        ).values_list("pk", "title")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(parent_id=self.value())
        else:
            raise Http404


class ApplicationTypeFilter(ChoicesFieldListFilter):
    def __init__(self, field, request, params, model, model_admin,
                 field_path):
        super().__init__(field, request, params, model, model_admin,
                         field_path)
        self.model = model
        self.model_admin = model_admin

    def choices(self, changelist):
        yield {
            'selected': self.lookup_val is None,
            'query_string': changelist.get_query_string(
                remove=[self.lookup_kwarg, self.lookup_kwarg_isnull]),
            'display': _('All')
        }
        for lookup, title in self.field.flatchoices:
            if lookup in self.model_admin.query_app_types:
                yield {
                    'selected': str(lookup) == self.lookup_val,
                    'query_string': changelist.get_query_string(
                        {self.lookup_kwarg: lookup},
                        [self.lookup_kwarg_isnull]),
                    'display': title,
                }


class EncryptedField(forms.CharField):
    """加密存储"""

    @property
    def initial(self):
        return self._initial

    @initial.setter
    def initial(self, value):
        if not value:
            value = b"" if self.raw else ""
        self._initial = value

    def __init__(self, *args, **kwargs):
        self.raw = kwargs.pop("raw", False)
        super().__init__(*args, **kwargs)

    def has_changed(self, initial, data):
        return self._has_changed(initial, data)\
               and self.clean(data) != initial

    def prepare_value(self, value):
        if self.raw and not isinstance(value, str):
            # 如果表单验证错误,会直接打下提交的内容,我们也直接输出
            value = base64.b64encode(value or b"").decode()
        return super().prepare_value(value)

    def clean(self, value):
        if not self._has_changed(self.initial, value):
            if self.raw:
                return base64.b64decode(value.encode())
            else:
                return value
        return crypto.encrypt(value, self.raw)

    def _has_changed(self, initial, value):
        return value != self.prepare_value(initial)


class BaseApplicationAdmin(admin.ModelAdmin):
    allowed_app_types = tuple()

    actions = None
    list_display = ("__str__",  "type", "appid", "desc", "created_at")
    search_fields = ("title", "name", "appid")

    fields = ("title", "name", "appid", "appsecret", "access_token_url",
              "desc", "pays")

    form = ModelForm

    def notify_url(self, obj):
        return obj and obj.notify_url(self.request)
    notify_url.short_description = _("Message notify URL")

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj=obj)
        if not obj:
            return tuple(field for field in fields if field not in
                         ("notify_url",))
        return fields

    def get_readonly_fields(self, request, obj=None):
        if obj:
            fields = ("name", "appid", "mchid", "notify_url")
            if obj.type != AppType.UNKNOWN:
                fields = fields + ("type",)
            return fields
        return tuple()

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field=from_field)
        if obj and obj.type not in self.allowed_app_types:
            return None
        return obj

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        if change:
            for name, field in form.base_fields.items():
                if name in ENCRYPTED_FIELDS:
                    field.initial = getattr(obj, name)
        return form

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "type":
            kwargs["choices"] = tuple((name, verbose)
                                      for name, verbose in db_field.choices
                                      if name in self.allowed_app_types)
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # 替换formclass为EncryptedField
        if db_field.name in ENCRYPTED_FIELDS:
            kwargs["form_class"] = EncryptedField
            kwargs["widget"] = forms.PasswordInput(render_value=True)
            kwargs["raw"] = db_field.name in BINARY_FIELDS

        elif db_field.name == "pays":
            kwargs["widget"] = FilteredSelectMultiple(_("WeChat Pays"), False)

        elif db_field.name == "access_token_url":
            kwargs["form_class"] = forms.URLField

        formfield = super().formfield_for_dbfield(db_field=db_field,
                                                  request=request, **kwargs)

        if db_field.name == "pays":
            formfield.widget.can_add_related = False

        return formfield

    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request).filter(
            type__in=self.query_app_types)

    @property
    def query_app_types(self):
        return self.allowed_app_types


class HostApplicationAdmin(BaseApplicationAdmin):
    hosted_application = None

    @mark_safe
    def manage(self, obj):
        link = reverse("admin:{0}_{1}_changelist".format(
            self.hosted_application._meta.app_label,
            self.hosted_application._meta.model_name))
        template = '<a href="{0}?parent_id={1}">{2}</a>'
        return template.format(link, obj.pk, _("Manage"))


class HostedApplicationAdmin(BaseApplicationAdmin):
    parent_type = None

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj=obj)
        if obj:
            return tuple(field for field in fields if field != "parent")
        return fields

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        if not change:
            parent = self._get_parent(request)
            if parent.type != self.parent_type:
                raise Http404
            form.base_fields["parent"].initial = parent.id
            form.base_fields["parent"].disabled = True
            form.base_fields["name"].initial = parent.name + "."
        return form

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field=db_field,
                                                  request=request, **kwargs)

        if db_field.name == "parent":
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_delete_related = False

        return formfield

    def has_module_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return False

    def _get_parent(self, request):
        changelist_filters = request.GET.get("_changelist_filters")
        if not changelist_filters:
            raise Http404
        query = dict(parse_qsl(changelist_filters))
        return Application.objects.get(pk=query["parent_id"])
