import sys

from django.conf import settings


ENABLE_MERCHANT = True
ENABLE_THIRDPARTYPLATFORM = True
ENABLE_WECHATPAY = True

SECRET_KEY = settings.SECRET_KEY

OAUTH_LOGIN_HANDLER = "wechat_django.oauth.oauth_login"


def get(key, default=None):
    if hasattr(settings, "WECHAT_DJANGO_" + key):
        return getattr(settings, "WECHAT_DJANGO_" + key)
    return default if default else getattr(sys.modules[__name__], key)
