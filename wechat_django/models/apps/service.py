# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechat_django.constants import AppType
from .base import ApiClientApp, InteractableApp, OAuthApp, WeChatApp


@WeChatApp.register_apptype_cls(AppType.SERVICEAPP)
class ServiceApp(ApiClientApp, InteractableApp, OAuthApp, WeChatApp):
    """服务号"""

    OAUTH_URL = "https://open.weixin.qq.com/connect/oauth2/authorize"

    class Meta(object):
        proxy = True
