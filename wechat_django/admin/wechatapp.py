# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django import forms
from django.contrib import admin
from django.template.defaultfilters import truncatechars
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _

from ..models import WeChatApp
from ..models.app.base import AppAdminProperty, InteractableApp
from ..models.permission import get_user_permissions
from ..utils.model import model_fields
from .base import has_wechat_permission


class WeChatAppFormMeta(object):
    fields = "__all__"
    widgets = dict(
        appsecret=forms.PasswordInput(render_value=True),
        token=forms.PasswordInput(render_value=True),
        encoding_aes_key=forms.PasswordInput(render_value=True)
    )


class WeChatAppForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        if instance:
            # 读取表单上的属性
            props = self._get_props(instance)
            initial = kwargs.get("initial", {})
            initial.update(**props)
            kwargs["initial"] = initial

        return super(WeChatAppForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        props = self._get_props(self.instance)
        # 设置表单上的属性
        for prop in props:
            if prop in self.changed_data:
                setattr(self.instance, prop, self.cleaned_data[prop])
        return super(WeChatAppForm, self).save(commit)

    def _get_props(self, instance):
        """获取展示在表单上的属性"""
        cls = type(instance)
        return {
            field: getattr(instance, field)
            for field in self._meta.fields
            if isinstance(getattr(cls, field, None), AppAdminProperty)
        }


@admin.register(WeChatApp)
class WeChatAppAdmin(admin.ModelAdmin):
    change_form_template = "admin/change_form.html"
    change_list_template = "admin/change_list.html"
    delete_confirmation_template = "admin/delete_confirmation.html"
    object_history_template = "admin/object_history.html"

    actions = None
    list_display = ("title", "name", "type", "appid", "short_desc",
                    "abilities", "created_at", "updated_at")
    search_fields = ("title", "name", "appid", "short_desc")

    fields = ("title", "name", "appid", "appsecret", "type", "abilities",
              "desc", "created_at", "updated_at", "token", "encoding_aes_key",
              "encoding_mode", "site_host", "site_https", "callback",
              "log_message", "accesstoken_url", "oauth_url")
    form = WeChatAppForm
    readonly_fields = ("name", "appid", "abilities", "callback", "created_at",
                       "updated_at")

    @mark_safe
    def abilities(self, obj):
        abilities = []
        if obj.abilities.authed:
            abilities.append(_("authed"))
        if obj.abilities.api:
            abilities.append(_("api"))
        if obj.abilities.interactable:
            abilities.append(_("interactable"))
        if obj.abilities.pay:
            abilities.append(_("WeChat pay"))

        styles = {
            "background-color": "#70be2b",
            "color": "white",
            "border-radius": "5px",
            "margin": "0 2px",
            "padding": "2px 4px"
        }
        style_str = ";".join(["{0}: {1}".format(*o) for o in styles.items()])
        tpl = '<span style="{0}">{1}</span>'
        return "".join(map(lambda o: tpl.format(style_str, o), abilities))
    abilities.short_description = _("abilities")

    def short_desc(self, obj):
        return truncatechars(obj.desc, 35)
    short_desc.short_description = _("description")

    def callback(self, obj):
        return obj and obj.build_url(
            "handler", request=self.request, absolute=True)
    callback.short_description = _("message callback url")

    def add_view(self, request, *args, **kwargs):
        extra_context = kwargs.pop("extra_context", None) or {}
        extra_context["show_save"] = False
        extra_context["save_as"] = True
        kwargs["extra_context"] = extra_context
        return super(WeChatAppAdmin, self).add_view(request, *args, **kwargs)

    def delete_view(self, request, object_id, *args, **kwargs):
        request.app = WeChatApp.objects.get(id=object_id)
        return super(WeChatAppAdmin, self).delete_view(request, object_id,
                                                       *args, **kwargs)

    def get_urls(self):
        urlpatterns = super(WeChatAppAdmin, self).get_urls()
        # django 1.11 替换urlpattern为命名式的
        if django.VERSION[0] < 2:
            for pattern in urlpatterns:
                pattern._regex = pattern._regex.replace(
                    "(.+)", "(?P<object_id>.+)")
        return urlpatterns

    def get_fields(self, request, obj=None):
        if not obj:
            return ("title", "name", "appid", "appsecret", "type", "desc")

        fields = list(super(WeChatAppAdmin, self).get_fields(request, obj))

        if not isinstance(obj, InteractableApp):
            # 移除消息交互app才需要的字段
            fields.remove("token")
            fields.remove("encoding_aes_key")
            fields.remove("encoding_mode")
            fields.remove("site_host")
            fields.remove("site_https")
            fields.remove("callback")

        allows = self._list_admin_properties(request, obj)
        allows += model_fields(type(obj))
        allows += ["callback", "abilities"]

        return tuple(field for field in fields if field in allows)

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return tuple()

        fields = self.get_fields(request, obj)
        # TODO: readonly会抛出Unable to lookup异常,只能先不做处理
        readonlys = [
        # attr
        # for attr, prop in self._list_admin_properties(request, obj, True)
        # if (not prop.fset  # 没有fset的
        #     # 或已设的
        #     or getattr(prop, "readonly", False) and getattr(obj, attr))
        ]
        obj.type and readonlys.append("type")
        return set(self.readonly_fields).intersection(fields).union(readonlys)

    def _list_admin_properties(self, request, obj, items=False):
        """列举admin额外需要显示的属性"""
        cls = type(obj)
        return [
            (attr, getattr(cls, attr)) if items else attr
            for attr in dir(cls)
            if isinstance(getattr(cls, attr), AppAdminProperty)
        ]

    def get_form(self, request, obj=None, **kwargs):
        """生成app表单"""
        parent = super(WeChatAppAdmin, self)
        if not obj:
            return parent.get_form(request, obj, **kwargs)

        meta = type(str("Meta"), (WeChatAppFormMeta,), {"model": type(obj)})

        # 设置属性
        attrs = dict(Meta=meta)
        for attr, prop in self._list_admin_properties(request, obj, True):
            field_kwargs = dict(
                label=_(attr),
                help_text=_(prop.help_text)
            )
            if getattr(prop, "widget", None):
                field_kwargs["widget"] = prop.widget
            field_kwargs["required"] = getattr(prop, "required", False)

            attrs[attr] = prop.field_type(**field_kwargs)

        origin_form = self.form
        try:
            self.form = type(str("WeChatAppForm"), (origin_form, ), attrs)
            return parent.get_form(request, obj, **kwargs)
        finally:
            self.form = origin_form

    def get_queryset(self, request):
        self.request = request
        rv = super(WeChatAppAdmin, self).get_queryset(request)

        # 非管理员 过滤拥有的微信号权限
        if not super(WeChatAppAdmin, self).has_change_permission(request):
            allowed_apps = self._get_allowed_apps(request)
            rv = rv.filter(name__in=allowed_apps)

        return rv

    def has_change_permission(self, request, obj=None):
        rv = super(WeChatAppAdmin, self).has_change_permission(request, obj)
        if not rv:
            if obj:
                return has_wechat_permission(request, obj, "manage")
            else:
                return bool(self._get_allowed_apps(request))
        return rv

    def _get_allowed_apps(self, request):
        """有权限的微信号"""
        perms = get_user_permissions(request.user)
        return set(
            appname for appname, permissions in perms.items()
            if "manage" in permissions
        )

    def get_model_perms(self, request):
        return ({} if getattr(request, "app_id", None)
                else super(WeChatAppAdmin, self).get_model_perms(request))

    def get_deleted_objects(self, objs, request):
        from ..models import WeChatUser
        from ..pay.models import UnifiedOrder
        deleted_objects, model_count, perms_needed, protected =\
            super(WeChatAppAdmin, self).get_deleted_objects(objs, request)
        # 忽略对用户及统一订单的操作权限,可移除app
        ignored_models = (WeChatUser._meta.verbose_name,
                          UnifiedOrder._meta.verbose_name)
        perms_needed = perms_needed.difference(ignored_models)
        return deleted_objects, model_count, perms_needed, protected
