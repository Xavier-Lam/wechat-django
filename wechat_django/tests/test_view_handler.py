# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time

from django.urls import reverse
from django.utils.http import urlencode
from wechatpy.replies import deserialize_reply, TextReply
from wechatpy.utils import WeChatSigner

from .. import settings
from ..models import MessageHandler, Reply, Rule
from .bases import WeChatTestCase

# TODO: 应该拆解成测试各方法会比较直观


class HandlerTestCase(WeChatTestCase):
    def setUp(self):
        super(HandlerTestCase, self).setUp()
        handler = MessageHandler.objects.create(app=self.app)
        rule = Rule.objects.create(type=Rule.Type.EQUAL, content=dict(
            pattern=self.match_str
        ), handler=handler)
        reply = Reply.objects.create(msg_type=Reply.MsgType.TEXT, content=dict(
            content=self.success_reply
        ), handler=handler)

        settings.MESSAGENOREPEATNONCE = False

    def test_badrequest(self):
        """测试错误请求"""
        nonce = "123456"

        # 错误时间戳
        query = dict(
            timestamp=str(int(time.time() - 1000)),
            nonce=nonce
        )
        resp = self.post(query)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"")
        settings.MESSAGETIMEOFFSET = 2000
        resp = self.post(query)
        self.assertEqual(resp.status_code, 200)
        reply = deserialize_reply(resp.content)
        self.assertEqual(reply.content, self.success_reply)

        # 错误签名
        query["signature"] = "666666"
        resp = self.post(query)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"")

        # 错误格式
        del query["signature"]
        resp = self.post(query)
        self.assertEqual(resp.status_code, 200)
        reply = deserialize_reply(resp.content)
        self.assertEqual(reply.content, self.success_reply)
        resp = self.client.post(self.url + "?" + urlencode(query), dict(a=1))
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"")

        # 防重放
        settings.MESSAGENOREPEATNONCE = True
        resp = self.post(query)
        self.assertEqual(resp.status_code, 200)
        reply = deserialize_reply(resp.content)
        self.assertEqual(reply.content, self.success_reply)
        resp = self.post(query)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"")

        # 防重放超时正常接收
        pass

    def test_request(self):
        """测试正常请求"""
        timestamp = str(int(time.time()))
        nonce = "123456"
        query = dict(
            timestamp=timestamp,
            nonce=nonce
        )

        # 未匹配到
        resp = self.post(query, "666")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"")

        # 正常匹配
        resp = self.post(query)
        self.assertEqual(resp.status_code, 200)
        reply = deserialize_reply(resp.content)
        self.assertEqual(reply.target, self.sender)
        self.assertIsInstance(reply, TextReply)
        self.assertEqual(reply.content, self.success_reply)

    def test_echostr(self):
        """测试初次请求验证"""
        echostr = b"666666"
        timestamp = str(int(time.time()))
        nonce = "123456"
        query = dict(
            timestamp=timestamp,
            nonce=nonce,
            echostr=echostr
        )
        query["signature"] = self.sign(query)
        resp = self.client.get(self.url, query)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, echostr)

    def sign(self, query):
        signer = WeChatSigner()
        signer.add_data(
            self.app.token,
            query["timestamp"],
            query["nonce"]
        )
        return signer.signature

    def post(self, query, content=""):
        xml = """<xml>
        <ToUserName><![CDATA[toUser]]></ToUserName>
        <FromUserName><![CDATA[{sender}]]></FromUserName>
        <CreateTime>{timestamp}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{content}]]></Content>
        <MsgId>1234567890123456</MsgId>
        </xml>""".format(
            sender=self.sender,
            content=content or self.match_str,
            timestamp=query["timestamp"]
        )
        if "signature" not in query:
            query["signature"] = self.sign(query)
        return self.client.generic("POST", self.url + "?" + urlencode(query),
            xml)

    @property
    def sender(self):
        return "sender"

    @property
    def match_str(self):
        return "abc"

    @property
    def success_reply(self):
        return "success"

    @property
    def url(self):
        return reverse("wechat_django:handler",
            kwargs=dict(appname=self.app.name))
