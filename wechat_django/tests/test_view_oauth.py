# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.conf.urls import url
from django.http import response
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils.http import urlencode
from six.moves.urllib.parse import parse_qsl, urlparse

from ..models import WeChatUser
from ..oauth import wechat_auth, WeChatOAuthHandler, WeChatSNSScope
from ..patches import WeChatOAuth
from .bases import WeChatTestCase
from .interceptors import common_interceptor


def oauth_api(openid, callback=None):
    kwargs = dict(
        netloc=r"(.*\.)?api\.weixin\.qq\.com$",
        path="/sns/oauth2/access_token"
    )

    def mock(url, request):
        headers = {
            "Content-Type": "application/json"
        }
        data = dict(
            access_token="123",
            refresh_token="123",
            expires_in=7200,
            openid=openid
        )
        from httmock import response
        resp = response(200, data, headers)
        if callback:
            callback(url, request, resp)
        return resp

    return common_interceptor(mock, **kwargs)


def snsinfo_api(openid, callback=None, **data):
    kwargs = dict(
        netloc=r"(.*\.)?api\.weixin\.qq\.com$",
        path="/sns/userinfo"
    )

    def mock(url, request):
        headers = {
            "Content-Type": "application/json"
        }
        from httmock import response
        resp = response(200, data, headers)
        if callback:
            callback(url, request, resp)
        return resp

    return common_interceptor(mock, **kwargs)


@wechat_auth("test", state="state")
def test_oauth_view(request, *args):
    user = request.wechat.user
    return dict(
        openid=user.openid,
        id=user.id,
        args=args
    )

urlpatterns = [
    url(r"^test/(.+)$", test_oauth_view)
]


