# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from wechatpy.exceptions import WeChatException


class BadMessageRequest(ValueError):
    pass


class MessageHandleError(ValueError):
    pass


class WeChatAbilityError(WeChatException):
    """当公众号尝试使用不具备的某一能力时抛出的异常"""

    API = (10000, _("没有API访问能力"))
    TEMPLATE = (10001, _("没有模板消息能力"))
    OAUTH = (10002, _("没有OAUTH能力"))
    INTERACTABLE = (10003, _("没有消息交互能力"))

    def __init__(self, err):
        super(WeChatAbilityError, self).__init__(*err)
