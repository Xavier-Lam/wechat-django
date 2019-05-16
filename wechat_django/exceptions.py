# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechatpy.exceptions import WeChatException


class BadMessageRequest(ValueError):
    pass


class MessageHandleError(ValueError):
    pass


class AbilityError(WeChatException):
    TEMPLATE = 10001 # 没有模板消息能力
