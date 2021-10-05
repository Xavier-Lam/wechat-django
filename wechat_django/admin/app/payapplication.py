from django import forms
from django.utils.translation import ugettext_lazy as _

from wechat_django.enums import AppType
from wechat_django.models import apps
from wechat_django.utils.crypto import crypto
from wechat_django.utils.form import ModelForm
from .base import (BaseApplicationAdmin, HostApplicationAdmin,
                   HostedApplicationAdmin, ParentApplicationFilter)


class WeChatPayForm(ModelForm):
    clear_cert = forms.BooleanField(label=_("Clear certs"), initial=False,
                                    required=False,
                                    help_text=_("Remove your cert pair "
                                                "already uploaded"))
    _mch_cert = forms.FileField(label=_("mch_cert"), required=False)
    _mch_key = forms.FileField(label=_("mch_key"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 处理字段
        inst = self.instance
        if inst.pk and inst.mch_cert and inst.mch_key:
            self.fields["_mch_cert"].widget = forms.widgets.HiddenInput()
            self.fields["_mch_cert"].disabled = True
            self.fields["_mch_key"].widget = forms.widgets.HiddenInput()
            self.fields["_mch_key"].disabled = True
        else:
            self.fields["clear_cert"].widget = forms.widgets.HiddenInput()
            self.fields["clear_cert"].disabled = True

    def clean__mch_cert(self):
        return self._clean_file("_mch_cert")

    def clean__mch_key(self):
        return self._clean_file("_mch_key")

    def _clean_file(self, field_name):
        file = self.cleaned_data.get(field_name)
        if file:
            return crypto.encrypt(file.read())
        return None

    def clean(self):
        cleaned_data = super().clean()
        mch_cert = cleaned_data.get("_mch_cert")
        mch_key = cleaned_data.get("_mch_key")
        if (mch_cert or mch_key) and not (mch_cert and mch_key):
            self.add_error("_mch_cert",
                           _("You have to upload both mch_cert and mch_key"))
        return cleaned_data

    def _post_clean(self):
        super()._post_clean()
        # 处理证书
        if self.cleaned_data.get("clear_cert"):
            self.instance.mch_cert = None
            self.instance.mch_key = None
        if self.cleaned_data.get("_mch_cert"):
            self.instance.mch_cert = self.cleaned_data.pop("_mch_cert")
        if self.cleaned_data.get("_mch_key"):
            self.instance.mch_key = self.cleaned_data.pop("_mch_key")


class PayApplicationAdmin(BaseApplicationAdmin):
    allowed_app_types = (AppType.PAY,)

    list_display = ("__str__", "mchid", "desc", "created_at")

    fields = ("title", "name", "mchid", "api_key", "_mch_cert", "_mch_key",
              "clear_cert", "desc")
    form = WeChatPayForm


class PayMerchantAdmin(HostApplicationAdmin):
    allowed_app_types = (AppType.MERCHANTPAY,)
    hosted_application = apps.HostedPayApplication

    list_display = ("__str__", "appid", "mchid", "desc", "created_at",
                    "manage")

    fields = ("title", "name", "appid", "mchid", "api_key", "_mch_cert",
              "_mch_key", "clear_cert", "desc")
    form = WeChatPayForm


class HostedPayAdmin(HostedApplicationAdmin):
    allowed_app_types = (AppType.HOSTED | AppType.PAY,)
    parent_type = AppType.MERCHANTPAY

    list_display = ("__str__", "mchid", "desc", "created_at")
    list_filter = (ParentApplicationFilter,)

    fields = ("parent", "title", "name", "mchid", "desc")
