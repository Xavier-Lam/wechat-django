# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from wechat_django.patches import WeChatClient


def in_wechat(request):
    """判断是否时微信环境"""
    ua = request.META["HTTP_USER_AGENT"]
    return bool(re.search(r"micromessenger", ua, re.IGNORECASE))


def get_wechat_client(wechat_app):
    """:type wechat_app: wechat_django.models.WeChatApp"""
    return WeChatClient
