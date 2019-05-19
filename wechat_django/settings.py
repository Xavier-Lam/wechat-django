# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings

SITE_HOST = getattr(settings, "WECHAT_SITE_HOST", None)
SITE_HTTPS = getattr(settings, "WECHAT_SITE_HTTPS", True)

PATCHADMINSITE = getattr(settings, "WECHAT_PATCHADMINSITE", True)
"""是否将django默认的adminsite替换为wechat_django默认的adminsite, 默认替换"""

SESSIONSTORAGE = getattr(
    settings, "WECHAT_SESSIONSTORAGE", "django.core.cache.cache")

WECHATCLIENTFACTORY = getattr(
    settings, "WECHAT_WECHATCLIENTFACTORY",
    "wechat_django.client.get_client")

OAUTHCLIENTFACTORY = getattr(
    settings, "WECHAT_OAUTHCLIENTFACTORY",
    "wechat_django.oauth.get_client")

MESSAGETIMEOFFSET = getattr(settings, "WECHAT_MESSAGETIMEOFFSET", 180)

MESSAGENOREPEATNONCE = getattr(settings, "WECHAT_MESSAGENOREPEATNONCE", True)
