# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechatpy import events, messages

from ..models import MessageHandler, Rule
from .bases import WeChatTestCase


class HandlerTestCase(WeChatTestCase):
    def test_match(self):
        """测试匹配"""
        def _create_msg(type, **kwargs):
            rv = type(dict())
            for k, v in kwargs.items():
                setattr(rv, k, v)
            return rv

        content = "某中文"
        text_message = _create_msg(messages.TextMessage, content=content)
        another_content = "abc"
        another_text_message = _create_msg(messages.TextMessage,
            content=another_content)

        media_id = "media_id"
        url = "http://example.com/foo?bar=1"
        image_message = _create_msg(messages.ImageMessage, media_id=media_id, image=url)

        event_key = "key"
        sub_event = _create_msg(events.SubscribeEvent, key=event_key)
        click_event = _create_msg(events.ClickEvent, key=event_key)
        another_key = "another"
        another_click_event = _create_msg(events.ClickEvent, key=another_key)

        # 所有消息
        rule = Rule(type=Rule.Type.ALL)
        self.assertMatch(rule, text_message)
        self.assertMatch(rule, image_message)

        # 测试类型匹配
        rule = Rule(type=
            Rule.Type.MSGTYPE, msg_type=Rule.ReceiveMsgType.IMAGE)
        self.assertNotMatch(rule, text_message)
        self.assertMatch(rule, image_message)

        # 测试事件匹配
        rule = Rule(type=
            Rule.Type.EVENT, event=MessageHandler.EventType.SUBSCRIBE)
        self.assertNotMatch(rule, text_message)
        self.assertMatch(rule, sub_event)
        self.assertNotMatch(rule, click_event)

        # 测试指定事件匹配
        rule = Rule(type=
            Rule.Type.EVENTKEY, event=MessageHandler.EventType.CLICK,
            key=event_key)
        self.assertNotMatch(rule, text_message)
        self.assertNotMatch(rule, sub_event)
        self.assertMatch(rule, click_event)
        self.assertNotMatch(rule, another_click_event)

        # 测试包含匹配
        rule = Rule(type=Rule.Type.CONTAIN, pattern="中")
        self.assertMatch(rule, text_message)
        self.assertNotMatch(rule, another_text_message)
        self.assertNotMatch(rule, image_message)
        self.assertNotMatch(rule, click_event)

        # 测试相等匹配
        rule = Rule(type=Rule.Type.EQUAL, pattern=content)
        self.assertMatch(rule, text_message)
        self.assertNotMatch(rule, another_text_message)
        self.assertNotMatch(rule, image_message)
        self.assertNotMatch(rule, click_event)

        # 测试正则匹配
        rule = Rule(type=Rule.Type.REGEX, pattern=r"[a-c]+")
        self.assertNotMatch(rule, text_message)
        self.assertMatch(rule, another_text_message)
        self.assertNotMatch(rule, image_message)
        self.assertNotMatch(rule, click_event)

        # 测试handler匹配
        handler3 = self._create_handler(rules=[dict(
            type=Rule.Type.EQUAL,
            pattern=content
        ), dict(
            type=Rule.Type.EQUAL,
            pattern=another_content
        )], name="3")
        self.assertTrue(handler3.is_match(
            self._msg2info(text_message)))
        self.assertTrue(handler3.is_match(
            self._msg2info(another_text_message)))
        self.assertFalse(handler3.is_match(
            self._msg2info(click_event)))

        # 测试匹配顺序
        handler1 = self._create_handler(rules=[dict(
            type=Rule.Type.EVENTKEY,
            event=MessageHandler.EventType.CLICK,
            key=event_key
        )], name="1", weight=5)
        handler2 = self._create_handler(rules=[dict(
            type=Rule.Type.EQUAL,
            pattern=content
        )], name="2")
        handler4 = self._create_handler(rules=[dict(
            type=Rule.Type.EVENT,
            event=MessageHandler.EventType.CLICK
        )], name="4", weight=-5)
        matches = MessageHandler.matches(self._msg2info(text_message))
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].id, handler2.id)
        matches = MessageHandler.matches(self._msg2info(click_event))
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].id, handler1.id)
        matches = MessageHandler.matches(self._msg2info(another_click_event))
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].id, handler4.id)

    def assertMatch(self, rule, message):
        self.assertTrue(rule._match(message))

    def assertNotMatch(self, rule, message):
        self.assertFalse(rule._match(message))
