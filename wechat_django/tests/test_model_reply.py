# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import time

from django.test import RequestFactory
from django.utils.http import urlencode
from httmock import response
from requests.exceptions import HTTPError
from six.moves.urllib.parse import parse_qsl
from wechatpy import messages, parse_message, replies
from wechatpy.utils import check_signature, WeChatSigner

from ..exceptions import MessageHandleError
from ..models import MessageHandler, Reply, WeChatMessageInfo
from ..sites.wechat import patch_request
from .base import WeChatTestCase
from .interceptors import (common_interceptor, wechatapi,
    wechatapi_accesstoken, wechatapi_error)


class ReplyTestCase(WeChatTestCase):
    def test_reply(self):
        """测试一般回复"""
        sender = "openid"
        message = messages.TextMessage(dict(
            FromUserName=sender,
            content="xyz"
        ))

        def _test_reply(type, **kwargs):
            reply = Reply(
                type=type,
                **{
                    k: v
                    for k, v in kwargs.items()
                    if v is not None
                }
            )
            reply_message = reply.normal_reply(message)
            self.assertEqual(reply_message.target, sender)
            self.assertEqual(reply_message.type, type)
            return reply_message

        # 测试文本回复
        content = "test"
        reply = _test_reply(Reply.MsgType.TEXT, content=content)
        self.assertEqual(reply.content, content)

        # 测试图片回复
        media_id = "media_id"
        reply = _test_reply(Reply.MsgType.IMAGE, media_id=media_id)
        self.assertEqual(reply.image, media_id)

        # 测试音频回复
        reply = _test_reply(Reply.MsgType.VOICE, media_id=media_id)
        self.assertEqual(reply.voice, media_id)

        # 测试视频回复
        title = "title"
        description = "desc"
        reply = _test_reply(
            Reply.MsgType.VIDEO, media_id=media_id, title=title,
            description=description)
        self.assertEqual(reply.media_id, media_id)
        self.assertEqual(reply.title, title)
        self.assertEqual(reply.description, description)
        # 选填字段
        reply = _test_reply(Reply.MsgType.VIDEO, media_id=media_id)
        self.assertEqual(reply.media_id, media_id)
        self.assertIsNone(reply.title)
        self.assertIsNone(reply.description)

        # 测试音乐回复
        music_url = "music_url"
        hq_music_url = "hq_music_url"
        reply = _test_reply(
            Reply.MsgType.MUSIC, thumb_media_id=media_id, title=title,
            description=description, music_url=music_url,
            hq_music_url=hq_music_url)
        self.assertEqual(reply.thumb_media_id, media_id)
        self.assertEqual(reply.title, title)
        self.assertEqual(reply.description, description)
        self.assertEqual(reply.music_url, music_url)
        self.assertEqual(reply.hq_music_url, hq_music_url)
        # 选填字段
        reply = _test_reply(Reply.MsgType.MUSIC, thumb_media_id=media_id)
        self.assertEqual(reply.thumb_media_id, media_id)
        self.assertIsNone(reply.title)
        self.assertIsNone(reply.description)
        self.assertIsNone(reply.music_url)
        self.assertIsNone(reply.hq_music_url)

        # 测试图文回复
        pass

    def test_multireply(self):
        """测试多回复"""
        reply1 = "abc"
        reply2 = "def"
        replies = [dict(
            type=Reply.MsgType.TEXT,
            content=reply1
        ), dict(
            type=Reply.MsgType.TEXT,
            content=reply2
        )]
        handler_all = self._create_handler(
            replies=replies, strategy=MessageHandler.ReplyStrategy.REPLYALL)
        handler_rand = self._create_handler(
            replies=replies, strategy=MessageHandler.ReplyStrategy.RANDOM)

        # 随机回复
        api = "/cgi-bin/message/custom/send"
        sender = "openid"
        message = messages.TextMessage(dict(
            FromUserName=sender,
            content="xyz"
        ))
        message = self._wrap_message(message)
        with wechatapi_accesstoken(), wechatapi_error(api):
            reply = handler_rand.reply(message)
            self.assertEqual(reply.type, Reply.MsgType.TEXT)
            self.assertEqual(reply.target, sender)
            self.assertIn(reply.content, (reply1, reply2))

        # 回复一条正常消息以及一条客服消息
        counter = dict(calls=0)

        def callback(url, request, response):
            counter["calls"] += 1
            data = json.loads(request.body.decode())
            self.assertEqual(data["text"]["content"], reply1)
            self.assertEqual(data["touser"], sender)
        with wechatapi_accesstoken(), wechatapi(api, dict(errcode=0, errmsg=""), callback):
            reply = handler_all.reply(message)
            self.assertEqual(reply.type, Reply.MsgType.TEXT)
            self.assertEqual(reply.target, sender)
            self.assertEqual(reply.content, reply2)
            self.assertEqual(counter["calls"], 1)

    def test_custom(self):
        """测试自定义回复"""
        from ..models import WeChatApp

        def _get_handler(handler, app=None):
            return self._create_handler(replies=dict(
                type=Reply.MsgType.CUSTOM,
                program="wechat_django.tests.test_model_handler." + handler
            ), app=app)

        sender = "openid"
        message = messages.TextMessage(dict(
            FromUserName=sender,
            content="xyz"
        ))
        message = self._wrap_message(message)
        success_reply = "success"
        # 测试自定义回复
        handler = _get_handler("debug_handler")
        reply = handler.reply(message)
        self.assertIsInstance(reply, replies.TextReply)
        self.assertEqual(reply.content, success_reply)

        # 测试未加装饰器的自定义回复
        handler = _get_handler("forbidden_handler")
        self.assertRaises(MessageHandleError, lambda: handler.reply(message))

        # 测试不属于本app的自定义回复
        handler_success = _get_handler("app_only_handler")
        handler_fail = _get_handler("app_only_handler",
            WeChatApp.objects.get_by_name("test1"))
        reply = handler_success.reply(message)
        self.assertIsInstance(reply, replies.TextReply)
        self.assertEqual(reply.content, success_reply)
        message._app = WeChatApp.objects.get_by_name("test1")
        self.assertRaises(MessageHandleError, lambda: handler_fail.reply(message))

    def test_forward(self):
        """测试转发回复"""
        scheme = "http"
        netloc = "example.com"
        path = "/debug"
        url = "{scheme}://{netloc}{path}".format(
            scheme=scheme,
            netloc=netloc,
            path=path
        )

        token = self.app.token
        timestamp = str(int(time.time()))
        nonce = "123456"
        query_data = dict(
            timestamp=timestamp,
            nonce=nonce
        )
        signer = WeChatSigner()
        signer.add_data(token, timestamp, nonce)
        signature = signer.signature
        query_data["signature"] = signature

        sender = "openid"
        content = "xyz"
        xml = """<xml>
        <ToUserName><![CDATA[toUser]]></ToUserName>
        <FromUserName><![CDATA[{sender}]]></FromUserName>
        <CreateTime>1348831860</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{content}]]></Content>
        <MsgId>1234567890123456</MsgId>
        </xml>""".format(sender=sender, content=content)
        req_url = url + "?" + urlencode(query_data)
        request = RequestFactory().post(req_url, xml, content_type="text/xml")

        patch_request(request, self.app.name, WeChatMessageInfo)
        message = request.wechat

        reply_text = "abc"

        def reply_test(url, request):
            self.assertEqual(url.scheme, scheme)
            self.assertEqual(url.netloc, netloc)
            self.assertEqual(url.path, path)

            query = dict(parse_qsl(url.query))
            self.assertEqual(query["timestamp"], timestamp)
            self.assertEqual(query["nonce"], nonce)
            self.assertEqual(query["signature"], signature)
            check_signature(self.app.token, query["signature"], timestamp, nonce)

            msg = parse_message(request.body)
            self.assertIsInstance(msg, messages.TextMessage)
            self.assertEqual(msg.source, sender)
            self.assertEqual(msg.content, content)
            reply = replies.create_reply(reply_text, msg)
            return response(content=reply.render())

        handler = self._create_handler(replies=dict(
            type=Reply.MsgType.FORWARD,
            url=url
        ))

        with common_interceptor(reply_test):
            reply = handler.reply(message)
            self.assertIsInstance(reply, replies.TextReply)
            self.assertEqual(reply.content, reply_text)
            self.assertEqual(reply.target, sender)

        def bad_reply(url, request):
            return response(404)

        with common_interceptor(bad_reply):
            self.assertRaises(HTTPError, lambda: handler.reply(message))

    def test_send(self):
        """测试客服回复"""
        sender = "openid"
        message = messages.TextMessage(dict(
            FromUserName=sender,
            content="xyz"
        ))
        message = self._wrap_message(message)

        # 空消息转换
        empty_msg = replies.EmptyReply()
        empty_str = ""
        self.assertIsNone(Reply.reply2send(empty_msg)[0])
        self.assertIsNone(Reply.reply2send(empty_str)[0])

        client = self.app.client.message

        # 文本消息转换
        content = "test"
        msg_type = Reply.MsgType.TEXT
        reply = Reply(type=msg_type, content=content).reply(message)
        funcname, kwargs = Reply.reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_text")
        self.assertEqual(reply.content, kwargs["content"])

        # 图片消息转换
        media_id = "media_id"
        msg_type = Reply.MsgType.IMAGE
        reply = Reply(type=msg_type, media_id=media_id).reply(message)
        funcname, kwargs = Reply.reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_image")
        self.assertEqual(reply.media_id, kwargs["media_id"])

        # 声音消息转换
        msg_type = Reply.MsgType.VOICE
        reply = Reply(type=msg_type, media_id=media_id).reply(message)
        funcname, kwargs = Reply.reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_voice")
        self.assertEqual(reply.media_id, kwargs["media_id"])

        # 视频消息转换
        title = "title"
        description = "desc"
        msg_type = Reply.MsgType.VIDEO
        reply = Reply(type=msg_type, media_id=media_id, title=title,
            description=description).reply(message)
        funcname, kwargs = Reply.reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_video")
        self.assertEqual(reply.media_id, kwargs["media_id"])
        self.assertEqual(reply.title, kwargs["title"])
        self.assertEqual(reply.description, kwargs["description"])
        # 选填字段
        reply = Reply(type=msg_type, media_id=media_id).reply(message)
        funcname, kwargs = Reply.reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_video")
        self.assertEqual(reply.media_id, kwargs["media_id"])
        self.assertIsNone(kwargs["title"])
        self.assertIsNone(kwargs["description"])

        # 音乐消息转换
        music_url = "music_url"
        hq_music_url = "hq_music_url"
        msg_type = Reply.MsgType.MUSIC
        reply = Reply(type=msg_type, thumb_media_id=media_id, title=title,
            description=description, music_url=music_url,
            hq_music_url=hq_music_url).reply(message)
        funcname, kwargs = Reply.reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_music")
        self.assertEqual(reply.thumb_media_id, kwargs["thumb_media_id"])
        self.assertEqual(reply.music_url, kwargs["url"])
        self.assertEqual(reply.hq_music_url, kwargs["hq_url"])
        self.assertEqual(reply.title, kwargs["title"])
        self.assertEqual(reply.description, kwargs["description"])
        # 选填字段
        reply = Reply(type=msg_type, thumb_media_id=media_id).reply(message)
        funcname, kwargs = Reply.reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_music")
        self.assertEqual(reply.thumb_media_id, kwargs["thumb_media_id"])
        self.assertIsNone(kwargs["url"])
        self.assertIsNone(kwargs["hq_url"])
        self.assertIsNone(kwargs["title"])
        self.assertIsNone(kwargs["description"])

        # 图文消息转换
        pass

        # 确认消息发送
        handler = self._create_handler(replies=dict(
            type=Reply.MsgType.TEXT,
            content=content
        ))

        def callback(url, request, response):
            data = json.loads(request.body.decode())
            self.assertEqual(data["touser"], sender)
            self.assertEqual(data["msgtype"], Reply.MsgType.TEXT)
            self.assertEqual(data["text"]["content"], content)

        with wechatapi_accesstoken(), wechatapi("/cgi-bin/message/custom/send", dict(
            errcode=0
        ), callback):
            handler.replies.all()[0].send(message)

    def _wrap_message(self, message):
        return WeChatMessageInfo(
            _app=self.app,
            _message=message
        )
