# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings

PATCHADMINSITE = getattr(settings, "WECHAT_PATCHADMINSITE", True)
"""是否将django默认的adminsite替换为wechat_django默认的adminsite, 默认替换"""

SESSIONSTORAGE = getattr(
    settings, "WECHAT_SESSIONSTORAGE", "django.core.cache.cache")

WECHATCLIENTFACTORY = getattr(
    settings, "WECHAT_WECHATCLIENTFACTORY",
    "wechat_django.utils.wechat.get_wechat_client")

MESSAGETIMEOFFSET = getattr(settings, "WECHAT_MESSAGETIMEOFFSET", 180)

MESSAGENOREPEATNONCE = getattr(settings, "WECHAT_MESSAGENOREPEATNONCE", True)
