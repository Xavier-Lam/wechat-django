import re

from django import forms
from django.contrib import admin
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.translation import ugettext as _

from .. import views
from ..models import WeChatApp, WECHATPERM_PREFIX
from .bases import has_wechat_permission

class WeChatAppAdmin(admin.ModelAdmin):
    actions = None
    list_display = ("title", "name", "appid", "short_desc", "interactable", 
        "created", "updated")
    search_fields = ("title", "name", "appid", "short_desc")

    fields = ("title", "name", "appid", "appsecret", "token", "encoding_aes_key",
        "encoding_mode", "desc", "callback", "created", "updated")

    def short_desc(self ,obj):
        return truncatechars(obj.desc, 35)
    short_desc.short_description = _("description")

    def callback(self, obj):
        return obj and self.request.build_absolute_uri(reverse(
            views.handler, kwargs=dict(appname=obj.name)))

    def get_fields(self, request, obj=None):
        fields = list(super(WeChatAppAdmin, self).get_fields(request, obj))
        if not obj:
            fields.remove("callback")
            fields.remove("created")
            fields.remove("updated")
        return fields

    def get_readonly_fields(self, request, obj=None):
        rv = super(WeChatAppAdmin, self).get_readonly_fields(request, obj)
        if obj:
            rv = rv + ("name", "appid", "created", "updated", "callback")
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
        all_perms = request.user.get_all_permissions()
        pattern = r"{label}.{prefix}(?P<appname>.+)(?:|manage)?$".format(
            label="wechat_django",
            prefix=WECHATPERM_PREFIX
        ).replace("|", "[|]")
        rv = set()
        for perm in all_perms:
            m = re.match(pattern, perm)
            m and rv.add(m.group("appname"))
        return rv

    def get_model_perms(self, request):
        return ({} if request.resolver_match.kwargs.get("app_id") 
            else super(WeChatAppAdmin, self).get_model_perms(request))
    
    class WeChatAppForm(forms.ModelForm):
        class Meta(object):
            model = WeChatApp
            fields = "__all__"
            widgets = dict(
                appsecret=forms.PasswordInput(render_value=True),
                encoding_aes_key=forms.PasswordInput(render_value=True)
            )

    form = WeChatAppForm

admin.site.register(WeChatApp, WeChatAppAdmin)