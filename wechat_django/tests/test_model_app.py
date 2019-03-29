# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import override_settings
from wechatpy.client import WeChatClient as _Client

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
