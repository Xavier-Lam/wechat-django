from unittest.mock import patch
from urllib.parse import parse_qsl, urlencode, urlparse

from django.test.utils import override_settings
from django.urls.base import reverse
from django.urls.conf import path

from wechat_django.authentication import OAuthCodeSessionAuthentication
from wechat_django.oauth import WeChatOAuthView
from wechat_django.utils.wechatpy import ComponentOAuth, WeChatOAuth
from ..base import WeChatDjangoTestCase
from ..urls import urlpatterns


class TestView(WeChatOAuthView):
    def get(self, request, *args, **kwargs):
        return "success"


urlpatterns += [
    path("unittest/oauth/",
         TestView.as_view(wechat_app_name="officialaccount"),
         name="unittest.oauth"),
    path("unittest/hostedoauth/",
         TestView.as_view(
             wechat_app_name="thirdpartyplatform.officialaccount"),
         name="unittest.hostedoauth")
]


class OAuthTestCase(WeChatDjangoTestCase):
    @override_settings(ROOT_URLCONF=__name__)
    def test_oauth2_flow(self):
        """测试完整流程"""
        app = self.officialaccount
        host = "wechat.django"
        url = reverse("unittest.oauth")

        # 初次请求,未授权
        response = self.client.get(url, HTTP_HOST=host, secure=True)
        request = response.wsgi_request
        self.assertEqual(response.status_code, 302)

        parsed_url = urlparse(response.url)
        parsed_query = dict(parse_qsl(parsed_url.query))
        self.assertEqual(response.url.split("?")[0],
                         app.DEFAULT_AUTHORIZE_URL)
        self.assertEqual(parsed_query["appid"], app.appid)
        proxy_page = reverse("wechat_django:oauth_proxy",
                             kwargs={"app_name": app.name})
        full_url = request.build_absolute_uri(url)
        redirect_uri = "{0}?{1}".format(
            request.build_absolute_uri(proxy_page),
            urlencode({"redirect_uri": full_url}))
        self.assertEqual(parsed_query["redirect_uri"], redirect_uri)
        self.assertEqual(parsed_query["scope"], app.DEFAULT_SCOPES)
        self.assertFalse(parsed_query.get("state"))
        self.assertEqual(parsed_url.fragment, "wechat_redirect")

        # 授权回来
        code = "code"
        data = {
            "redirect_uri": full_url,
            "scope": parsed_query["scope"],
            "state": "",
            "code": code
        }
        openid = "test_oauth2_flow"
        oauth_data = {
            "access_token": "access_token",
            "expires_in": 7200,
            "refresh_token": "refresh_token",
            "openid": openid,
            "scope": app.DEFAULT_SCOPES
        }
        with patch.object(WeChatOAuth, "fetch_access_token",
                          return_value=oauth_data):
            response = self.client.get(proxy_page, data, HTTP_HOST=host,
                                       secure=True)
            WeChatOAuth.fetch_access_token.assert_called_once_with(code)
            request = response.wsgi_request
            self.assertTrue(request.user.created)
            user = app.users.get(openid=openid)
            self.assertEqual(request.user.id, user.id)
            auth = OAuthCodeSessionAuthentication()
            session_key = auth.get_session_key(app)
            self.assertEqual(request.session[session_key], openid)
            self.assertEqual(response.url, full_url)

        # 重定向回到原页面
        response = self.client.get(url, HTTP_HOST=host, secure=True)
        request = response.wsgi_request
        self.assertEqual(request.user.id, user.id)
        auth = OAuthCodeSessionAuthentication()
        session_key = auth.get_session_key(app)
        self.assertEqual(request.session[session_key], openid)
        self.assertEqual(response.content, b"success")

    @override_settings(ROOT_URLCONF=__name__)
    def test_authorizer_oauth2_flow(self):
        """测试托管应用完整流程"""
        app = self.hosted_officialaccount
        host = "wechat.django"
        url = reverse("unittest.hostedoauth")

        # 初次请求,未授权
        response = self.client.get(url, HTTP_HOST=host, secure=True)
        request = response.wsgi_request
        self.assertEqual(response.status_code, 302)

        parsed_url = urlparse(response.url)
        parsed_query = dict(parse_qsl(parsed_url.query))
        self.assertEqual(response.url.split("?")[0],
                         app.DEFAULT_AUTHORIZE_URL)
        self.assertEqual(parsed_query["appid"], app.appid)
        self.assertEqual(parsed_query["component_appid"], app.parent.appid)
        proxy_page = reverse("wechat_django:oauth_proxy",
                             kwargs={"app_name": app.name})
        full_url = request.build_absolute_uri(url)
        redirect_uri = "{0}?{1}".format(
            request.build_absolute_uri(proxy_page),
            urlencode({"redirect_uri": full_url}))
        self.assertEqual(parsed_query["redirect_uri"], redirect_uri)
        self.assertEqual(parsed_query["scope"], app.DEFAULT_SCOPES)
        self.assertFalse(parsed_query.get("state"))
        self.assertEqual(parsed_url.fragment, "wechat_redirect")

        # 授权回来
        code = "code"
        data = {
            "redirect_uri": full_url,
            "scope": parsed_query["scope"],
            "state": "",
            "code": code
        }
        openid = "test_authorizer_oauth2_flow"
        oauth_data = {
            "access_token": "access_token",
            "expires_in": 7200,
            "refresh_token": "refresh_token",
            "openid": openid,
            "scope": app.DEFAULT_SCOPES
        }
        with patch.object(ComponentOAuth, "fetch_access_token",
                          return_value=oauth_data):
            response = self.client.get(proxy_page, data, HTTP_HOST=host,
                                       secure=True)
            ComponentOAuth.fetch_access_token.assert_called_once_with(code)
            request = response.wsgi_request
            self.assertTrue(request.user.created)
            user = app.users.get(openid=openid)
            self.assertEqual(request.user.id, user.id)
            auth = OAuthCodeSessionAuthentication()
            session_key = auth.get_session_key(app)
            self.assertEqual(request.session[session_key], openid)
            self.assertEqual(response.url, full_url)

        # 重定向回到原页面
        response = self.client.get(url, HTTP_HOST=host, secure=True)
        request = response.wsgi_request
        self.assertEqual(request.user.id, user.id)
        auth = OAuthCodeSessionAuthentication()
        session_key = auth.get_session_key(app)
        self.assertEqual(request.session[session_key], openid)
        self.assertEqual(response.content, b"success")
