# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64

from django import forms
from django.utils.translation import ugettext_lazy as _

from wechat_django.constants import AppType
from wechat_django.models.app.base import (AppAdminProperty,
                                           ConfigurationProperty, WeChatApp)


class PayPartnerCertProperty(AppAdminProperty):
    """证书用文件设置,base64至库中,读取时decode"""

    field_type = forms.FileField

    def __init__(self, key, doc="", **kw):
        def fget(self):
            rv = self.configurations.get(key)
            if rv:
                rv = base64.b64decode(rv)
            return rv

        def fset(self, value):
            raw = value and value.read()
            if raw:
                self.configurations[key] = base64.b64encode(raw)
            else:
                self.configurations.pop(key, None)

        kwargs = dict(
            fget=fget, fset=fset, fdel=lambda self: fset(self, None),
            doc=doc
        )
        kw["help_text"] = doc
        super(PayPartnerCertProperty, self).__init__(**kwargs)

        for k, v in kw.items():
            setattr(self, k, v)


@WeChatApp.register_apptype_cls(AppType.PAYPARTNER)
class PayPartnerApp(WeChatApp):
    """微信支付服务商"""

    mch_id = ConfigurationProperty("MCH_ID", required=True, readonly=True,
                                   doc=_("微信支付分配的商户号"))
    api_key = ConfigurationProperty(
        "API_KEY", widget=forms.PasswordInput(render_value=True),
        doc=_("商户号KEY"))

    mch_cert = PayPartnerCertProperty("MCH_CERT")
    mch_key = PayPartnerCertProperty("MCH_KEY")

    @property
    def pays(self):
        from . import WeChatSubPay

        queryset = super(PayPartnerApp, self).pays
        queryset.model = WeChatSubPay
        return queryset

    class Meta(object):
        proxy = True
