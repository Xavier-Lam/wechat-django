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
from .utils import list_property


class WeChatAppForm(forms.ModelForm):
    log_message = forms.BooleanField(
        label=_("log messages"), initial=False, required=False)

    accesstoken_url = forms.URLField(
        label=_("accesstoken url"), required=False,
        help_text=_("获取accesstoken的url,不填直接从微信取"))
    oauth_url = forms.URLField(
        label=_("oauth url"), required=False,
        help_text=_("授权重定向的url,用于第三方网页授权换取code,默认直接微信授权"))

    class Meta(object):
        model = WeChatApp
        fields = "__all__"
        widgets = dict(
            appsecret=forms.PasswordInput(render_value=True),
            token=forms.PasswordInput(render_value=True),
            encoding_aes_key=forms.PasswordInput(render_value=True)
        )

    def __init__(self, *args, **kwargs):
        inst = kwargs.get("instance")
        if inst:
            initial = kwargs.get("initial", {})
            initial["log_message"] = inst.log_message
            initial["accesstoken_url"] = inst.configurations.get("ACCESSTOKEN_URL", "")
            initial["oauth_url"] = inst.configurations.get("OAUTH_URL", "")
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
        self.instance.configurations["ACCESSTOKEN_URL"] =\
            self.cleaned_data.get("accesstoken_url", "")
        self.instance.configurations["OAUTH_URL"] =\
            self.cleaned_data.get("oauth_url", "")
        return super(WeChatAppForm, self).save(commit)


@admin.register(WeChatApp)
class WeChatAppAdmin(admin.ModelAdmin):
    change_form_template = "admin/change_form.html"
    change_list_template = "admin/change_list.html"
    delete_confirmation_template = "admin/delete_confirmation.html"
    object_history_template = "admin/object_history.html"

    actions = None
    list_display = (
        "title", "name", "type", "appid", "short_desc", 
        list_property(
            "abilities.interactable",
            boolean=True, short_description=_("interactable")),
        "created_at", "updated_at")
    search_fields = ("title", "name", "appid", "short_desc")

    fields = (
        "title", "name", "appid", "appsecret", "type", "token",
        "encoding_aes_key", "encoding_mode", "desc", "log_message",
        "callback", "accesstoken_url", "oauth_url",
        "created_at", "updated_at"
    )

    def short_desc(self, obj):
        return truncatechars(obj.desc, 35)
    short_desc.short_description = _("description")

    def callback(self, obj):
        return obj and self.request.build_absolute_uri(reverse(
            "wechat_django:handler", kwargs=dict(appname=obj.name)))
    callback.short_description = _("message callback url")

    def get_fields(self, request, obj=None):
        fields = list(super(WeChatAppAdmin, self).get_fields(request, obj))
        if not obj:
            fields.remove("callback")
            fields.remove("created_at")
            fields.remove("updated_at")
        if obj and obj.type == WeChatApp.Type.SUBSCRIBEAPP:
            fields.remove("oauth_url")
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
        return ({} if getattr(request, "app_id", None)
            else super(WeChatAppAdmin, self).get_model_perms(request))

    form = WeChatAppForm
