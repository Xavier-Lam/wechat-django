# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from wechat_django.admin.base import has_wechat_permission
from wechat_django.admin.wechatapp import WeChatAppAdmin
from wechat_django.models import WeChatApp
from ..models import WeChatPay


class WeChatPayForm(forms.ModelForm):
    clear_certs = forms.BooleanField(
        label=_("clear certs"), initial=False, required=False,
        help_text=_("Your mch_cert already uploaded"))
    _mch_cert = forms.FileField(
        label=_("mch_cert"), required=False, help_text=_("商户证书"))
    _mch_key = forms.FileField(
        label=_("mch_key"), required=False, help_text=_("商户证书私钥"))

    class Meta(object):
        model = WeChatPay
        fields = (
            "title", "name", "weight", "mch_id", "api_key", "sub_mch_id",
            "mch_app_id", "_mch_cert", "_mch_key", "clear_certs")
        widgets = dict(
            api_key=forms.PasswordInput(render_value=True),
        )

    def __init__(self, *args, **kwargs):
        super(WeChatPayForm, self).__init__(*args, **kwargs)

        # 处理字段
        inst = self.instance
        if inst.pk:
            self._readonly_field("name")
            self._readonly_field("mch_id")
            if not inst.mch_app_id:
                self._remove_field("sub_mch_id")
                self._remove_field("mch_app_id")
        if inst.pk and inst.mch_cert and inst.mch_key:
            self._remove_field("_mch_cert")
            self._remove_field("_mch_key")
        else:
            self._remove_field("clear_certs")

    def _remove_field(self, field):
        self.fields[field].widget = forms.widgets.HiddenInput()
        self.fields[field].disabled = True

    def _readonly_field(self, field):
        self.fields[field].disabled = True

    def clean__mch_cert(self):
        file = self.cleaned_data.get("_mch_cert")
        if file:
            return file.read()
        return None

    def clean__mch_key(self):
        file = self.cleaned_data.get("_mch_key")
        if file:
            return file.read()
        return None

    def clean(self):
        rv = super(WeChatPayForm, self).clean()
        mch_cert = rv.get("_mch_cert")
        mch_key = rv.get("_mch_key")
        if (mch_cert or mch_key) and not (mch_cert and mch_key):
            self.add_error(
                "_mch_cert", _("must upload both mch_cert and mch_key"))
        return rv

    def _post_clean(self):
        super(WeChatPayForm, self)._post_clean()
        # 处理证书
        if self.cleaned_data.get("clear_certs"):
            self.instance.mch_cert = None
            self.instance.mch_key = None
        if self.cleaned_data.get("_mch_cert"):
            self.instance.mch_cert = self.cleaned_data.pop("_mch_cert")
        if self.cleaned_data.get("_mch_key"):
            self.instance.mch_key = self.cleaned_data.pop("_mch_key")


class WeChatPayInline(admin.StackedInline):
    form = WeChatPayForm
    model = WeChatPay

    def get_extra(self, request, obj=None):
        return 0 if obj.pay else 1


admin.site.unregister(WeChatApp)


@admin.register(WeChatApp)
class WeChatAppWithPayAdmin(WeChatAppAdmin):
    inlines = (WeChatPayInline,)

    def get_inline_instances(self, request, obj=None):
        rv = super(WeChatAppWithPayAdmin, self).get_inline_instances(
            request, obj)
        if not obj or obj.type not in (
            WeChatApp.Type.SERVICEAPP, WeChatApp.Type.MINIPROGRAM,
            WeChatApp.Type.OTHER):
            return []
        # 支付权限
        if not has_wechat_permission(request, obj, "pay", "manage"):
            return []
        return rv

    def get_deleted_objects(self, objs, request):
        from ..models import UnifiedOrder
        deleted_objects, model_count, perms_needed, protected =\
            super(WeChatAppWithPayAdmin, self).get_deleted_objects(objs, request)
        ignored_models = (UnifiedOrder._meta.verbose_name,)
        perms_needed = perms_needed.difference(ignored_models)
        return deleted_objects, model_count, perms_needed, protected
