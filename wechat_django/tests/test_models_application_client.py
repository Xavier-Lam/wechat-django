import base64
import time
from unittest import mock

from wechatpy import client, WeChatComponent, WeChatPay
from wechatpy.component import ComponentVerifyTicketMessage
from wechatpy.utils import to_binary

from wechat_django.messagehandler import thirdpartyplatform_ticket
from wechat_django.models import Application
from .base import wechatapi, WeChatDjangoTestCase


class ModelApplicationClientTestCase(WeChatDjangoTestCase):
    def test_session(self):
        """测试会话"""
        VALUE = "value"
        # 测试值被正确设置
        app = self.miniprogram
        key = "{0}_access_token".format(app.appid)
        self.assertIsNone(app.session.get(key))
        app.session.set(key, VALUE)
        self.assertEqual(app.session.get(key), VALUE)

        # 重新载入存在
        app = Application.objects.get(name=app.name)
        self.assertEqual(app.session.get(key), VALUE)

        # 测试未串号
        app = Application.objects.get(name=self.officialaccount.name)
        key = "{0}_access_token".format(app.appid)
        self.assertIsNone(app.session.get(key))

        # 测试黑洞
        app.session.set("blackhole", 1)
        self.assertIsNone(app.session.get("blackhole"))

        # 移除测试数据
        key = "{0}_access_token".format(self.miniprogram.appid)
        self.miniprogram.session.delete(key)

    def test_client(self):
        """测试请求类"""
        # 小程序
        self.assertIsInstance(self.miniprogram.client, client.api.WeChatWxa)
        self.assertEqual(self.miniprogram.base_client.appid,
                         self.miniprogram.appid)
        self.assertEqual(self.miniprogram.base_client.secret,
                         self.APPSECRET)

        # 公众号
        self.officialaccount.access_token_url = "url"
        self.assertIsInstance(self.officialaccount.client,
                              client.WeChatClient)
        self.assertEqual(self.officialaccount.client.ACCESSTOKEN_URL, "url")
        self.assertEqual(self.officialaccount.client.appid,
                         self.officialaccount.appid)
        self.assertEqual(self.officialaccount.client.secret, self.APPSECRET)
        self.assertIs(self.officialaccount.client,
                      self.officialaccount.base_client)

        # web应用
        self.assertIsInstance(self.webapp.client, client.WeChatClient)
        self.assertEqual(self.webapp.client.appid, self.webapp.appid)
        self.assertIs(self.webapp.client, self.webapp.base_client)

        # 一般商户
        pay_client = self.pay.client(self.officialaccount)
        self.assertIsInstance(pay_client, WeChatPay)
        self.assertEqual(pay_client.appid, self.officialaccount.appid)
        self.assertEqual(pay_client.mch_id, self.pay.mchid)
        self.assertEqual(pay_client.api_key, self.API_KEY)
        self.assertEqual(pay_client._mch_cert, self.MCH_CERT)
        self.assertEqual(pay_client._mch_key, self.MCH_KEY)

        # 服务商
        self.assertRaises(AttributeError, lambda: self.merchant.client)

        # 子商户
        pay_client = self.hosted_pay.client()
        self.assertIsInstance(pay_client, WeChatPay)
        self.assertEqual(pay_client.appid, self.hosted_pay.parent.appid)
        self.assertIsNone(pay_client.sub_appid)
        self.assertEqual(pay_client.mch_id, self.hosted_pay.parent.mchid)
        self.assertEqual(pay_client.sub_mch_id, self.hosted_pay.mchid)
        self.assertEqual(pay_client.api_key, self.API_KEY)
        self.assertEqual(pay_client._mch_cert, self.MCH_CERT)
        self.assertEqual(pay_client._mch_key, self.MCH_KEY)
        pay_client = self.hosted_pay.client(self.officialaccount)
        self.assertIsInstance(pay_client, WeChatPay)
        self.assertEqual(pay_client.appid, self.hosted_pay.parent.appid)
        self.assertEqual(pay_client.sub_appid, self.officialaccount.appid)
        self.assertEqual(pay_client.api_key, self.API_KEY)
        self.assertEqual(pay_client.mch_id, self.hosted_pay.parent.mchid)
        self.assertEqual(pay_client.sub_mch_id, self.hosted_pay.mchid)
        self.assertEqual(pay_client._mch_cert, self.MCH_CERT)
        self.assertEqual(pay_client._mch_key, self.MCH_KEY)

        # 第三方平台
        self.assertIsInstance(self.thirdpartyplatform.client, WeChatComponent)
        self.assertEqual(self.thirdpartyplatform.appid,
                         self.thirdpartyplatform.client.component_appid)
        self.assertEqual(self.thirdpartyplatform.client.component_appsecret,
                         self.APPSECRET)
        self.assertIs(self.thirdpartyplatform.client.crypto,
                      self.thirdpartyplatform.crypto)

        # 托管小程序
        self.assertIsInstance(self.hosted_miniprogram.client,
                              client.api.WeChatWxa)
        self.assertIsInstance(self.hosted_miniprogram.base_client,
                              client.WeChatComponentClient)
        self.assertIs(self.hosted_miniprogram.base_client.component,
                      self.hosted_miniprogram.parent.client)
        self.assertEqual(self.hosted_miniprogram.base_client.appid,
                         self.hosted_miniprogram.appid)

        # 托管公众号
        self.assertIsInstance(self.hosted_officialaccount.client,
                              client.WeChatComponentClient)
        self.assertIs(self.hosted_officialaccount.client.component,
                      self.hosted_officialaccount.parent.client)
        self.assertEqual(self.hosted_officialaccount.client.appid,
                         self.hosted_officialaccount.appid)
        self.assertIs(self.hosted_officialaccount.client,
                      self.hosted_officialaccount.base_client)

    def test_oauth(self):
        """测试OAuth"""
        # 一般应用
        self.assertIs(self.officialaccount.oauth.app,
                      self.officialaccount)
        self.assertEqual(self.officialaccount.oauth.app_id,
                         self.officialaccount.appid)
        self.assertEqual(self.officialaccount.oauth.secret, self.APPSECRET)

        # 三方应用
        self.assertIs(self.hosted_officialaccount.oauth.app,
                      self.hosted_officialaccount)
        self.assertEqual(
            self.hosted_officialaccount.oauth.component.component_appid,
            self.thirdpartyplatform.appid)
        self.thirdpartyplatform._access_token = "access_token"
        self.assertEqual(
            self.hosted_officialaccount.oauth.component.access_token,
            "access_token")
        self.thirdpartyplatform._access_token = "_access_token"
        self.assertEqual(
            self.hosted_officialaccount.oauth.component.access_token,
            "_access_token")

        # 清除测试数据
        del self.thirdpartyplatform._access_token

    def test_crypto(self):
        """测试加密对象"""
        # 一般应用
        self.assertEqual(self.officialaccount.crypto.app_id,
                         self.officialaccount.appid)
        self.assertEqual(self.officialaccount.crypto.token, self.TOKEN)
        key = to_binary(self.ENCODING_AES_KEY + "=")
        self.assertEqual(base64.b64decode(key),
                         self.officialaccount.crypto.key)

        # 托管应用
        self.assertIs(self.hosted_officialaccount.crypto,
                      self.hosted_officialaccount.parent.crypto)

    def test_wechat_client_access_token(self):
        """测试一般请求客户端Storage"""
        def wechatapi_access_token(token, callback=None):
            return wechatapi("/cgi-bin/token", {
                "access_token": token,
                "expires_in": 7200
            }, callback)

        with wechatapi_access_token("officialaccount"):
            self.assertEqual(self.officialaccount.access_token,
                             "officialaccount")
            self.assertEqual(self.officialaccount._access_token,
                             "officialaccount")
        self.assertEqual(self.officialaccount.client.access_token,
                         "officialaccount")

        with wechatapi_access_token("miniprogram"):
            self.assertEqual(self.miniprogram.access_token,
                             "miniprogram")
            self.assertEqual(self.miniprogram._access_token,
                             "miniprogram")
        self.assertEqual(self.miniprogram.base_client.access_token,
                         "miniprogram")

        # 移除测试数据
        del self.officialaccount._access_token
        del self.miniprogram._access_token

    def test_jsapi_storage(self):
        """测试jsapi存储"""
        with mock.patch.object(client.api.WeChatJSAPI, "get_ticket",
                               return_value={
                                   "ticket": "miniprogram",
                                   "expires_in": 3600
                                }):
            self.assertEqual(self.miniprogram.jsapi_ticket, "miniprogram")
            self.assertEqual(self.miniprogram._jsapi_ticket, "miniprogram")
            self.assertAlmostEqual(self.miniprogram._jsapi_ticket_expires_at,
                                   time.time() + 3600, delta=1)
        self.assertEqual(
            self.miniprogram.base_client.jsapi.get_jsapi_ticket(),
            "miniprogram")

        with mock.patch.object(client.api.WeChatJSAPI, "get_ticket",
                               return_value={
                                   "ticket": "official",
                                   "expires_in": 3600
                                }):
            self.assertEqual(self.officialaccount.jsapi_ticket, "official")
            self.assertEqual(self.officialaccount._jsapi_ticket, "official")
            self.assertAlmostEqual(
                self.officialaccount._jsapi_ticket_expires_at,
                time.time() + 3600, delta=1)
        self.assertEqual(
            self.officialaccount.client.jsapi.get_jsapi_ticket(), "official")

        with mock.patch.object(client.api.WeChatJSAPI, "get_ticket",
                               return_value={
                                   "ticket": "miniprogram",
                                   "expires_in": 3600
                                }):
            self.assertEqual(self.miniprogram.jsapi_card_ticket,
                             "miniprogram")
            self.assertEqual(self.miniprogram._jsapi_card_ticket,
                             "miniprogram")
            self.assertAlmostEqual(
                self.miniprogram._jsapi_card_ticket_expires_at,
                time.time() + 3600, delta=1)
        self.assertEqual(
            self.miniprogram.base_client.jsapi.get_jsapi_card_ticket(),
            "miniprogram")

        with mock.patch.object(client.api.WeChatJSAPI, "get_ticket",
                               return_value={
                                   "ticket": "official",
                                   "expires_in": 3600
                                }):
            self.assertEqual(self.officialaccount.jsapi_card_ticket,
                             "official")
            self.assertEqual(self.officialaccount._jsapi_card_ticket,
                             "official")
            self.assertAlmostEqual(
                self.officialaccount._jsapi_card_ticket_expires_at,
                time.time() + 3600, delta=1)
        self.assertEqual(
            self.officialaccount.client.jsapi.get_jsapi_card_ticket(),
            "official")

    def test_thirdpartyplatform_storage(self):
        """测试第三方平台存储"""
        request = self.make_request("POST", path="/",
                                    wechat_app=self.thirdpartyplatform)
        # 接收verify_ticket
        thirdpartyplatform_ticket(
            ComponentVerifyTicketMessage({"ComponentVerifyTicket": "ticket"}),
            request)
        self.assertEqual(self.thirdpartyplatform.verify_ticket, "ticket")
        self.assertEqual(
            self.thirdpartyplatform.client.component_verify_ticket, "ticket")
        thirdpartyplatform = Application.objects.get(
            name=self.thirdpartyplatform.name)
        self.assertEqual(thirdpartyplatform.verify_ticket, "ticket")
        self.assertEqual(thirdpartyplatform.client.component_verify_ticket,
                         "ticket")

        # access_token
        def wechatapi_access_token(token, callback=None):
            return wechatapi("/cgi-bin/component/api_component_token", {
                "component_access_token": token,
                "expires_in": 7200
            }, callback)

        with wechatapi_access_token("token"):
            self.assertEqual(self.thirdpartyplatform.access_token, "token")
            self.assertEqual(self.thirdpartyplatform._access_token, "token")
        self.assertEqual(self.thirdpartyplatform.access_token, "token")
        self.assertEqual(self.thirdpartyplatform.client.access_token, "token")

        # 初次鉴权
        auth_result = {
            "authorization_info": {
                "authorizer_appid": self.hosted_miniprogram.appid,
                "authorizer_access_token": "authorizer_access_token",
                "expires_in": 7200,
                "authorizer_refresh_token": "authorizer_refresh_token"
            }
        }
        with mock.patch.object(WeChatComponent, "_query_auth",
                               return_value=auth_result):
            self.thirdpartyplatform.query_auth("code")
        hosted_miniprogram = Application.objects.get(
            name=self.hosted_miniprogram.name)
        self.assertEqual(hosted_miniprogram._access_token,
                         "authorizer_access_token")
        self.assertEqual(hosted_miniprogram.access_token,
                         "authorizer_access_token")
        self.assertEqual(hosted_miniprogram.refresh_token,
                         "authorizer_refresh_token")
        self.assertEqual(hosted_miniprogram.base_client.access_token,
                         "authorizer_access_token")
        self.assertEqual(hosted_miniprogram.base_client.refresh_token,
                         "authorizer_refresh_token")

        # 移除测试数据
        del hosted_miniprogram._access_token
        del hosted_miniprogram.refresh_token

    def test_authorizer_storage(self):
        """测试第三方平台托管应用存储"""
        result = {
            "authorizer_access_token": "new_access_token",
            "expires_in": 7200,
            "authorizer_refresh_token": "new_refresh_token"
        }
        with mock.patch.object(WeChatComponent, "refresh_authorizer_token",
                               return_value=result):
            self.assertEqual(self.hosted_miniprogram.access_token,
                             "new_access_token")
            self.assertEqual(self.hosted_miniprogram._access_token,
                             "new_access_token")
            self.assertEqual(self.hosted_miniprogram.refresh_token,
                             "new_refresh_token")
            self.assertEqual(self.hosted_miniprogram.base_client.access_token,
                             "new_access_token")
            self.assertEqual(
                self.hosted_miniprogram.base_client.refresh_token,
                "new_refresh_token")

        hosted_miniprogram = Application.objects.get(
            name=self.hosted_miniprogram.name)
        self.assertEqual(hosted_miniprogram._access_token, "new_access_token")
        self.assertEqual(hosted_miniprogram.access_token, "new_access_token")
        self.assertEqual(hosted_miniprogram.refresh_token,
                         "new_refresh_token")
        self.assertEqual(hosted_miniprogram.base_client.access_token,
                         "new_access_token")
        self.assertEqual(hosted_miniprogram.base_client.refresh_token,
                         "new_refresh_token")

        # 测试jsapi
        with mock.patch.object(client.api.WeChatJSAPI, "get_ticket",
                               return_value={
                                   "ticket": "authorizer",
                                   "expires_in": 3600
                                }):
            self.assertEqual(hosted_miniprogram.jsapi_ticket, "authorizer")
            self.assertEqual(hosted_miniprogram._jsapi_ticket, "authorizer")
            self.assertAlmostEqual(
                hosted_miniprogram._jsapi_ticket_expires_at,
                time.time() + 3600, delta=1)
        self.assertEqual(
            hosted_miniprogram.base_client.jsapi.get_jsapi_ticket(),
            "authorizer")

        # 移除测试数据
        del hosted_miniprogram._access_token
        del hosted_miniprogram.refresh_token
