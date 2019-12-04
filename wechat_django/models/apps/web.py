# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechat_django.constants import AppType
from .base import OAuthApp, WeChatApp


@WeChatApp.register_apptype_cls(AppType.WEBAPP)
class WebApp(OAuthApp, WeChatApp):
    """订阅号"""

    OAUTH_URL = "https://open.weixin.qq.com/connect/qrconnect"

    class Meta(object):
        proxy = True
