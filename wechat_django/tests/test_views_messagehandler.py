import time
from unittest import mock
from urllib.parse import urlencode

from django.urls import reverse
from wechatpy import replies
from wechatpy.crypto.base import BasePrpCrypto
from wechatpy.utils import WeChatSigner, random_string
import xmltodict

from wechat_django.enums import EncryptStrategy
from wechat_django.exceptions import BadMessageRequest
from wechat_django.models.apps.base import (Application,
                                            MessagePushApplicationMixin)
from wechat_django.views.messagehandler import (AuthorizerHandler, Handler,
                                                MessageResponse)
from wechat_django.wechat.messagehandler import message_handlers
from .base import WeChatDjangoTestCase


class ModelWeChatMessageHandlerTestCase(WeChatDjangoTestCase):
    def test_response(self):
        """测试MessageResponse"""
        reply1 = replies.TextReply(content="1")
        reply2 = replies.TextReply(content="2")

        # 加密响应
        query = {
            "nonce": "nonce",
            "timestamp": str(int(time.time()))
        }
        request = self.make_request("POST", path="/",
                                    wechat_app=self.officialaccount,
                                    QUERY_STRING=urlencode(query))
        response = MessageResponse(request, [reply1, reply2])
        with mock.patch.object(BasePrpCrypto, "get_random_string",
                               return_value="0"*16):
            encrypted_xml = self.officialaccount.crypto.encrypt_message(
                reply1.render(), query["nonce"], query["timestamp"]).encode()
            self.assertEqual(response.content, encrypted_xml)

        # 主动发送消息
        with mock.patch.object(MessagePushApplicationMixin, "send_message"):
            response.close()
            MessagePushApplicationMixin.send_message.assert_called_once_with(
                reply2)

        # 未加密响应
        self.officialaccount.encrypt_strategy = EncryptStrategy.PLAIN
        response = MessageResponse(request, [reply1])
        self.assertEqual(response.content, reply1.render().encode())
        with mock.patch.object(MessagePushApplicationMixin, "send_message"):
            response.close()
            MessagePushApplicationMixin.send_message.assert_not_called()

    def test_initial(self):
        """测试初始化请求"""
        query = self.make_query()
        handler = Handler()
        request = self.make_request("POST", path="/",
                                    wechat_app=self.officialaccount,
                                    QUERY_STRING=urlencode(query))
        handler.initial(request)
        self.assertRaises(BadMessageRequest, lambda: handler.initial(request))
        request = self.make_request("POST", path="/",
                                    wechat_app=self.miniprogram,
                                    QUERY_STRING=urlencode(query))
        handler.initial(request)

    def test_echostr(self):
        """测试输出echostr"""
        query = self.make_query()
        request = self.make_request("GET", path="/",
                                    QUERY_STRING=urlencode(query))
        view = Handler.as_view()
        response = view(request, app_name=self.officialaccount.name)
        self.assertEqual(response.content, b"echostr")

    def test_handler(self):
        """测试消息处理"""
        message_handlers.register(match_all=True, pass_through=True)(
            lambda message, request, *args, **kwargs: message.content)
        message_handlers.register(match_all=True)(
            lambda message, request, *args, **kwargs: request.wechat_app.name)
        view = Handler.as_view()

        query = self.make_query()
        raw_message = """<xml>
        <ToUserName><![CDATA[toUser]]></ToUserName>
        <FromUserName><![CDATA[{sender}]]></FromUserName>
        <CreateTime>{timestamp}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{content}]]></Content>
        <MsgId>1234567890123456</MsgId>
        </xml>""".format(
            sender="sender",
            content="content",
            timestamp=query["timestamp"]
        )
        encrypted_message = self.officialaccount.crypto.encrypt_message(
            raw_message, query["nonce"], query["timestamp"])
        sign = xmltodict.parse(encrypted_message)["xml"]["MsgSignature"]
        query["msg_signature"] = sign
        request = self.make_request("POST", path="/",
                                    content_type="text/plain",
                                    data=encrypted_message,
                                    QUERY_STRING=urlencode(query))
        response = view(request, app_name=self.officialaccount.name)
        self.assertEqual(len(response.replies), 2)
        self.assertEqual(response.replies[0].content, "content")
        self.assertEqual(response.replies[1].content,
                         self.officialaccount.name)

        # 非加密消息
        self.officialaccount.encrypt_strategy = EncryptStrategy.PLAIN
        self.officialaccount.save()
        query = self.make_query()
        request = self.make_request("POST", path="/",
                                    content_type="text/plain",
                                    data=raw_message,
                                    QUERY_STRING=urlencode(query))
        response = view(request, app_name=self.officialaccount.name)
        self.assertEqual(len(response.replies), 2)
        self.assertEqual(response.replies[0].content, "content")
        self.assertEqual(response.replies[1].content,
                         self.officialaccount.name)

        # 还原测试信息
        message_handlers.clear()
        self.officialaccount.encrypt_strategy = EncryptStrategy.ENCRYPTED
        self.officialaccount.save()

    def test_thirdplatform_handler(self):
        """测试三方平台消息处理"""
        view = Handler.as_view()
        query = self.make_query()
        raw_message = """<xml>
            <AppId>some_appid</AppId>
            <CreateTime>1413192605</CreateTime>
            <InfoType>component_verify_ticket</InfoType>
            <ComponentVerifyTicket>ticket</ComponentVerifyTicket>
        </xml>"""
        encrypted_message = self.thirdpartyplatform.crypto.encrypt_message(
            raw_message, query["nonce"], query["timestamp"])
        sign = xmltodict.parse(encrypted_message)["xml"]["MsgSignature"]
        query["msg_signature"] = sign
        request = self.make_request("POST", path="/",
                                    content_type="text/plain",
                                    data=encrypted_message,
                                    QUERY_STRING=urlencode(query))
        response = view(request, app_name=self.thirdpartyplatform.name)
        self.assertEqual(len(response.replies), 1)
        self.assertEqual(response.replies[0].render(), "success")

        thirdpartyplatform = Application.objects.get(
            name=self.thirdpartyplatform.name)
        self.assertEqual(thirdpartyplatform.verify_ticket, "ticket")

        del thirdpartyplatform.verify_ticket

    def test_authorizer_handler(self):
        """测试托管应用消息处理"""
        message_handlers.register(
            app_names=self.hosted_miniprogram.name, pass_through=True)(
            lambda message, request, *args, **kwargs: message.content)
        message_handlers.register(app_names=self.hosted_miniprogram.name)(
            lambda message, request, *args, **kwargs: request.wechat_app.name)
        view = AuthorizerHandler.as_view()

        query = self.make_query()
        raw_message = """<xml>
        <ToUserName><![CDATA[toUser]]></ToUserName>
        <FromUserName><![CDATA[{sender}]]></FromUserName>
        <CreateTime>{timestamp}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{content}]]></Content>
        <MsgId>1234567890123456</MsgId>
        </xml>""".format(
            sender="sender",
            content="content",
            timestamp=query["timestamp"]
        )
        encrypted_message = self.thirdpartyplatform.crypto.encrypt_message(
            raw_message, query["nonce"], query["timestamp"])
        sign = xmltodict.parse(encrypted_message)["xml"]["MsgSignature"]
        query["msg_signature"] = sign
        request = self.make_request("POST", path="/",
                                    content_type="text/plain",
                                    data=encrypted_message,
                                    QUERY_STRING=urlencode(query))
        response = view(request, app_name=self.thirdpartyplatform.name,
                        appid=self.hosted_miniprogram.appid)
        self.assertEqual(len(response.replies), 2)
        self.assertEqual(response.replies[0].content, "content")
        self.assertEqual(response.replies[1].content,
                         self.hosted_miniprogram.name)

    def test_request(self):
        """测试直接请求"""
        # GET请求echo
        query = self.make_query()
        query["echostr"] = "echostr"
        path = reverse("wechat_django:handler",
                       kwargs={"app_name": self.miniprogram.name})
        resp = self.client.get(path, QUERY_STRING=urlencode(query))
        self.assertEqual(resp.content, query["echostr"].encode())

        # 普通消息直接请求
        message_handlers.register(
            query={"content": "content"}, pass_through=True)(
                lambda message, request, *args, **kwargs: message.content)
        query = self.make_query()
        raw_message = """<xml>
        <ToUserName><![CDATA[toUser]]></ToUserName>
        <FromUserName><![CDATA[sender]]></FromUserName>
        <CreateTime>1413192605</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[content]]></Content>
        <MsgId>1234567890123456</MsgId>
        </xml>"""
        encrypted_message = self.miniprogram.crypto.encrypt_message(
            raw_message, query["nonce"], query["timestamp"])
        sign = xmltodict.parse(encrypted_message)["xml"]["MsgSignature"]
        query["msg_signature"] = sign
        path = reverse("wechat_django:handler",
                       kwargs={"app_name": self.miniprogram.name})
        resp = self.client.post(path, data=encrypted_message,
                                content_type="text/plain",
                                QUERY_STRING=urlencode(query))
        response_sign = xmltodict.parse(resp.content)["xml"]["MsgSignature"]
        decrypted_response = self.miniprogram.crypto.decrypt_message(
            resp.content, response_sign, query["timestamp"], query["nonce"])
        reply = xmltodict.parse(decrypted_response)
        self.assertEqual(reply["xml"]["Content"], "content")

        # 第三方平台直接请求
        query = self.make_query()
        raw_message = """<xml>
            <AppId>some_appid</AppId>
            <CreateTime>1413192605</CreateTime>
            <InfoType>component_verify_ticket</InfoType>
            <ComponentVerifyTicket>ticket</ComponentVerifyTicket>
        </xml>"""
        encrypted_message = self.thirdpartyplatform.crypto.encrypt_message(
            raw_message, query["nonce"], query["timestamp"])
        sign = xmltodict.parse(encrypted_message)["xml"]["MsgSignature"]
        query["msg_signature"] = sign
        path = reverse("wechat_django:handler",
                       kwargs={"app_name": self.thirdpartyplatform.name})
        resp = self.client.post(path, data=encrypted_message,
                                content_type="text/plain",
                                QUERY_STRING=urlencode(query))
        self.assertEqual(resp.content, b"success")
        thirdplatform = Application.objects.get(
            name=self.thirdpartyplatform.name)
        self.assertEqual(thirdplatform.verify_ticket, "ticket")

        # 托管应用直接请求
        query = self.make_query()
        raw_message = """<xml>
        <ToUserName><![CDATA[toUser]]></ToUserName>
        <FromUserName><![CDATA[sender]]></FromUserName>
        <CreateTime>1413192605</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[content]]></Content>
        <MsgId>1234567890123456</MsgId>
        </xml>"""
        encrypted_message = self.thirdpartyplatform.crypto.encrypt_message(
            raw_message, query["nonce"], query["timestamp"])
        sign = xmltodict.parse(encrypted_message)["xml"]["MsgSignature"]
        query["msg_signature"] = sign
        path = reverse("wechat_django:authorizer_handler",
                       kwargs={
                           "app_name": self.thirdpartyplatform.name,
                           "appid": self.hosted_miniprogram.appid
                        })
        resp = self.client.post(path, data=encrypted_message,
                                content_type="text/plain",
                                QUERY_STRING=urlencode(query))
        response_sign = xmltodict.parse(resp.content)["xml"]["MsgSignature"]
        decrypted_response = self.thirdpartyplatform.crypto.decrypt_message(
            resp.content, response_sign, query["timestamp"], query["nonce"])
        reply = xmltodict.parse(decrypted_response)
        self.assertEqual(reply["xml"]["Content"], "content")

        # 清除测试数据
        message_handlers.clear()
        del thirdplatform.verify_ticket

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
