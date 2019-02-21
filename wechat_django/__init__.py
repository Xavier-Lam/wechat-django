# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__title__ = "wechat-django"
__description__ = "Django WeChat Extension"
__url__ = "https://github.com/Xavier-Lam/wechat-django"
__version__ = "0.1.0"
__author__ = "Xavier-Lam"
__author_email__ = "Lam.Xavier@hotmail.com"

__all__ = ("urls", )

default_app_config = 'wechat_django.apps.WeChatConfig'

url_patterns = []
urls = (url_patterns, "wechat_django", "wechat_django")

from . import _patch # NOQA
