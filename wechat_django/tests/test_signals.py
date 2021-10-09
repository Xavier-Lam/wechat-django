import time
from unittest.mock import patch
from urllib.parse import urlencode

from django.urls import reverse
from wechatpy.utils import WeChatSigner, random_string
from wechat_django.enums import EncryptStrategy

from wechat_django.models.apps.base import MessagePushApplicationMixin
from wechat_django import signals
from wechat_django.wechat.messagehandler import message_handlers
from .base import TestOnlyException, WeChatDjangoTestCase


def dummy_receiver(wechat_app, **kwargs):
    TestOnlyException.throw()


class SignalTestCase(WeChatDjangoTestCase):
    def test_signal(self):
        """测试信号基类"""
        # 测试使用对象发送信号能够正确接收
        dummy_signal = signals.WeChatDjangoSignal(("wechat_app", "data"))
        app = self.miniprogram
        with self.dummy_receiver():
            dummy_signal.connect(dummy_receiver, sender=app.name)
            dummy_signal.send(self.officialaccount, data="data")
            self.assertFalse(dummy_receiver.call_count)
            dummy_signal.send(app, data="data")
            self.assertEqual(dummy_receiver.call_count, 1)
            self.assertEqual(dummy_receiver.call_args[1]["wechat_app"].name,
                             app.name)
            self.assertEqual(dummy_receiver.call_args[1]["data"], "data")

        # 测试使用字符串发送信号能够正确接收
        with self.dummy_receiver():
            dummy_signal.connect(dummy_receiver, sender=app.name)
            dummy_signal.send(app.name, wechat_app=app, data="data")
            self.assertEqual(dummy_receiver.call_count, 1)
            self.assertEqual(dummy_receiver.call_args[1]["wechat_app"].name,
                             app.name)
            self.assertEqual(dummy_receiver.call_args[1]["data"], "data")

    @patch("wechat_django.signals.message_received.send_robust")
    @patch("wechat_django.signals.message_replied.send_robust")
    @patch("wechat_django.signals.message_sent.send_robust")
    def test_message_handle_success(self, *args):
        """测试messagehandler成功信号"""
        # 注册消息处理器
        message_handlers.register(match_all=True, pass_through=True)(
            lambda message, request, *args, **kwargs: message.content)
        message_handlers.register(match_all=True, pass_through=True)(
            lambda message, request, *args, **kwargs: message.source)
        message_handlers.register(match_all=True, pass_through=True)(
            lambda message, request, *args, **kwargs: message.type)

        # 注册信号
        app = self.officialaccount
        app.encrypt_strategy = EncryptStrategy.PLAIN
        app.save()

        # 普通消息直接请求
        query = self.make_query()
        raw_message = """<xml>
        <ToUserName><![CDATA[toUser]]></ToUserName>
        <FromUserName><![CDATA[sender]]></FromUserName>
        <CreateTime>1413192605</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[content]]></Content>
        <MsgId>1234567890123456</MsgId>
        </xml>"""
        path = reverse("wechat_django:handler", kwargs={"app_name": app.name})

        with patch.object(MessagePushApplicationMixin, "send_message"):
            resp = self.client.post(path, data=raw_message,
                                    content_type="text/plain",
                                    QUERY_STRING=urlencode(query))

        # 测试message_received
        self.assertEqual(signals.message_received.send_robust.call_count, 1)
        self.assert_called_app(signals.message_received, app, robust=True)
        called_kwargs = self.get_called_kwargs(signals.message_received, True)
        self.assertEqual(called_kwargs["message"].type, "text")
        self.assertEqual(called_kwargs["message"].content, "content")
        self.assertEqual(called_kwargs["request"].wechat_app.name, app.name)
        self.assertEqual(called_kwargs["request"].message.type, "text")
        self.assertEqual(called_kwargs["request"].message.content, "content")

        # 测试message_replied
        self.assertEqual(signals.message_replied.send_robust.call_count, 1)
        self.assert_called_app(signals.message_replied, app, robust=True)
        called_kwargs = self.get_called_kwargs(signals.message_replied, True)
        self.assertIs(called_kwargs["reply"], resp.replies[0])
        self.assertEqual(called_kwargs["message"].type, "text")
        self.assertEqual(called_kwargs["message"].content, "content")
        self.assertEqual(called_kwargs["response_content"], resp.content)

        # 测试message_sent
        self.assertEqual(signals.message_sent.send_robust.call_count, 2)
        self.assert_called_app(signals.message_sent, app, robust=True)
        called_kwargs = signals.message_sent.send_robust.call_args_list[0][1]
        self.assertIs(called_kwargs["reply"], resp.replies[1])
        self.assertEqual(called_kwargs["message"].type, "text")
        self.assertEqual(called_kwargs["message"].content, "content")
        called_kwargs = signals.message_sent.send_robust.call_args_list[1][1]
        self.assertIs(called_kwargs["reply"], resp.replies[2])
        self.assertEqual(called_kwargs["message"].type, "text")
        self.assertEqual(called_kwargs["message"].content, "content")

        # 清除测试数据
        app.encrypt_strategy = EncryptStrategy.ENCRYPTED
        app.save()
        message_handlers.clear()

    @patch("wechat_django.signals.message_handle_failed.send_robust")
    def test_message_handle_failed(self, *args):
        """测试messagehandler处理失败信号"""
        # 注册消息处理器
        message_handlers.register(match_all=True)(
            lambda message, *args, **kwargs:
                TestOnlyException.throw(message.content))

        # 注册信号
        app = self.officialaccount
        app.encrypt_strategy = EncryptStrategy.PLAIN
        app.save()

        # 普通消息直接请求
        query = self.make_query()
        raw_message = """<xml>
        <ToUserName><![CDATA[toUser]]></ToUserName>
        <FromUserName><![CDATA[sender]]></FromUserName>
        <CreateTime>1413192605</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[content]]></Content>
        <MsgId>1234567890123456</MsgId>
        </xml>"""
        path = reverse("wechat_django:handler", kwargs={"app_name": app.name})

        with patch.object(MessagePushApplicationMixin, "send_message"):
            self.client.post(path, data=raw_message,
                             content_type="text/plain",
                             QUERY_STRING=urlencode(query))

        # 测试message_handle_failed
        self.assertEqual(
            signals.message_handle_failed.send_robust.call_count, 1)
        self.assert_called_app(
            signals.message_handle_failed, app, robust=True)
        called_kwargs = self.get_called_kwargs(
            signals.message_handle_failed, robust=True)
        self.assertEqual(called_kwargs["message"].type, "text")
        self.assertEqual(called_kwargs["message"].content, "content")
        self.assertEqual(called_kwargs["exc"].args[0], "content")
        self.assertEqual(called_kwargs["request"].wechat_app.name, app.name)
        self.assertEqual(called_kwargs["request"].message.type, "text")
        self.assertEqual(called_kwargs["request"].message.content, "content")

        # 清除测试数据
        app.encrypt_strategy = EncryptStrategy.ENCRYPTED
        app.save()
        message_handlers.clear()

    @patch("wechat_django.signals.message_send_failed.send_robust")
    def test_message_send_failed(self, *args):
        """测试messagehandler消息发送失败信号"""
        # 注册消息处理器
        message_handlers.register(match_all=True, pass_through=True)(
            lambda message, request, *args, **kwargs: message.source)
        message_handlers.register(match_all=True, pass_through=True)(
            lambda message, request, *args, **kwargs: message.content)

        # 注册信号
        app = self.officialaccount
        app.encrypt_strategy = EncryptStrategy.PLAIN
        app.save()

        # 普通消息直接请求
        query = self.make_query()
        raw_message = """<xml>
        <ToUserName><![CDATA[toUser]]></ToUserName>
        <FromUserName><![CDATA[sender]]></FromUserName>
        <CreateTime>1413192605</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[content]]></Content>
        <MsgId>1234567890123456</MsgId>
        </xml>"""
        path = reverse("wechat_django:handler", kwargs={"app_name": app.name})

        with patch.object(MessagePushApplicationMixin, "send_message",
                          side_effect=TestOnlyException("exception")):
            resp = self.client.post(path, data=raw_message,
                                    content_type="text/plain",
                                    QUERY_STRING=urlencode(query))

        # 测试message_handle_failed
        self.assertEqual(
            signals.message_send_failed.send_robust.call_count, 1)
        self.assert_called_app(
            signals.message_send_failed, app, robust=True)
        called_kwargs = self.get_called_kwargs(
            signals.message_send_failed, robust=True)
        self.assertIs(called_kwargs["reply"], resp.replies[1])
        self.assertEqual(called_kwargs["message"].type, "text")
        self.assertEqual(called_kwargs["message"].content, "content")
        self.assertEqual(called_kwargs["exc"].args[0], "exception")
        self.assertEqual(called_kwargs["request"].wechat_app.name, app.name)
        self.assertEqual(called_kwargs["request"].message.type, "text")
        self.assertEqual(called_kwargs["request"].message.content, "content")

        # 清除测试数据
        app.encrypt_strategy = EncryptStrategy.ENCRYPTED
        app.save()
        message_handlers.clear()

    def dummy_receiver(self, **kwargs):
        return patch("{0}.{1}".format(
            dummy_receiver.__module__, dummy_receiver.__name__), **kwargs)

    def assert_called_app(self, signal, wechat_app, robust=False):
        method = "send_robust" if robust else "send"
        sender = getattr(signal, method).call_args[0][0]
        sender_name = sender if isinstance(sender, str) else sender.name
        self.assertEqual(sender_name, wechat_app.name)

    def get_called_kwargs(self, signal, robust=False):
        method = "send_robust" if robust else "send"
        return getattr(signal, method).call_args[1]

    def make_query(self):
        now = str(int(time.time()))
        nonce = random_string()
        signer = WeChatSigner()
        signer.add_data(self.TOKEN, now, nonce)
        return {
            "nonce": nonce,
            "timestamp": now,
            "signature": signer.signature,
            "echostr": "echostr"
        }
