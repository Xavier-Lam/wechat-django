# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.conf.urls import url
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import response
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils.http import urlencode
import six
from six.moves.urllib.parse import parse_qsl, urlparse

from ..models import WeChatUser
from ..oauth import (WeChatAuthenticated, wechat_auth, WeChatSNSScope,
                     WeChatOAuthClient, WeChatOAuthView)
from .base import mock, WeChatTestCase
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
        rf = self.rf(HTTP_HOST=host)
        api = "/app"
        absolute_uri = lambda uri: "http://" + host + uri

        # 测试写入redirect_uri时
        redirect_uri = "https://mp.weixin.qq.com/wiki"
        view_cls = WeChatOAuthView(
            appname=self.app.name, redirect_uri=redirect_uri)
        request = rf.get(api)
        SessionMiddleware().process_request(request)
        view_cls.setup(request)
        request = view_cls.initialize_request(request)
        self.assertEqual(request.wechat.redirect_uri, redirect_uri)

        redirect_uri = "/app"
        view_cls = WeChatOAuthView(
            appname=self.app.name, redirect_uri=redirect_uri)
        request = rf.get(api)
        SessionMiddleware().process_request(request)
        view_cls.setup(request)
        request = view_cls.initialize_request(request)
        self.assertEqual(request.wechat.redirect_uri,
                         absolute_uri(redirect_uri))

        # 测试模板请求redirect_uri
        view_cls = WeChatOAuthView(appname=self.app.name)
        request = rf.get(redirect_uri)
        SessionMiddleware().process_request(request)
        view_cls.setup(request)
        request = view_cls.initialize_request(request)
        self.assertEqual(request.wechat.redirect_uri,
                         absolute_uri(redirect_uri))

        # 测试ajax请求redirect_uri
        view_cls = WeChatOAuthView(appname=self.app.name)
        request = rf.post(api, dict(a=1),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_REFERRER=absolute_uri(redirect_uri))
        SessionMiddleware().process_request(request)
        view_cls.setup(request)
        request = view_cls.initialize_request(request)
        self.assertEqual(request.wechat.redirect_uri,
                         absolute_uri(redirect_uri))

        # 测试callable redirect_uri
        callable_redirect = lambda request, *args, **kwargs: redirect_uri
        view_cls = WeChatOAuthView(appname=self.app.name,
                                   redirect_uri=callable_redirect)
        request = rf.get(redirect_uri)
        SessionMiddleware().process_request(request)
        view_cls.setup(request)
        request = view_cls.initialize_request(request)
        self.assertEqual(request.wechat.redirect_uri,
                         absolute_uri(redirect_uri))

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
        request = handler.initialize_request(request)
        resp = handler.unauthorization_response(request)
        self.assertIsInstance(resp, response.HttpResponseRedirect)
        client = WeChatOAuthClient(self.app)
        self.assertEqual(resp.url, client.authorize_url(
            redirect_uri, WeChatSNSScope.USERINFO, state))

        # 传入callable state
        state = lambda request: request.path
        request = rf.get(path)
        handler = self._make_handler(
            request, redirect_uri=redirect_uri,
            scope=WeChatSNSScope.USERINFO, state=state)
        request = handler.initialize_request(request)
        resp = handler.unauthorization_response(request)
        self.assertIsInstance(resp, response.HttpResponseRedirect)
        client = WeChatOAuthClient(self.app)
        self.assertEqual(resp.url, client.authorize_url(
            redirect_uri, WeChatSNSScope.USERINFO, path))

        # 传入callback response
        resp = response.HttpResponseForbidden()
        request = rf.get(path)
        handler = self._make_handler(request, response=resp)
        request = handler.initialize_request(request)
        self.assertIs(
            resp,
            handler.unauthorization_response(request)
        )

        # 传入普通response
        resp_func = lambda request: response.HttpResponseForbidden(request.path)
        request = rf.get(path)
        handler = self._make_handler(request, response=resp_func)
        request = handler.initialize_request(request)
        resp = handler.unauthorization_response(request)
        self.assertIsInstance(resp, response.HttpResponseForbidden)
        self.assertEqual(resp.content, path.encode())

    def test_user_update(self):
        "测试更新授权数据"
        pass

    def test_request(self):
        "测试请求"
        redirect_uri = "https://mp.weixin.qq.com/wiki"
        url = "/test"
        request = self._create_request(url)

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
        request = self._create_request(url + "?code=123")
        openid = "456"
        view = lambda request, *args, **kwargs: request.wechat.openid
        handler = self._make_handler(request, view=view)
        with oauth_api(openid):
            resp = handler.dispatch(request)
            self.assertEqual(resp.content, openid.encode())

        # 已授权
        session_key = "sessionid"
        resp = SessionMiddleware().process_response(request, resp)
        request = self._create_request(url + "?code=123")
        request.COOKIES[session_key] = resp.cookies[session_key].value
        resp = handler.dispatch(request)
        self.assertEqual(resp.content, openid.encode())

    def test_decorator(self):
        """测试class based view与decorator是否一致"""
        openid = "test_decorator"
        user = WeChatUser.objects.upsert_by_dict(
            dict(openid=openid), app=self.app)
        session_key = "wechat_{0}_user".format(self.app.name)

        view = lambda request: request
        # 测试appname
        wrapped_view = wechat_auth(self.app.name)(view)
        request = self._create_request("/")
        request.session[session_key] = openid
        self.assertEqual(wrapped_view(request).wechat.appname, self.app.name)

        # 测试scope
        wrapped_view = wechat_auth(
            self.app.name, scope=WeChatSNSScope.USERINFO)(view)
        request = self._create_request("/")
        request.session[session_key] = openid
        self.assertIn(WeChatSNSScope.USERINFO, wrapped_view(request).wechat.scope)

        # 测试redirect_uri
        redirect_uri = "https://www.baidu.com/"
        wrapped_view = wechat_auth(
            self.app.name, redirect_uri=redirect_uri)(view)
        request = self._create_request("/")
        request.session[session_key] = openid
        self.assertEqual(wrapped_view(request).wechat.redirect_uri, redirect_uri)

        # 测试required
        wrapped_view = wechat_auth(self.app.name, required=False)(view)
        request = self._create_request("/")
        self.assertEqual(wrapped_view(request), request)

        # 测试默认required及response
        resp = response.HttpResponse()
        wrapped_view = wechat_auth(self.app.name, response=resp)(view)
        request = self._create_request("/")
        self.assertEqual(wrapped_view(request), resp)

        # 测试state
        state = "abc"
        wrapped_view = wechat_auth(
            self.app.name, state=state)(view)
        request = self._create_request("/")
        request.session[session_key] = openid
        self.assertEqual(wrapped_view(request).wechat.state, state)

        # 测试methods
        request_get = self._create_request("/")
        request_get.session[session_key] = openid
        request_post = self._create_request("/", "post")
        request_post.session[session_key] = openid

        # 测试仅get
        view = lambda request: resp
        wrapped_view = wechat_auth(self.app.name)(view)
        self.assertEqual(wrapped_view(request_get), resp)
        self.assertIsInstance(wrapped_view(request_post),
                              response.HttpResponseNotAllowed)
        
        # 测试仅post
        wrapped_view = wechat_auth(self.app.name, methods=["POST"])(view)
        self.assertIsInstance(wrapped_view(request_get),
                              response.HttpResponseNotAllowed)
        self.assertEqual(wrapped_view(request_post), resp)

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

    def test_custom_oauth_url(self):
        """测试设置了OAUTH_URL url后 不再向微信请求授权,转向第三方请求授权"""
        with mock.patch.object(WeChatOAuthClient, "authorize_url"):
            new_url = "new_url"
            self.app.configurations["OAUTH_URL"] = new_url
            hasattr(self.app, "_oauth") and delattr(self.app, "_oauth")
            url = self.app.oauth.authorize_url("redirect_url")
            self.assertTrue(url.startswith(new_url))
            delattr(self.app, "_oauth")
            del self.app.configurations["OAUTH_URL"]

    def _make_handler(self, request, appname="", **kwargs):
        view = kwargs.pop("view", lambda request, *args, **kwargs: "")
        appname = appname or self.app.name
        scope = kwargs.get("scope")
        if scope and isinstance(scope, six.text_type):
            kwargs["scope"] = (scope,)
        cls = type("WeChatOAuthView", (WeChatOAuthView,), dict())
        kwargs = cls.prepare_init_kwargs(appname=appname, **kwargs)
        rv = cls(**kwargs)
        rv.setup(request)
        rv.get = view
        return rv

    def _create_request(self, path, method="get"):
        request = getattr(self.rf(), method)(path)
        SessionMiddleware().process_request(request)
        return request
