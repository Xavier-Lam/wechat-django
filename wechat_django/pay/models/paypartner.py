# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from wechat_django.constants import AppType
from wechat_django.models.apps.base import (ApiClientApp,
                                            ConfigurationProperty,
                                            InteractableApp, WeChatApp)


@WeChatApp.register_apptype_cls(AppType.PAYPARTNER)
class PayPartnerApp(ApiClientApp, InteractableApp, WeChatApp):
    """微信支付服务商"""

    mch_id = ConfigurationProperty("MCH_ID", required=True, readonly=True,
                                   doc=_("微信支付分配的商户号"))
    api_key = ConfigurationProperty("API_KEY", doc=_("商户号KEY"))

    # mch_cert mch_key

    class Meta(object):
        proxy = True
