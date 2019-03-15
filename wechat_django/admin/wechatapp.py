# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from ..models import MsgLogFlag, WeChatApp
from ..models.permission import get_user_permissions
from .base import has_wechat_permission


class WeChatAppForm(forms.ModelForm):
    class Meta(object):
        model = WeChatApp
        fields = "__all__"
        widgets = dict(
            appsecret=forms.PasswordInput(render_value=True),
            encoding_aes_key=forms.PasswordInput(render_value=True)
        )

    log_message = forms.BooleanField(
        label=_("log messages"), initial=False, required=False)

    def __init__(self, *args, **kwargs):
        inst = kwargs.get("instance")
        if inst:
            initial = kwargs.get("initial", {})
            initial["log_message"] = inst.log_message
            kwargs["initial"] = initial
        return super(WeChatAppForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(WeChatAppForm, self).clean()
        if cleaned_data.get("log_message"):
            cleaned_data["flags"] = MsgLogFlag.LOG_MESSAGE
        else:
            cleaned_data["flags"] = 0
        return cleaned_data

    def save(self, commit=True):
        self.instance.flags = self.cleaned_data["flags"]
        return super(WeChatAppForm, self).save(commit)


class WeChatAppAdmin(admin.ModelAdmin):
    actions = None
    list_display = (
        "title", "name", "type", "appid", "short_desc", "interactable",
        "created_at", "updated_at"
    )
    search_fields = ("title", "name", "appid", "short_desc")

    fields = (
        "title", "name", "appid", "appsecret", "type", "token",
        "encoding_aes_key", "encoding_mode", "desc", "log_message",
        "callback", "created_at", "updated_at"
    )

    def short_desc(self, obj):
        return truncatechars(obj.desc, 35)
    short_desc.short_description = _("description")

    def callback(self, obj):
        return obj and self.request.build_absolute_uri(reverse(
            "wechat_django:handler", kwargs=dict(appname=obj.name)))
    callback.short_description = _("message callback url")

    def interactable(self, obj):
        """可与微信服务器交互的"""
        return obj.abilities.interactable
    interactable.boolean = True
    interactable.short_description = _("interactable")

    def get_fields(self, request, obj=None):
        fields = list(super(WeChatAppAdmin, self).get_fields(request, obj))
        if not obj:
            fields.remove("callback")
            fields.remove("created_at")
            fields.remove("updated_at")
        return fields

    def get_readonly_fields(self, request, obj=None):
        rv = super(WeChatAppAdmin, self).get_readonly_fields(request, obj)
        if obj:
            rv = rv + ("name", "appid", "type", "callback",
                "created_at", "updated_at")
        return rv

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
        return ({} if request.resolver_match.kwargs.get("app_id")
            else super(WeChatAppAdmin, self).get_model_perms(request))

    form = WeChatAppForm
