# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings

ADMINSITE = getattr(
    settings, "WECHAT_ADMINSITE", "django.contrib.admin.site")
SESSIONSTORAGE = getattr(
    settings, "WECHAT_SESSIONSTORAGE", "django.core.cache.cache")
WECHATCLIENTFACTORY = getattr(
    settings, "WECHAT_WECHATCLIENTFACTORY",
    "wechat_django.utils.wechat.get_wechat_client")
MESSAGETIMEOFFSET = getattr(settings, "WECHAT_MESSAGETIMEOFFSET", 180)
MESSAGENOREPEATNONCE = getattr(settings, "WECHAT_MESSAGENOREPEATNONCE", True)
