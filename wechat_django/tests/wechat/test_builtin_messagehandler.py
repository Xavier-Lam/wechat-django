from unittest import mock
from wechatpy import WeChatComponent

from wechat_django.messagehandler.builtins import builtin_handlers
from wechat_django.models import Application
from ..base import WeChatDjangoTestCase


class BuiltinMessageHandlerTestCase(WeChatDjangoTestCase):
    def test_builtin_subscribe_handlers(self):
        """测试内建关注相关处理器"""
        # 关注
        app = self.officialaccount
        openid = "test_builtin_subscribe_handlers"
        user = app.users.create(openid=openid)
        request = self.make_request("POST", path="/", wechat_app=app,
                                    user=user)
        xml = """<xml>
            <ToUserName><![CDATA[toUser]]></ToUserName>
            <FromUserName><![CDATA[{0}]]></FromUserName>
            <CreateTime>123456789</CreateTime>
            <MsgType><![CDATA[event]]></MsgType>
            <Event><![CDATA[subscribe]]></Event>
        </xml>""".format(openid)
        message = app.parse_message(xml)
        result = builtin_handlers.handle(message, request)
        self.assertTrue(request.user.openid, openid)
        self.assertTrue(hasattr(request.user, "first_subscribe"))
        self.assertTrue(request.user.first_subscribe)
        self.assertTrue(request.user.subscribed)
        self.assertTrue(request.user.latest_subscribe_time)
        self.assertFalse(len(result))
        user = app.users.get(openid=openid)
        self.assertTrue(user.openid, openid)
        self.assertTrue(user.subscribed)
        self.assertTrue(user.latest_subscribe_time)

        # 扫码不触发
        app = self.officialaccount
        openid = "test_builtin_subscribe_handlers"
        request = self.make_request("POST", path="/", wechat_app=app,
                                    user=user)
        xml = """<xml>
            <ToUserName><![CDATA[toUser]]></ToUserName>
            <FromUserName><![CDATA[{0}]]></FromUserName>
            <CreateTime>123456789</CreateTime>
            <MsgType><![CDATA[event]]></MsgType>
            <Event><![CDATA[SCAN]]></Event>
            <EventKey><![CDATA[SCENE_VALUE]]></EventKey>
            <Ticket><![CDATA[TICKET]]></Ticket>
        </xml>""".format(openid)
        message = app.parse_message(xml)
        result = builtin_handlers.handle(message, request)
        self.assertFalse(hasattr(request.user, "first_subscribe"))

        # 取关
        app = self.officialaccount
        openid = "test_builtin_subscribe_handlers"
        request = self.make_request("POST", path="/", wechat_app=app,
                                    user=user)
        xml = """<xml>
            <ToUserName><![CDATA[toUser]]></ToUserName>
            <FromUserName><![CDATA[{0}]]></FromUserName>
            <CreateTime>123456789</CreateTime>
            <MsgType><![CDATA[event]]></MsgType>
            <Event><![CDATA[unsubscribe]]></Event>
        </xml>""".format(openid)
        message = app.parse_message(xml)
        result = builtin_handlers.handle(message, request)
        self.assertTrue(request.user.openid, openid)
        self.assertFalse(request.user.subscribed)
        self.assertTrue(request.user.latest_unsubscribe_time)
        self.assertFalse(len(result))
        user = app.users.get(openid=openid)
        self.assertTrue(user.openid, openid)
        self.assertFalse(user.subscribed)
        self.assertTrue(user.latest_unsubscribe_time)

        # 再度关注
        app = self.officialaccount
        openid = "test_builtin_subscribe_handlers"
        request = self.make_request("POST", path="/", wechat_app=app,
                                    user=user)
        xml = """<xml>
            <ToUserName><![CDATA[toUser]]></ToUserName>
            <FromUserName><![CDATA[{0}]]></FromUserName>
            <CreateTime>123456789</CreateTime>
            <MsgType><![CDATA[event]]></MsgType>
            <Event><![CDATA[subscribe]]></Event>
        </xml>""".format(openid)
        message = app.parse_message(xml)
        result = builtin_handlers.handle(message, request)
        self.assertTrue(request.user.openid, openid)
        self.assertTrue(hasattr(request.user, "first_subscribe"))
        self.assertFalse(request.user.first_subscribe)
        self.assertTrue(request.user.subscribed)
        self.assertTrue(request.user.latest_subscribe_time)
        self.assertFalse(len(result))
        user = app.users.get(openid=openid)
        self.assertTrue(user.openid, openid)
        self.assertTrue(user.subscribed)
        self.assertTrue(user.latest_subscribe_time)

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
