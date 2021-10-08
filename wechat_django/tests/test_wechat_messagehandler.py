from unittest import mock
from wechatpy import messages, replies, WeChatComponent

from wechat_django.models.apps.base import Application
from wechat_django.wechat.messagehandler import (
    builtin_handlers, MessageHandler, MessageHandlerCollection,
    MessageMatcher, MessageResponder, reply2send)
from .base import TestOnlyException, WeChatDjangoTestCase


class WeChatMessageHandlerTestCase(WeChatDjangoTestCase):
    def test_reply2send(self):
        """测试被动回复转主动"""
        # 空消息转换
        empty_msg = replies.EmptyReply()
        empty_str = ""
        self.assertIsNone(reply2send(empty_msg)[0])
        self.assertIsNone(reply2send(empty_str)[0])

        client = self.officialaccount.base_client.message

        # 文本消息转换
        target = "target"
        content = "test"
        reply = replies.TextReply(target=target, content=content)
        funcname, kwargs = reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_text")
        self.assertEqual(kwargs["user_id"], target)
        self.assertEqual(kwargs["content"], content)

        # 图片消息转换
        media_id = "media_id"
        reply = replies.ImageReply(target=target, media_id=media_id)
        funcname, kwargs = reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_image")
        self.assertEqual(kwargs["user_id"], target)
        self.assertEqual(kwargs["media_id"], media_id)

        # 声音消息转换
        reply = replies.VoiceReply(target=target, media_id=media_id)
        funcname, kwargs = reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_voice")
        self.assertEqual(kwargs["user_id"], target)
        self.assertEqual(kwargs["media_id"], media_id)

        # 视频消息转换
        title = "title"
        description = "desc"
        reply = replies.VideoReply(target=target, media_id=media_id,
                                   title=title, description=description)
        funcname, kwargs = reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_video")
        self.assertEqual(kwargs["user_id"], target)
        self.assertEqual(kwargs["media_id"], media_id)
        self.assertEqual(kwargs["title"], title)
        self.assertEqual(kwargs["description"], description)
        # 选填字段
        reply = replies.VideoReply(target=target, media_id=media_id)
        funcname, kwargs = reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_video")
        self.assertEqual(kwargs["user_id"], target)
        self.assertEqual(kwargs["media_id"], media_id)
        self.assertIsNone(kwargs["title"])
        self.assertIsNone(kwargs["description"])

        # 音乐消息转换
        music_url = "music_url"
        hq_music_url = "hq_music_url"
        reply = replies.MusicReply(target=target, thumb_media_id=media_id,
                                   title=title, description=description,
                                   music_url=music_url,
                                   hq_music_url=hq_music_url)
        funcname, kwargs = reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_music")
        self.assertEqual(kwargs["user_id"], target)
        self.assertEqual(kwargs["thumb_media_id"], media_id)
        self.assertEqual(kwargs["url"], music_url)
        self.assertEqual(kwargs["hq_url"], hq_music_url)
        self.assertEqual(kwargs["title"], title)
        self.assertEqual(kwargs["description"], description)
        # 选填字段
        reply = replies.MusicReply(target=target, thumb_media_id=media_id)
        funcname, kwargs = reply2send(reply)
        self.assertTrue(hasattr(client, funcname))
        self.assertEqual(funcname, "send_music")
        self.assertEqual(kwargs["user_id"], target)
        self.assertEqual(kwargs["thumb_media_id"], media_id)
        self.assertIsNone(kwargs["url"])
        self.assertIsNone(kwargs["hq_url"])
        self.assertIsNone(kwargs["title"])
        self.assertIsNone(kwargs["description"])

        # 图文消息转换
        pass

    def test_matcher(self):
        """测试MessageMatcher"""
        content = "content"
        message = messages.TextMessage({"Content": content})
        image_message = messages.ImageMessage({})
        matched_request = self.make_request("POST", path="/",
                                            wechat_app=self.officialaccount)
        unmatched_request = self.make_request("POST", path="/",
                                              wechat_app=self.miniprogram)
        matched_query = {"content": content}
        unmatched_query = {"content": "123"}

        def image_matcher(message, request, *args, **kwargs):
            return message.type == image_message.type

        # 测试app_name
        matcher = MessageMatcher(app_names=self.officialaccount.name)
        self.assertTrue(matcher.match(message, matched_request))
        self.assertFalse(matcher.match(message, unmatched_request))
        matcher = MessageMatcher(app_names=[self.officialaccount.name])
        self.assertTrue(matcher.match(message, matched_request))
        self.assertFalse(matcher.match(message, unmatched_request))
        matcher = MessageMatcher(app_names=[self.officialaccount.name,
                                            self.miniprogram.name])
        self.assertTrue(matcher.match(message, matched_request))
        self.assertTrue(matcher.match(message, unmatched_request))

        # 测试query
        matcher = MessageMatcher(query=matched_query)
        self.assertTrue(matcher.match(message, matched_request))
        self.assertTrue(matcher.match(message, unmatched_request))
        matcher = MessageMatcher(query=unmatched_query)
        self.assertFalse(matcher.match(message, matched_request))
        self.assertFalse(matcher.match(message, unmatched_request))

        # 测试matcher
        matcher = MessageMatcher(matcher=image_matcher)
        self.assertTrue(matcher.match(image_message, matched_request))
        self.assertFalse(matcher.match(message, matched_request))

        # 测试appname + query
        matcher = MessageMatcher(app_names=self.officialaccount.name,
                                 query=matched_query)
        self.assertTrue(matcher.match(message, matched_request))
        self.assertFalse(matcher.match(message, unmatched_request))
        matcher = MessageMatcher(app_names=self.officialaccount.name,
                                 query=unmatched_query)
        self.assertFalse(matcher.match(message, matched_request))
        self.assertFalse(matcher.match(message, unmatched_request))
        matcher = MessageMatcher(app_names=self.officialaccount.name,
                                 matcher=image_matcher)
        self.assertFalse(matcher.match(message, matched_request))
        self.assertTrue(matcher.match(image_message, matched_request))
        matcher = MessageMatcher(app_names=self.officialaccount.name,
                                 query=matched_query,
                                 matcher=image_matcher)
        self.assertFalse(matcher.match(message, matched_request))
        self.assertFalse(matcher.match(image_message, matched_request))

        # 测试dummy matcher
        matcher = MessageMatcher()
        self.assertFalse(matcher.match(message, matched_request))

        # 测试match_all
        matcher = MessageMatcher(match_all=True)
        self.assertTrue(matcher.match(message, matched_request))
        self.assertTrue(matcher.match(message, unmatched_request))

    def test_responder(self):
        """测试Responder"""
        message = messages.TextMessage({})
        good_handler = self.create_handler(str(message))
        bad_handler = self.create_handler(exc=TestOnlyException)

        responder = MessageResponder(handler=good_handler)
        self.assertEqual(responder(message, None).content, str(message))
        responder = MessageResponder(handler=bad_handler)
        self.assertRaises(TestOnlyException, lambda: responder(message, None))
        responder = MessageResponder(handler=bad_handler,
                                     ignore_exceptions=True)
        self.assertIsInstance(responder(message, None), replies.EmptyReply)

    def test_handler(self):
        """测试MessageHandler"""
        content = "content"
        message = messages.TextMessage({"Content": content})

        dummy_matcher = MessageMatcher()
        all_matcher = MessageMatcher(match_all=True)

        result1 = "1"
        result2 = "2"
        empty_responder = self.create_handler()
        responder1 = self.create_handler(result1)
        responder2 = self.create_handler(result2)
        bad_handler = self.create_handler(exc=TestOnlyException)

        def return_content(message, request, *args, **kwargs):
            return message.content

        # 测试直接注册函数
        handler = MessageHandler(all_matcher, return_content)
        self.assertEqual(
            tuple(map(lambda o: o.content, handler(message, None))),
            (content,))
        handler = MessageHandler(all_matcher, (return_content,))
        self.assertEqual(
            tuple(map(lambda o: o.content, handler(message, None))),
            (content,))

        # 单一matcher,responder
        handler = MessageHandler(dummy_matcher, responder1)
        self.assertFalse(handler.match(message, None))
        self.assertFalse(handler(message, None))
        handler = MessageHandler(all_matcher, responder1)
        self.assertTrue(handler.match(message, None))
        self.assertEqual(
            tuple(map(lambda o: o.content, handler(message, None))),
            (result1,))

        # 多matcher,单一responder
        handler = MessageHandler([dummy_matcher, dummy_matcher], responder1)
        self.assertFalse(handler.match(message, None))
        self.assertFalse(handler(message, None))
        handler = MessageHandler([dummy_matcher, all_matcher], responder1)
        self.assertTrue(handler.match(message, None))
        self.assertEqual(
            tuple(map(lambda o: o.content, handler(message, None))),
            (result1,))

        # 单matcher,多responder
        handler = MessageHandler(dummy_matcher, [responder1, responder2])
        self.assertFalse(handler(message, None))
        handler = MessageHandler(all_matcher, [responder1, empty_responder,
                                               responder2])
        self.assertEqual(
            tuple(map(lambda o: o.content, handler(message, None))),
            (result1, result2))

        # responder异常
        handler = MessageHandler(all_matcher, bad_handler)
        self.assertRaises(TestOnlyException, lambda: handler(message, None))

        # 允许异常
        handler = MessageHandler(all_matcher, bad_handler,
                                 ignore_exceptions=True)
        self.assertFalse(handler(message, None))
        handler = MessageHandler(all_matcher, [bad_handler, responder1],
                                 ignore_exceptions=True)
        self.assertEqual(
            tuple(map(lambda o: o.content, handler(message, None))),
            (result1,))

    def test_collection(self):
        """测试MessageHandlerCollection"""
        collection1 = MessageHandlerCollection()
        collection2 = MessageHandlerCollection()
        collection3 = MessageHandlerCollection()

        kwargs = {"match_all": True, "pass_through": True}
        collection2.register(**kwargs, weight=3)(self.create_handler(1))
        collection3.register(**kwargs, weight=2)(self.create_handler(2))
        collection1.register(**kwargs, weight=1)(self.create_handler(3))
        collection3.register(**kwargs)(self.create_handler(4))
        collection2.register(**kwargs)(self.create_handler(5))
        collection1.register(**kwargs)(self.create_handler(6))
        collection1.register(**kwargs, weight=-1)(self.create_handler(7))
        collection3.register(**kwargs, weight=-2)(self.create_handler(8))
        collection2.register(**kwargs, weight=-3)(self.create_handler(9))
        collection = MessageHandlerCollection(
            collection3, collection2, collection1)
        message = messages.TextMessage({})
        self.assertEqual(
            list(map(lambda o: o(message, None)[0].content, collection)),
            list(map(lambda o: str(o + 1), range(9))))

    def test_register(self):
        """测试message_handler注册"""
        message = messages.TextMessage({})
        image_message = messages.ImageMessage({})

        # 测试注册权重
        kwargs = {"match_all": True, "pass_through": True}
        message_handler = MessageHandlerCollection()
        message_handler.register(**kwargs)(self.create_handler(2))
        message_handler.register(**kwargs)(self.create_handler(3))
        message_handler.register(weight=1, **kwargs)(self.create_handler(1))
        message_handler.register(weight=-1, **kwargs)(self.create_handler(4))
        replies = message_handler.handle(message, None)
        self.assertEqual(tuple(map(lambda o: int(o.content), replies)),
                         (1, 2, 3, 4))

        # 测试非passthrough
        message_handler = MessageHandlerCollection()
        message_handler.register(match_all=True)(self.create_handler(1))
        message_handler.register(match_all=True)(self.create_handler(2))
        replies = message_handler.handle(message, None)
        self.assertEqual(tuple(map(lambda o: int(o.content), replies)), (1,))

        # 测试空响应
        message_handler = MessageHandlerCollection()
        message_handler.register(match_all=True, pass_through=True)(
            self.create_handler())
        message_handler.register(match_all=True, pass_through=True)(
            self.create_handler())
        replies = message_handler.handle(message, None)
        self.assertFalse(replies)

        # 测试条件匹配
        message_handler = MessageHandlerCollection()
        message_handler.register(query={"type": "text"}, pass_through=True)(
            self.create_handler("text"))
        message_handler.register(query={"type": "image"}, pass_through=True)(
            self.create_handler("image"))
        replies = message_handler.handle(message, None)
        self.assertEqual(tuple(map(lambda o: o.content, replies)), ("text",))
        replies = message_handler.handle(image_message, None)
        self.assertEqual(tuple(map(lambda o: o.content, replies)), ("image",))

        # 测试异常
        message_handler = MessageHandlerCollection()
        message_handler.register(match_all=True)(
            self.create_handler(exc=TestOnlyException))
        self.assertRaises(TestOnlyException,
                          lambda: message_handler.handle(message, None))
        message_handler = MessageHandlerCollection()
        message_handler.register(match_all=True, pass_through=True)(
            self.create_handler(1))
        message_handler.register(
            match_all=True, pass_through=True, ignore_exceptions=True)(
                self.create_handler(exc=TestOnlyException))
        message_handler.register(match_all=True, pass_through=True)(
            self.create_handler(2))
        replies = message_handler.handle(message, None)
        self.assertEqual(tuple(map(lambda o: int(o.content), replies)),
                         (1, 2))

    def test_builtin_thirdpartyplatform_handlers(self):
        """测试内建第三方平台相关处理器"""
        # 测试ticket推送
        request = self.make_request("POST", path="/",
                                    wechat_app=self.thirdpartyplatform)
        xml = """<xml>
            <AppId>some_appid</AppId>
            <CreateTime>1413192605</CreateTime>
            <InfoType>component_verify_ticket</InfoType>
            <ComponentVerifyTicket>t</ComponentVerifyTicket>
        </xml>"""
        message = self.thirdpartyplatform.parse_message(xml)
        result = builtin_handlers.handle(message, request)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].render(), "success")
        thirdpartyplatform = Application.objects.get(
            name=self.thirdpartyplatform.name)
        self.assertEqual(thirdpartyplatform.verify_ticket, "t")

        # 测试授权新增
        xml = """<xml>
            <AppId>appid</AppId>
            <CreateTime>1413192760</CreateTime>
            <InfoType>authorized</InfoType>
            <AuthorizerAppid>hosted_officialaccount_appid</AuthorizerAppid>
            <AuthorizationCode>code1</AuthorizationCode>
            <AuthorizationCodeExpiredTime>0</AuthorizationCodeExpiredTime>
            <PreAuthCode>pre_code</PreAuthCode>
        </xml>"""
        message = self.thirdpartyplatform.parse_message(xml)
        auth_result = {
            "authorization_info": {
                "authorizer_appid": "hosted_miniprogram_appid",
                "authorizer_access_token": "access_token1",
                "authorizer_refresh_token": "refresh_token1"
            }
        }
        with mock.patch.object(WeChatComponent, "_query_auth",
                               return_value=auth_result):
            result = builtin_handlers.handle(message, request)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].render(), "success")
            WeChatComponent._query_auth.assert_called_once_with("code1")
        app = Application.objects.get(name=self.hosted_miniprogram.name)
        self.assertEqual(app.access_token, "access_token1")
        self.assertEqual(app.refresh_token, "refresh_token1")

        # 测试授权变更
        xml = """<xml>
            <AppId>appid</AppId>
            <CreateTime>1413192760</CreateTime>
            <InfoType>updateauthorized</InfoType>
            <AuthorizerAppid>hosted_officialaccount_appid</AuthorizerAppid>
            <AuthorizationCode>code2</AuthorizationCode>
            <AuthorizationCodeExpiredTime>0</AuthorizationCodeExpiredTime>
            <PreAuthCode>pre_code</PreAuthCode>
        </xml>"""
        message = self.thirdpartyplatform.parse_message(xml)
        auth_result = {
            "authorization_info": {
                "authorizer_appid": "hosted_miniprogram_appid",
                "authorizer_access_token": "access_token2",
                "authorizer_refresh_token": "refresh_token2"
            }
        }
        with mock.patch.object(WeChatComponent, "_query_auth",
                               return_value=auth_result):
            result = builtin_handlers.handle(message, request)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].render(), "success")
            WeChatComponent._query_auth.assert_called_once_with("code2")
        app = Application.objects.get(name=self.hosted_miniprogram.name)
        self.assertEqual(app.access_token, "access_token2")
        self.assertEqual(app.refresh_token, "refresh_token2")

        # 测试授权取消
        xml = """<xml>
            <AppId>appid</AppId>
            <CreateTime>1413192760</CreateTime>
            <InfoType>unauthorized</InfoType>
            <AuthorizerAppid>hosted_miniprogram_appid</AuthorizerAppid>
        </xml>"""
        message = self.thirdpartyplatform.parse_message(xml)
        result = builtin_handlers.handle(message, request)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].render(), "success")
        app = Application.objects.get(name=self.hosted_miniprogram.name)
        self.assertIsNone(app._access_token)
        self.assertIsNone(app.refresh_token)

        del thirdpartyplatform.verify_ticket

    def create_handler(self, result=None, exc=None):
        if exc:
            def func(message, request, *args, **kwargs):
                raise exc
            return func
        return lambda message, request, *args, **kwargs: result
