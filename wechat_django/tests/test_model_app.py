# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import override_settings
from wechatpy.client import WeChatClient as _Client
from wechatpy.client.api import WeChatWxa

from ..models import WeChatApp
from .base import mock, WeChatTestCase
from .interceptors import wechatapi, wechatapi_accesstoken, wechatapi_error


class AppTestCase(WeChatTestCase):
    def test_getaccesstoken(self):
        """测试accesstoken获取"""
        api = "/cgi-bin/token"
        # 测试获取accesstoken
        with wechatapi_accesstoken(lambda url, req, resp: self.assertTrue(req)):
            token = self.app.client.access_token
            self.assertEqual(token, "ACCESS_TOKEN")
        # 测试获取后不再请求accesstoken
        success = dict(
            errcode=0,
            errmsg=""
        )
        with wechatapi_error(api), wechatapi("/cgi-bin/message/custom/send", success):
            resp = self.app.client.message.send_text("openid", "abc")
            self.assertEqual(resp["errcode"], 0)

    @override_settings(CACHES={
        "default": {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    })
    def test_custom_accesstoken_url(self):
        """测试设置了ACCESSTOKEN url后 不再向原地址发送请求,转为向新地址发送请求"""
        with mock.patch.object(_Client, "_fetch_access_token"):
            new_url = "new_url"
            self.app.configurations["ACCESSTOKEN_URL"] = new_url
            hasattr(self.app, "_client") and delattr(self.app, "_client")
            self.app.client.access_token
            self.assertEqual(
                _Client._fetch_access_token.call_args[0][0], new_url)
            delattr(self.app, "_client")
            del self.app.configurations["ACCESSTOKEN_URL"]

    def test_miniprogram_auth(self):
        """测试小程序授权"""
        openid = "mini_openid"
        session_key = "session_key"
        unionid = "unionid"
        app = WeChatApp.objects.create(
            title="miniprogram", name="miniprogram", appid="miniprogram",
            appsecret="secret", type=WeChatApp.Type.MINIPROGRAM)
        with mock.patch.object(WeChatWxa, "code_to_session"):
            return_value = dict(
                openid=openid,
                session_key=session_key,
                unionid=unionid
            )
            WeChatWxa.code_to_session.return_value = return_value
            code = "abcabc"
            user, data = app.auth(code)
            user_id = user.id
            WeChatWxa.code_to_session.assert_called_with(code)
            self.assertEqual(data, return_value)
            self.assertEqual(user.openid, openid)
            self.assertEqual(user.unionid, unionid)
            self.assertEqual(user.sessions.count(), 1)
            self.assertEqual(user.session.session_key, session_key)

        # 再一次授权
        session_key = "another_key"
        with mock.patch.object(WeChatWxa, "code_to_session"):
            return_value = dict(
                openid=openid,
                session_key=session_key,
                unionid=unionid
            )
            WeChatWxa.code_to_session.return_value = return_value
            code = "dddddd"
            user, data = app.auth(code)
            user_id = user.id
            WeChatWxa.code_to_session.assert_called_with(code)
            self.assertEqual(data, return_value)
            self.assertEqual(user.id, user_id)
            self.assertEqual(user.openid, openid)
            self.assertEqual(user.unionid, unionid)
            self.assertEqual(user.sessions.count(), 1)
            self.assertEqual(user.session.session_key, session_key)
