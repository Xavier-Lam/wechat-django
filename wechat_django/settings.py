# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings

SITE_HOST = getattr(settings, "WECHAT_SITE_HOST", None)
SITE_HTTPS = getattr(settings, "WECHAT_SITE_HTTPS", True)

PATCHADMINSITE = getattr(settings, "WECHAT_PATCHADMINSITE", True)

SESSIONSTORAGE = getattr(
    settings, "WECHAT_SESSIONSTORAGE", "django.core.cache.cache")

MESSAGETIMEOFFSET = getattr(settings, "WECHAT_MESSAGETIMEOFFSET", 180)

MESSAGENOREPEATNONCE = getattr(settings, "WECHAT_MESSAGENOREPEATNONCE", True)
