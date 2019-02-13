__version__ = "0.1.0"
__author__ = "Xavier-Lam"

__all__ = ("urls", )

default_app_config = 'wechat_django.apps.WeChatConfig'

url_patterns = []
urls = (url_patterns, "wechat_django", "wechat_django")

from . import _patch
