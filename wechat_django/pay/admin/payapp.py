# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from wechat_django.admin.base import has_wechat_permission
from wechat_django.admin.wechatapp import WeChatAppAdmin, WeChatAppForm
from wechat_django.constants import AppType
from wechat_django.models import WeChatApp
from wechat_django.pay.models import PayPartnerApp, WeChatPay, WeChatSubPay


class WeChatPayPartnerAppForm(WeChatAppForm):
    clear_certs = forms.BooleanField(label=_("clear certs"), initial=False,
                                     required=False,
                                     help_text=_("Your mch_cert already "
                                                 "uploaded"))

    def clean(self):
        data = super(WeChatPayPartnerAppForm, self).clean()
        mch_cert = data.get("_mch_cert")
        mch_key = data.get("_mch_key")
        if (mch_cert or mch_key) and not (mch_cert and mch_key):
            self.add_error("_mch_cert",
                           _("must upload both mch_cert and mch_key"))
        return data

    def _post_clean(self):
        super(WeChatPayPartnerAppForm, self)._post_clean()
        # 处理证书
        if self.cleaned_data.get("clear_certs"):
            del self.instance.mch_cert
            del self.instance.mch_key


admin.site.unregister(WeChatApp)


@admin.register(WeChatApp)
class WeChatAppWithPayAdmin(WeChatAppAdmin):
    """替换原有微信App后台,增加微信支付相关功能"""

    form = WeChatPayPartnerAppForm

    def get_fields(self, request, obj=None):
        fields = super(WeChatAppWithPayAdmin, self).get_fields(request, obj)
        if obj and isinstance(obj, PayPartnerApp):
            # 服务商app字段不同
            fields = tuple(field for field in fields if field != "appsecret")
            add_fields = ["mch_id", "api_key"]
            if obj.mch_cert and obj.mch_key:
                add_fields.append("clear_certs")
            else:
                add_fields += ["mch_cert", "mch_key"]
            fields = fields + tuple(add_fields)
        return fields

    def get_inline_instances(self, request, obj=None):
        origin_inlines = self.inlines
        self.inlines = self.get_inlines(request, obj)
        try:
            parent = super(WeChatAppWithPayAdmin, self)
            return parent.get_inline_instances(request, obj)
        finally:
            self.inlines = origin_inlines

    def get_inlines(self, request, obj=None):
        form = None
        inlines = list(self.inlines)
        if obj and has_wechat_permission(request, obj, "pay", "manage"):
            if obj.type & AppType.PAYPARTNER:
                form = SubPayForm
            elif obj.type & (AppType.SERVICEAPP | AppType.MINIPROGRAM):
                form = BasicPayForm

        if form:
            inline_cls = type(WeChatPayInline.__name__,
                              (WeChatPayInline,), dict(form=form))

            inlines.append(inline_cls)

        return inlines

    def get_deleted_objects(self, objs, request):
        # 防止权限不足造成无法删除app的情况
        from ..models import UnifiedOrder
        deleted_objects, model_count, perms_needed, protected =\
            super(WeChatAppWithPayAdmin, self).get_deleted_objects(objs, request)
        ignored_models = (UnifiedOrder._meta.verbose_name,)
        perms_needed = perms_needed.difference(ignored_models)
        return deleted_objects, model_count, perms_needed, protected


class WeChatPayForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(WeChatPayForm, self).__init__(*args, **kwargs)

        # 处理字段
        if self.instance and self.instance.id:
            self.fields["_mch_id"].disabled = True
            self.fields["name"].disabled = True


class BasicPayForm(WeChatPayForm):
    clear_certs = forms.BooleanField(label=_("clear certs"), initial=False,
                                     required=False,
                                     help_text=_("Your mch_cert already "
                                                 "uploaded"))
    _mch_cert = forms.FileField(label=_("mch_cert"), required=False,
                                help_text=_("商户证书"))
    _mch_key = forms.FileField(label=_("mch_key"), required=False,
                               help_text=_("商户证书私钥"))

    class Meta(object):
        model = WeChatPay
        exclude = ("sub_appid",)
        widgets = dict(api_key=forms.PasswordInput(render_value=True))

    def __init__(self, *args, **kwargs):
        super(BasicPayForm, self).__init__(*args, **kwargs)

        # 处理字段
        inst = self.instance
        if inst.pk and inst.mch_cert and inst.mch_key:
            self._remove_field("_mch_cert")
            self._remove_field("_mch_key")
        else:
            self._remove_field("clear_certs")

    def _remove_field(self, field):
        self.fields[field].widget = forms.widgets.HiddenInput()
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
        data = super(BasicPayForm, self).clean()
        mch_cert = data.get("_mch_cert")
        mch_key = data.get("_mch_key")
        if (mch_cert or mch_key) and not (mch_cert and mch_key):
            self.add_error("_mch_cert",
                           _("must upload both mch_cert and mch_key"))
        return data

    def _post_clean(self):
        super(BasicPayForm, self)._post_clean()
        # 处理证书
        if self.cleaned_data.get("clear_certs"):
            self.instance.mch_cert = None
            self.instance.mch_key = None
        if self.cleaned_data.get("_mch_cert"):
            self.instance.mch_cert = self.cleaned_data.pop("_mch_cert")
        if self.cleaned_data.get("_mch_key"):
            self.instance.mch_key = self.cleaned_data.pop("_mch_key")

    def save(self, commit=True):
        if isinstance(self.instance, WeChatSubPay) and\
           "sub_mch_id" in self.changed_data:
            self.instance.sub_mch_id = self.cleaned_data["sub_mch_id"]
        return super(BasicPayForm, self).save(commit)


class SubPayForm(WeChatPayForm):
    def __init__(self, *args, **kwargs):
        super(SubPayForm, self).__init__(*args, **kwargs)

    class Meta(object):
        model = WeChatSubPay
        fields = ("title", "name", "weight", "_mch_id")


class WeChatPayInline(admin.StackedInline):
    model = WeChatPay
    readonly_fields = ("created_at", "updated_at")

    def get_extra(self, request, obj=None):
        return 0 if obj.pay else 1
