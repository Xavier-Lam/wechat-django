import json

from wechatpy import messages

from ..models import MessageHandler, Reply, Rule
from .bases import WeChatTestCase
from .interceptors import wechatapi, wechat_api_accesstoken, wechatapi_error

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
        pass

    def test_forward(self):
        """测试转发回复"""
        pass
        
    def test_reply(self):
        """测试一般回复"""
        # 测试文本回复
        pass
        # 测试图片回复
        pass
        # 测试音频回复
        pass
        # 测试视频回复
        pass
        # 测试音乐回复
        pass
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
        rule = dict(type=Rule.Type.ALL)
        handler_all = self._create_handler(rule, replies=replies, 
            strategy=MessageHandler.ReplyStrategy.ALL)
        handler_rand = self._create_handler(rule, replies=replies,
            strategy=MessageHandler.ReplyStrategy.RANDOM)

        # 随机回复
        api = "/cgi-bin/message/custom/send"
        sender = "openid"
        message = messages.TextMessage(dict(
            FromUserName=sender,
            content="xyz"
        ))
        with wechat_api_accesstoken(), wechatapi_error(api):
            reply = handler_rand.reply(message)
            self.assertTrue(reply1 in reply or reply2 in reply)
        
        # 回复一条正常消息以及一条客服消息
        counter = dict(calls=0)
        def callback(request, response):
            counter["calls"] += 1
            data = json.loads(request.body.decode())
            self.assertEqual(data["text"]["content"], reply2)
            self.assertEqual(data["touser"], sender)
        with wechat_api_accesstoken(), wechatapi(api, dict(errcode=0, errmsg=""), callback):
            reply = handler_all.reply(message)
            self.assertTrue(reply1 in reply and reply2 not in reply)
            self.assertEqual(counter["calls"], 1)
    
    def _create_handler(self, rules, name="", replies=None, **kwargs):
        """:rtype: MessageHandler"""
        handler = MessageHandler.objects.create(
            app=self.app,
            name=name,
            **kwargs
        )
        
        if isinstance(rules, dict):
            rules = [rules]
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