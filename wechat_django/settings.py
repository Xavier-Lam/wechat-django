from django.conf import settings

ADMINSITE = getattr(settings, "WECHAT_ADMINSITE", 
    "django.contrib.admin.site")
SESSIONSTORAGE = getattr(settings, "WECHAT_SESSIONSTORAGE", 
    "django.core.cache.cache")
WECHATCLIENTFACTORY = getattr(settings, "WECHAT_WECHATCLIENTFACTORY",
    "wechat_django.wechat.get_wechat_client")