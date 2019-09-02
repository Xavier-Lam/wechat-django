# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta
import time

from django.urls import reverse
from django.utils import timezone
from wechatpy import events, messages

from ..handler import Handler, message_handler
from ..models import (MessageHandler, Reply, Rule, WeChatMessageInfo,
                      WeChatUser)
from ..sites.wechat import patch_request
from .base import WeChatTestCase
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

    def test_subscribe_events(self):
        """测试关注,取关事件"""
        # url = reverse("wechat_django:handler",
        #               kwargs=dict(appname=self.app.name))
        url = "/"
        openid = "test_subscribe_events"
        user = WeChatUser.objects.upsert_by_dict(dict(openid=openid), self.app)
        self.assertIsNone(user.subscribe)

        handler = Handler()

        subscribe_event_text = """
        <xml>
        <ToUserName><![CDATA[ToUser]]></ToUserName>
        <FromUserName><![CDATA[{0}]]></FromUserName>
        <CreateTime>123456789</CreateTime>
        <MsgType><![CDATA[event]]></MsgType>
        <Event><![CDATA[subscribe]]></Event>
        </xml>
        """.format(openid)
        request = self.rf().post(
            url, subscribe_event_text, content_type="text/xml")
        request = patch_request(request, self.app.name)
        self.assertEqual(handler.post(request), "")
        user.refresh_from_db()
        self.assertTrue(user.subscribe)

        unsubscribe_event_text = """
        <xml>
        <ToUserName><![CDATA[ToUser]]></ToUserName>
        <FromUserName><![CDATA[{0}]]></FromUserName>
        <CreateTime>123456789</CreateTime>
        <MsgType><![CDATA[event]]></MsgType>
        <Event><![CDATA[unsubscribe]]></Event>
        </xml>
        """.format(openid)
        request = self.rf().post(
            url, unsubscribe_event_text, content_type="text/xml")
        request = patch_request(request, self.app.name)
        self.assertEqual(handler.post(request), "")
        user.refresh_from_db()
        self.assertEqual(user.subscribe, False)

        subscribe_event_text = """
        <xml>
        <ToUserName><![CDATA[ToUser]]></ToUserName>
        <FromUserName><![CDATA[{0}]]></FromUserName>
        <CreateTime>123456789</CreateTime>
        <MsgType><![CDATA[event]]></MsgType>
        <Event><![CDATA[subscribe]]></Event>
        <EventKey><![CDATA[qrscene_123123]]></EventKey>
        <Ticket><![CDATA[TICKET]]></Ticket>
        </xml>
        """.format(openid)
        request = self.rf().post(
            url, subscribe_event_text, content_type="text/xml")
        request = patch_request(request, self.app.name)
        self.assertEqual(handler.post(request), "")
        user.refresh_from_db()
        self.assertTrue(user.subscribe)
