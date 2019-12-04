# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechat_django.constants import AppType
from .base import ApiClientApp, InteractableApp, WeChatApp


@WeChatApp.register_apptype_cls(AppType.SUBSCRIBEAPP)
class SubscribeApp(ApiClientApp, InteractableApp, WeChatApp):
    """订阅号"""

    class Meta(object):
        proxy = True