@override_settings(ROOT_URLCONF=__name__)
class OAuthTestCase(WeChatTestCase):
    def test_oauth_api(self):
        """测试oauth接口请求"""
        pass

    def test_redirect_uri(self):
        """测试redirect_uri生成"""
        host = "example.com"
        rf = RequestFactory(HTTP_HOST=host)
        api = "/app"
        absolute_uri = lambda uri: "http://" + host + uri

        # 测试写入redirect_uri时
        redirect_uri = "https://mp.weixin.qq.com/wiki"
        decorator = wechat_auth(self.app.name, redirect_uri=redirect_uri)
        request = rf.get(api)
        self.assertEqual(decorator.redirect_uri(request), redirect_uri)

        redirect_uri = "/app"
        decorator = wechat_auth(self.app.name, redirect_uri=redirect_uri)
        request = rf.get(api)
        self.assertEqual(
            decorator.redirect_uri(request),
            absolute_uri(redirect_uri)
        )

        # 测试模板请求redirect_uri
        decorator = wechat_auth(self.app.name)
        request = rf.get(redirect_uri)
        self.assertEqual(
            decorator.redirect_uri(request),
            absolute_uri(redirect_uri)
        )

        # 测试ajax请求redirect_uri
        request = rf.post(api, dict(a=1),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_REFERRER=absolute_uri(redirect_uri))
        self.assertEqual(
            decorator.redirect_uri(request),
            absolute_uri(redirect_uri)
        )

    def test_unauthorization(self):
        rf = RequestFactory()
        path = "/test"
        redirect_uri = "https://mp.weixin.qq.com/wiki"

        # 默认response
        state = "abc"
        request = rf.get(path)
        handler = self._make_handler(
            request, redirect_uri=redirect_uri,
            scope=WeChatSNSScope.USERINFO, state=state)
        resp = handler.unauthorization_response(request)
        self.assertIsInstance(resp, response.HttpResponseRedirect)
        client = WeChatOAuth(self.app.appid, self.app.appsecret)
        self.assertEqual(resp.url, client.authorize_url(
            redirect_uri, WeChatSNSScope.USERINFO, state))

        # 传入callable state
        state = lambda request: request.path
        request = rf.get(path)
        handler = self._make_handler(
            request, redirect_uri=redirect_uri,
            scope=WeChatSNSScope.USERINFO, state=state)
        resp = handler.unauthorization_response(request)
        self.assertIsInstance(resp, response.HttpResponseRedirect)
        client = WeChatOAuth(self.app.appid, self.app.appsecret)
        self.assertEqual(resp.url, client.authorize_url(
            redirect_uri, WeChatSNSScope.USERINFO, path))

        # 传入callback response
        resp = response.HttpResponseForbidden()
        request = rf.get(path)
        handler = self._make_handler(request, response=resp)
        self.assertIs(
            resp,
            handler.unauthorization_response(request)
        )

        # 传入普通response
        resp_func = lambda request: response.HttpResponseForbidden(request.path)
        request = rf.get(path)
        handler = self._make_handler(request, response=resp_func)
        resp = handler.unauthorization_response(request)
        self.assertIsInstance(resp, response.HttpResponseForbidden)
        self.assertEqual(resp.content, path.encode())

    # def test_get_params(self):
    #     """测试url参数获取"""
    #     host = "example.com"
    #     path = "/test"
    #     code = "123456"
    #     state = ""

    #     decorator = wechat_auth(self.app.name)
    #     view = lambda request, *args, **kwargs: ""
    #     handler = WeChatOAuthHandler(decorator, view)
    #     rf = RequestFactory(HTTP_HOST=host)
    #     request = rf.get(path + "?" + urlencode(dict(
    #         code=code,
    #         state=state
    #     )))
    #     resp = handler.dispatch(request)
    #     self.assertEqual(resp, "")
    #     self.assertEqual(handler.get_params("code"), code)
    #     self.assertEqual(handler.get_params("state"), state)

    def test_auth(self):
        """测试授权"""
        rf = RequestFactory()
        openid = "abc"
        code = "def"

        # base授权
        request = rf.get("/test?code=" + code)
        handler = self._make_handler(request)
        with oauth_api(openid):
            resp = handler.auth()
            self.assertEqual(resp["openid"], openid)

        # snsinfo授权
        handler = self._make_handler(request, scope=WeChatSNSScope.USERINFO)
        with oauth_api(openid), snsinfo_api(openid, nickname=code):
            resp = handler.auth()
            self.assertEqual(resp["openid"], openid)
            self.assertEqual(resp["nickname"], code)

    def test_session(self):
        """测试授权后session状态保持"""
        openid = "12345"
        rf = RequestFactory()
        request = rf.get("/test?code=123")
        view = lambda request, *args, **kwargs: response.HttpResponse(request.wechat.openid)
        handler = self._make_handler(request, view=view)
        with oauth_api(openid):
            resp = handler.dispatch(request)
            self.assertEqual(resp.content, openid.encode())

        # 首次授权后不再授权
        session_key = "wechat_test_user"

        def ban_api(*args, **kwargs):
            self.assertFalse(True)
        request = rf.get("/test?code=123")
        request.COOKIES[session_key] = resp.cookies[session_key].value
        with oauth_api(openid, ban_api):
            resp = handler.dispatch(request)
        request = rf.get("/")
        request.COOKIES[session_key] = resp.cookies[session_key].value
        with oauth_api(openid, ban_api):
            resp = handler.dispatch(request)

    def test_user_update(self):
        "测试更新授权数据"
        pass

    def test_request(self):
        "测试请求"
        redirect_uri = "https://mp.weixin.qq.com/wiki"
        host = "example.com"
        url = "/test"
        rf = RequestFactory(HTTP_HOST=host)
        request = rf.get(url)

        # 设置了response
        resp = response.HttpResponseForbidden()
        handler = self._make_handler(
            request, redirect_uri=redirect_uri, response=resp)
        self.assertIs(handler.dispatch(request), resp)

        # 未授权
        handler = self._make_handler(request, redirect_uri=redirect_uri)
        resp = handler.dispatch(request)
        self.assertIsInstance(resp, response.HttpResponseRedirect)
        self.assertEqual(resp.url, request.wechat.oauth_uri)

        # 授权
        request = rf.get(url + "?code=123")
        openid = "456"
        view = lambda request, *args, **kwargs: request.wechat.openid
        handler = self._make_handler(request, redirect_uri=redirect_uri, view=view)
        with oauth_api(openid):
            resp = handler.dispatch(request)
            self.assertEqual(resp.content, openid.encode())

        # 已授权
        session_key = "wechat_test_user"
        request.COOKIES[session_key] = resp.cookies[session_key].value
        resp = handler.dispatch(request)
        self.assertEqual(resp.content, openid.encode())

    def test_view(self):
        """测试view是否正常"""
        args = "t"
        openid = "666"
        host = "example.com"
        path = "/test/" + args

        resp = self.client.get(path, HTTP_HOST="example.com")
        self.assertEqual(resp.status_code, 302)
        parsed_url = urlparse(resp.url)
        self.assertEqual(parsed_url.netloc, "open.weixin.qq.com")
        query = dict(parse_qsl(parsed_url.query))
        self.assertEqual(query["appid"], self.app.appid)
        self.assertEqual(query["response_type"], "code")
        self.assertEqual(query["scope"], WeChatSNSScope.BASE)
        self.assertEqual(query["state"], "state")
        self.assertEqual(parsed_url.fragment, "wechat_redirect")
        self.assertEqual(query["redirect_uri"], "http://" + host + path)

        with oauth_api(openid):
            resp = self.client.get(path + "?code=123", follow=True,
                HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode())
        self.assertEqual(data["openid"], openid)
        self.assertEqual(data["args"], [args])
        id = data["id"]
        user = WeChatUser.objects.get(id=id)
        self.assertEqual(user.openid, openid)

    def _make_handler(self, request, appname="", **kwargs):
        view = kwargs.pop("view", lambda request, *args, **kwargs: "")
        appname = appname or self.app.name
        decorator = wechat_auth(appname, **kwargs)
        handler = WeChatOAuthHandler(decorator, view)
        handler._patch_request(request)
        return handler
