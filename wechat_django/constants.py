# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class AppType(object):
    OTHER = 0
    SERVICEAPP = 0x01
    SUBSCRIBEAPP = 0x02
    MINIPROGRAM = 0x04
    PAYPARTNER = 0x100  # 微信支付服务商


class WeChatSNSScope(object):
    BASE = "snsapi_base"
    USERINFO = "snsapi_userinfo"
