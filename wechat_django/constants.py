# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class AppType(object):
    OTHER = 0
    SERVICEAPP = 1
    SUBSCRIBEAPP = 2
    MINIPROGRAM = 4


class WeChatSNSScope(object):
    BASE = "snsapi_base"
    USERINFO = "snsapi_userinfo"
