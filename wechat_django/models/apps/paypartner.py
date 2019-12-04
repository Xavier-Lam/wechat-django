# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechat_django.constants import AppType
from .base import ApiClientApp, InteractableApp, WeChatApp


@WeChatApp.register_apptype_cls(AppType.PAYPARTNER)
class PayPartnerApp(ApiClientApp, InteractableApp, WeChatApp):
    """微信支付服务商"""

    class Meta(object):
        proxy = True
