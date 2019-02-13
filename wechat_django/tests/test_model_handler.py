import json
import time

from django.test import RequestFactory
from django.utils.http import urlencode
from httmock import response
from requests.exceptions import HTTPError
from six.moves.urllib.parse import parse_qsl
from wechatpy import messages, parse_message, replies
from wechatpy.utils import check_signature, WeChatSigner

from ..decorators import message_handler
from ..models import MessageHandler, Reply, Rule
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
    def test_match(self):
        """测试匹配"""
        # 测试类型匹配
        pass
        # 测试事件匹配
        pass
        # 测试指定事件匹配
        pass
        # 测试包含匹配
        pass
        # 测试相等匹配
        pass
        # 测试正则匹配
        pass
        # 测试全部匹配
        pass
        # 测试匹配顺序
        pass

    def test_available(self):
        """测试handler有效性"""
        from datetime import timedelta
        from django.utils import timezone

        rule = dict(type=Rule.Type.ALL)
        now = timezone.now()
        day = timedelta(days=1)
        handler_not_begin = self._create_handler(rule,
            name="not_begin", starts=now + day)
        handler_ended = self._create_handler(rule, name="ended", 
            ends=now - day)
        handler_disabled = self._create_handler(rule, 
            name="disabled", enabled=False)
        handler_available = self._create_handler(rule, name="available", 
            starts=now - day, ends=now + day)

        msg = messages.TextMessage("abc")
        self.assertFalse(handler_not_begin.is_match(msg))
        self.assertFalse(handler_ended.is_match(msg))
        self.assertFalse(handler_disabled.is_match(msg))
        self.assertTrue(handler_available.is_match(msg))

        matches = MessageHandler.matches(self.app, msg)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], handler_available)
    
    def test_custom(self):
        """测试自定义回复"""
        from ..models import WeChatApp

        def _get_handler(handler, app=None):
            return self._create_handler(replies=dict(
                msg_type=Reply.MsgType.CUSTOM,
                content=dict(
                    program="wechat_django.tests.test_model_handler." + handler
                )
            ), app=app)
        
        sender = "openid"
        message = messages.TextMessage(dict(
            FromUserName=sender,
            content="xyz"
        ))
        success_reply = "success"
        # 测试自定义回复
        handler = _get_handler("debug_handler")
        reply = handler.reply(message)
        self.assertIsInstance(reply, replies.TextReply)
        self.assertEqual(reply.content, success_reply)

        # 测试不属于本app的自定义回复
        handler_success = _get_handler("app_only_handler")
        handler_fail = _get_handler("app_only_handler", 
            WeChatApp.get_by_name("test1"))
        reply = handler_success.reply(message)
        self.assertIsInstance(reply, replies.TextReply)
        self.assertEqual(reply.content, success_reply)
        self.assertRaises(ValueError, lambda: handler_fail.reply(message))

        # 测试未加装饰器的自定义回复
        handler = _get_handler("forbidden_handler")
        self.assertRaises(ValueError, lambda: handler.reply(message))

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
            token=token,
            timestamp=timestamp,
            nonce=nonce
        )
        signer = WeChatSigner()
        signer.add_data(token, timestamp, nonce)
        signature = signer.signature
        query_data["signature"] = signature

        request = RequestFactory().get(url + "?" + urlencode(query_data))

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
        message = parse_message(xml)
        message.raw = xml
        message.request = request

        reply_text = "abc"
        def reply_test(url, request):
            self.assertEqual(url.scheme, scheme)
            self.assertEqual(url.netloc, netloc)
            self.assertEqual(url.path, path)

            query = dict(parse_qsl(url.query))
            self.assertEqual(query["token"], token)
            self.assertEqual(query["timestamp"], timestamp)
            self.assertEqual(query["nonce"], nonce)
            check_signature(token, query["signature"], timestamp, nonce)

            msg = parse_message(request.body)
            self.assertIsInstance(msg, messages.TextMessage)
            self.assertEqual(msg.source, sender)
            self.assertEqual(msg.content, content)
            reply = replies.create_reply(reply_text, msg)
            return response(content=reply.render())

        handler = self._create_handler(replies=dict(
            msg_type=Reply.MsgType.FORWARD,
            content=dict(url=url)
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
    
    def test_sync(self):
        """测试同步"""
        pass
        
    def test_reply(self):
        """测试一般回复"""
        def _create_reply(msg_type, **kwargs):
            return Reply(msg_type=msg_type, content=kwargs)
        sender = "openid"
        message = messages.TextMessage(dict(
            FromUserName=sender,
            content="xyz"
        ))

        # 测试文本回复
        content = "test"
        msg_type = Reply.MsgType.TEXT
        reply = _create_reply(msg_type, content=content)
        obj = reply.reply(message)
        self.assertEqual(obj.target, sender)
        self.assertEqual(obj.type, msg_type)
        self.assertEqual(obj.content, content)

        # 测试图片回复
        media_id = "media_id"
        msg_type = Reply.MsgType.IMAGE
        reply = _create_reply(msg_type, media_id=media_id)
        obj = reply.reply(message)
        self.assertEqual(obj.target, sender)
        self.assertEqual(obj.type, msg_type)
        self.assertEqual(obj.image, media_id)

        # 测试音频回复
        msg_type = Reply.MsgType.VOICE
        reply = _create_reply(msg_type, media_id=media_id)
        obj = reply.reply(message)
        self.assertEqual(obj.target, sender)
        self.assertEqual(obj.type, msg_type)
        self.assertEqual(obj.voice, media_id)

        # 测试视频回复
        title = "title"
        description = "desc"
        msg_type = Reply.MsgType.VIDEO
        reply = _create_reply(msg_type, media_id=media_id, title=title, 
            description=description)
        obj = reply.reply(message)
        self.assertEqual(obj.target, sender)
        self.assertEqual(obj.type, msg_type)
        self.assertEqual(obj.media_id, media_id)
        self.assertEqual(obj.title, title)
        self.assertEqual(obj.description, description)
        # 选填字段
        reply = _create_reply(msg_type, media_id=media_id)
        obj = reply.reply(message)
        self.assertEqual(obj.target, sender)
        self.assertEqual(obj.type, msg_type)
        self.assertEqual(obj.media_id, media_id)
        self.assertIsNone(obj.title)
        self.assertIsNone(obj.description)

        # 测试音乐回复
        music_url = "music_url"
        hq_music_url = "hq_music_url"
        msg_type = Reply.MsgType.MUSIC
        reply = _create_reply(msg_type, thumb_media_id=media_id, title=title, 
            description=description, music_url=music_url, 
            hq_music_url=hq_music_url)
        obj = reply.reply(message)
        self.assertEqual(obj.target, sender)
        self.assertEqual(obj.type, msg_type)
        self.assertEqual(obj.thumb_media_id, media_id)
        self.assertEqual(obj.title, title)
        self.assertEqual(obj.description, description)
        self.assertEqual(obj.music_url, music_url)
        self.assertEqual(obj.hq_music_url, hq_music_url)
        # 选填字段
        reply = _create_reply(msg_type, thumb_media_id=media_id)
        obj = reply.reply(message)
        self.assertEqual(obj.target, sender)
        self.assertEqual(obj.type, msg_type)
        self.assertEqual(obj.thumb_media_id, media_id)
        self.assertIsNone(obj.title)
        self.assertIsNone(obj.description)
        self.assertIsNone(obj.music_url)
        self.assertIsNone(obj.hq_music_url)

        # 测试图文回复
        pass
    
    def test_send(self):
        """测试客服回复"""
        pass
    
    def test_multireply(self):
        """测试多回复"""
        reply1 = "abc"
        reply2 = "def"
        replies = [dict(
            msg_type=Reply.MsgType.TEXT,
            content=dict(content=reply1)
        ), dict(
            msg_type=Reply.MsgType.TEXT,
            content=dict(content=reply2)
        )]
        handler_all = self._create_handler(replies=replies, 
            strategy=MessageHandler.ReplyStrategy.ALL)
        handler_rand = self._create_handler(replies=replies,
            strategy=MessageHandler.ReplyStrategy.RANDOM)

        # 随机回复
        api = "/cgi-bin/message/custom/send"
        sender = "openid"
        message = messages.TextMessage(dict(
            FromUserName=sender,
            content="xyz"
        ))
        with wechatapi_accesstoken(), wechatapi_error(api):
            reply = handler_rand.reply(message)
            self.assertEqual(reply.type, Reply.MsgType.TEXT)
            self.assertEqual(reply.target, sender)
            self.assertIn(reply.content, (reply1, reply2))
        
        # 回复一条正常消息以及一条客服消息
        counter = dict(calls=0)
        def callback(request, response):
            counter["calls"] += 1
            data = json.loads(request.body.decode())
            self.assertEqual(data["text"]["content"], reply2)
            self.assertEqual(data["touser"], sender)
        with wechatapi_accesstoken(), wechatapi(api, dict(errcode=0, errmsg=""), callback):
            reply = handler_all.reply(message)
            self.assertEqual(reply.type, Reply.MsgType.TEXT)
            self.assertEqual(reply.target, sender)
            self.assertEqual(reply.content, reply1)
            self.assertEqual(counter["calls"], 1)
    
    def _create_handler(self, rules=None, name="", replies=None, app=None, **kwargs):
        """:rtype: MessageHandler"""
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