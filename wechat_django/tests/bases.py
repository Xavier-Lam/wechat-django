# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from ..models import WeChatApp


class WeChatTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(WeChatTestCase, cls).setUpTestData()
        WeChatApp.objects.create(title="test", name="test",
            appid="appid", appsecret="secret", token="token")
        WeChatApp.objects.create(title="test1", name="test1",
            appid="appid1", appsecret="secret", token="token")

    def setUp(self):
        self.app = WeChatApp.get_by_name("test")

    #region utils
    def _create_handler(self, rules=None, name="", replies=None, app=None, 
        **kwargs):
        """:rtype: MessageHandler"""
        from ..models import MessageHandler, Reply, Rule
        handler = MessageHandler.objects.create(
            app=app or self.app,
            name=name,
            **kwargs
        )

        if not rules:
            rules = [dict(type=Rule.Type.ALL)]
        if isinstance(rules, dict):
            rules = [rules]
        if isinstance(replies, dict):
            replies = [replies]
        replies = replies or []
        Rule.objects.bulk_create([
            Rule(handler=handler, **rule)
            for rule in rules
        ])
        Reply.objects.bulk_create([
            Reply(handler=handler, **reply)
            for reply in replies
        ])

        return handler

    def _msg2info(self, message, app=None, **kwargs):
        """:rtype: WeChatMessageInfo"""
        from ..models import WeChatMessageInfo
        return WeChatMessageInfo(
            _app=app or self.app,
            _message=message,
            **{
                "_" + k: v
                for k, v in kwargs.items()
            }
        )
    #endregion
