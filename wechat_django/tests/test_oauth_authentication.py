# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.sessions.middleware import SessionMiddleware
from wechatpy.oauth import WeChatOAuthException

from ..models import WeChatApp, WeChatUser
from wechat_django.oauth import (WeChatAuthenticated, WeChatOAuthClient,
                                 WeChatOAuthSessionAuthentication,
                                 WeChatOAuthView, WeChatSNSScope)
from .base import mock, WeChatTestCase


class OAuthAuthenticationTestCase(WeChatTestCase):
    def test_authentication(self):
        """测试WeChatOAuthSessionAuthentication"""

        path = "/test"
        openid = "openid_test_authentication"

        auth = WeChatOAuthSessionAuthentication()
        user_dict = dict(openid=openid)
        wechat_user = WeChatUser.objects.upsert_by_dict(user_dict, self.app)

        # 未认证用户返回False header返回非空
        request = self._create_request(path)
        view = self._make_view(request)
        request = view.initialize_request(request)
        self.assertIsNone(auth.authenticate(request))
        self.assertTrue(auth.authenticate_header(request))

        # code认证用户返回True 并正确记录session
        code = "123456"
        request = self._create_request(path + "?code=" + code)
        request = view.initialize_request(request)
        with mock.patch.object(WeChatApp, "auth"):
            WeChatApp.auth.return_value = wechat_user, user_dict
            user, authed_openid = auth.authenticate(request)
            self.assertTrue(user.id)
            self.assertEqual(user.openid, openid)
            self.assertEqual(authed_openid, openid)
            self.assertEqual(request.session[request.wechat.session_key],
                             openid)
            self.assertEqual(request.wechat.user.openid, openid)
            self.assertEquals(WeChatApp.auth.call_args[0][0], code)

        # session认证用户返回True
        request = self._create_request(path + "?code=" + code)
        request = view.initialize_request(request)
        request.session[request.wechat.session_key] = openid
        with mock.patch.object(WeChatApp, "auth"):
            user, authed_openid = auth.authenticate(request)
            self.assertEqual(user.openid, openid)
            self.assertEqual(authed_openid, openid)
            self.assertEqual(request.session[request.wechat.session_key],
                             openid)
            self.assertEqual(request.wechat.user.openid, openid)
            # session认证用户不调用code认证代码
            self.assertFalse(WeChatApp.auth.called)

        # 认证异常用户返回False
        # 假code
        request = self._create_request(path + "?code=" + code)
        request = view.initialize_request(request)
        with mock.patch.object(WeChatApp, "auth"):
            WeChatApp.auth.side_effect = WeChatOAuthException(0, "")
            self.assertIsNone(auth.authenticate(request))
            self.assertTrue(auth.authenticate_header(request))

    def test_model_auth(self):
        """测试WeChatApp.auth"""

        code = "code"
        openid = "openid_test_model_auth"

        # base授权
        with mock.patch.object(WeChatOAuthClient, "fetch_access_token"):
            WeChatOAuthClient.fetch_access_token.return_value = dict(
                openid=openid)

            user, user_dict = self.app.auth(code, WeChatSNSScope.BASE)
            self.assertTrue(user.id)
            self.assertEqual(user.openid, openid)
            self.assertEqual(user_dict["openid"], openid)
            WeChatOAuthClient.fetch_access_token.assert_called_with(code)

        # snsinfo授权
        openid = "openid_test_model_auth2"
        nickname = "nickname"
        user_info = dict(openid=openid, nickname=nickname)
        with mock.patch.object(WeChatOAuthClient, "fetch_access_token"),\
             mock.patch.object(WeChatOAuthClient, "get_user_info"):
            WeChatOAuthClient.fetch_access_token.return_value = dict(
                openid=openid)
            WeChatOAuthClient.get_user_info.return_value = user_info

            user, user_dict = self.app.auth(code, WeChatSNSScope.USERINFO)
            self.assertTrue(user.id)
            self.assertEqual(user.openid, openid)
            self.assertEqual(user.nickname, nickname)
            self.assertEqual(user_dict, user_info)
            WeChatOAuthClient.fetch_access_token.assert_called_with(code)

    def test_permissions(self):
        """测试WeChatAuthenticated权限"""
        path = "/test"
        openid = "openid_test_permissions"

        permission = WeChatAuthenticated()
        user_dict = dict(openid=openid)
        WeChatUser.objects.upsert_by_dict(user_dict, self.app)

        # 未认证用户返回False
        request = self._create_request(path)
        view = self._make_view(request)
        request = view.initialize_request(request)
        self.assertFalse(permission.has_permission(request, view))

        # TODO: 怎么测认证失败用户返回False

        # 认证用户返回True
        request = self._create_request(path)
        view = self._make_view(request)
        request = view.initialize_request(request)
        request.session[request.wechat.session_key] = openid
        self.assertTrue(permission.has_permission(request, view))
        self.assertTrue(permission.has_object_permission(request, view, None))

    def _make_handler(self, request, appname="", **kwargs):
        view = kwargs.pop("view", lambda request, *args, **kwargs: "")
        rv = self._make_view(request, appname, **kwargs)
        rv.initialize_request(request)
        rv.get = view
        return rv

    def _make_view(self, request, appname="", **kwargs):
        appname = appname or self.app.name
        rv = WeChatOAuthView(appname=appname, **kwargs)
        rv.setup(request)
        return rv

    def _create_request(self, path):
        request = self.rf().get(path)
        SessionMiddleware().process_request(request)
        return request
