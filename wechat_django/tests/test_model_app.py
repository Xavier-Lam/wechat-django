# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import override_settings
from django.urls import reverse
from wechatpy.client import WeChatClient as _Client
from wechatpy.client.api import WeChatWxa

from ..models import WeChatApp
from .. import settings
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
        app = self.miniprogram
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

    def test_build_url(self):
        """测试url构建"""
        def assertUrlCorrect(hostname, urlname, request=None, secure=False, kwargs=None):
            kwargs_copy = (kwargs or dict()).copy()
            kwargs_copy["appname"] = self.app.name
            location = reverse(
                "wechat_django:{0}".format(urlname), kwargs=kwargs_copy)
            self.assertEqual(
                location, self.app.build_url(urlname, kwargs, absolute=False))

            protocol = "https://" if secure else "http://"
            self.assertEqual(
                protocol + hostname + location,
                self.app.build_url(
                    urlname, kwargs, request=request, absolute=True))

        url_name = "handler"
        allowed_host = "example.com"
        request_host = "example.com:1000"
        settings_host = "example.com:2000"
        configure_host = "example.com:3000"
        req = self.rf(SERVER_NAME=request_host).get("/")

        # 连request都没有时,取allowed host的第一个
        assertUrlCorrect(allowed_host, url_name, secure=True)

        # 什么都没有配置时,取request的host
        assertUrlCorrect(request_host, url_name, req, secure=False)

        settings.SITE_HOST = settings_host
        settings.SITE_HTTPS = True

        # app中未设置site host 取设置里的site host
        assertUrlCorrect(settings_host, url_name, req, secure=True)
        
        # app中设置取app设置
        self.app.configurations["SITE_HTTPS"] = False
        self.app.configurations["SITE_HOST"] = configure_host
        assertUrlCorrect(configure_host, url_name, req, secure=False)
