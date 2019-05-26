# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django import forms
from django.contrib import admin
from django.template.defaultfilters import truncatechars
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _

from ..models import MsgLogFlag, WeChatApp
from ..models.permission import get_user_permissions
from .base import has_wechat_permission


class WeChatAppForm(forms.ModelForm):
    log_message = forms.BooleanField(
        label=_("log messages"), initial=False, required=False)

    wechat_host = forms.CharField(
        label=_("WeChat host"), required=False,
        help_text=_("接收微信回调的域名"))
    wechat_https = forms.ChoiceField(
        label=_("WeChat https"), required=False,
        choices=[(True, _("Yes")), (False, _("No"))],
        help_text=_("回调地址是否为https"))

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
            initial["wechat_host"] = inst.site_host
            initial["wechat_https"] = inst.site_https
            initial["accesstoken_url"] = inst.configurations.get(
                "ACCESSTOKEN_URL", "")
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
        self.instance.configurations["SITE_HOST"] =\
            self.cleaned_data.get("wechat_host", "")
        self.instance.configurations["SITE_HTTPS"] =\
            self.cleaned_data.get("wechat_https", None)
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
        "title", "name", "type", "appid", "short_desc", "abilities",
        "created_at", "updated_at")
    search_fields = ("title", "name", "appid", "short_desc")

    fields = (
        "title", "name", "appid", "appsecret", "type", "abilities", "token",
        "encoding_aes_key", "encoding_mode", "desc", "log_message",
        "callback", "wechat_host", "wechat_https", "accesstoken_url",
        "oauth_url", "created_at", "updated_at"
    )
    readonly_fields = ("abilities",)

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

    def delete_view(self, request, object_id, *args, **kwargs):
        request.app = WeChatApp.objects.get(id=object_id)
        return super(WeChatAppAdmin, self).delete_view(
            request, object_id, *args, **kwargs)

    def get_urls(self):
        urlpatterns = super(WeChatAppAdmin, self).get_urls()
        # django 1.11 替换urlpattern为命名式的
        if django.VERSION[0] < 2:
            for pattern in urlpatterns:
                pattern._regex = pattern._regex.replace(
                    "(.+)", "(?P<object_id>.+)")
        return urlpatterns

    def get_fields(self, request, obj=None):
        fields = list(super(WeChatAppAdmin, self).get_fields(request, obj))
        if not obj:
            fields.remove("callback")
            fields.remove("created_at")
            fields.remove("updated_at")
        if obj and obj.type == WeChatApp.Type.SUBSCRIBEAPP:
            fields.remove("oauth_url")
        if obj and not obj.abilities.interactable:
            fields.remove("callback")
        return fields

    def get_readonly_fields(self, request, obj=None):
        rv = super(WeChatAppAdmin, self).get_readonly_fields(request, obj)
        if obj:
            rv = rv + (
                "name", "appid", "callback", "created_at", "updated_at")
            if obj.type != 0:
                rv = rv + ("type",)
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

    def get_deleted_objects(self, objs, request):
        from ..models import WeChatUser
        from ..pay.models import UnifiedOrder
        deleted_objects, model_count, perms_needed, protected =\
            super(WeChatAppAdmin, self).get_deleted_objects(objs, request)
        ignored_models = (
            WeChatUser._meta.verbose_name, UnifiedOrder._meta.verbose_name)
        perms_needed = perms_needed.difference(ignored_models)
        return deleted_objects, model_count, perms_needed, protected

    form = WeChatAppForm
