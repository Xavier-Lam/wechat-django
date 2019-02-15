# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta
import time

from django.utils import timezone
from wechatpy import events, messages, replies

from ..decorators import message_handler
from ..models import MessageHandler, Reply, Rule, WeChatMessageInfo
from .bases import WeChatTestCase
from .interceptors import (common_interceptor, wechatapi,
    wechatapi_accesstoken, wechatapi_error)


@message_handler
def debug_handler(message):
    return "success"


@message_handler("test")
def app_only_handler(message):
    return "success"


def forbidden_handler(message):
    return ""


class HandlerTestCase(WeChatTestCase):
    def test_available(self):
        """测试handler有效性"""
        rule = dict(type=Rule.Type.ALL)
        now = timezone.now()
        day = timedelta(days=1)
        handler_not_begin = self._create_handler(rule, starts=now + day)
        handler_ended = self._create_handler(rule, ends=now - day)
        handler_disabled = self._create_handler(rule, enabled=False)
        handler_available = self._create_handler(
            rule, starts=now - day, ends=now + day)

        msg_info = self._msg2info(messages.TextMessage("abc"))
        self.assertFalse(handler_not_begin.is_match(msg_info))
        self.assertFalse(handler_ended.is_match(msg_info))
        self.assertFalse(handler_disabled.is_match(msg_info))
        self.assertTrue(handler_available.is_match(msg_info))

        matches = MessageHandler.matches(msg_info)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], handler_available)

    def test_sync(self):
        """测试同步"""
        pass
    
