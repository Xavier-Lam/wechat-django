from unittest.mock import patch
from urllib.parse import parse_qsl, urlencode, urlparse

from django.urls.base import reverse

from wechat_django.enums import WeChatOAuthScope
from wechat_django.utils.wechatpy import WeChatOAuth
from .base import WeChatDjangoTestCase


class ModelMixinTestCase(WeChatDjangoTestCase):
    def test_oauth_auth(self):
        """测试oauth的auth方法"""
        # 测试base scope
        code = "code"
        openid = "ModelMixinTestCase_test_oauth"
        scopes = WeChatOAuthScope.BASE
        access_token = "ACCESS_TOKEN"
        refresh_token = "REFRESH_TOKEN"
        data = {
            "access_token": access_token,
            "expires_in": 7200,
            "refresh_token": refresh_token,
            "openid": openid,
            "scope": scopes
        }
        with patch.object(WeChatOAuth, "fetch_access_token",
                          return_value=data):
            user = self.officialaccount.auth(code, scopes)
            WeChatOAuth.fetch_access_token.assert_called_once_with(code)
            self.assertTrue(user.created)
            self.assertEqual(user.app_id, self.officialaccount.id)
            self.assertEqual(user.openid, openid)
            self.assertEqual(user.access_token, access_token)
            self.assertEqual(user.refresh_token, refresh_token)

        # 测试userinfo scope
        scopes = WeChatOAuthScope.USERINFO
        access_token = "ACCESS_TOKEN2",
        refresh_token = "REFRESH_TOKEN2"
        data = {
            "access_token": access_token,
            "expires_in": 7200,
            "refresh_token": refresh_token,
            "openid": openid,
            "scope": scopes
        }
        userinfo_data = {
            "openid": openid,
            "nickname": "NICKNAME",
            "sex": 1,
            "province": "PROVINCE",
            "city": "CITY",
            "country": "COUNTRY",
            "headimgurl": "https://thirdwx.qlogo.cn/",
            "privilege": ["PRIVILEGE1", "PRIVILEGE2"],
            "unionid": "UNIONID"
        }
        with patch.object(
                WeChatOAuth, "fetch_access_token", return_value=data),\
            patch.object(
                WeChatOAuth, "get_user_info",
                return_value=userinfo_data.copy()):
            user = self.officialaccount.auth(code, scopes)
            WeChatOAuth.fetch_access_token.assert_called_once_with(code)
            self.assertFalse(user.created)
            self.assertEqual(user.app_id, self.officialaccount.id)
            self.assertEqual(user.openid, openid)
            self.assertEqual(user.access_token, access_token)
            self.assertEqual(user.refresh_token, refresh_token)
            self.assertEqual(user.unionid, userinfo_data.pop("unionid"))
            self.assertEqual(user.nickname, userinfo_data.pop("nickname"))
            self.assertEqual(user.avatar_url,
                             userinfo_data.pop("headimgurl"))
            self.assertEqual(user.ext_info, userinfo_data)

    def test_oauth_build_authorize_url(self, *args):
        """测试build_oauth_url"""
        host = "wechat.django"
        request = self.make_request(
            "GET", path="/", secure=True, HTTP_HOST=host)
        app = self.officialaccount

        # 采用默认scope与oauth_url
        default_proxy_page = request.build_absolute_uri(
            reverse("wechat_django:oauth_proxy",
                    kwargs={"app_name": app.name}))
        next = "/oauth2"
        url = app.build_oauth_url(request, next)
        parsed_url = urlparse(url)
        parsed_query = dict(parse_qsl(parsed_url.query))
        self.assertEqual(url.split("?")[0], app.DEFAULT_AUTHORIZE_URL)
        self.assertEqual(parsed_query["appid"], app.appid)
        redirect_uri = "{0}?{1}".format(
            default_proxy_page,
            urlencode({"redirect_uri": request.build_absolute_uri(next)}))
        self.assertEqual(parsed_query["redirect_uri"], redirect_uri)
        self.assertEqual(parsed_query["scope"], app.DEFAULT_SCOPES)
        self.assertFalse(parsed_query.get("state"))
        self.assertEqual(parsed_url.fragment, "wechat_redirect")

        # 测试有host
        next = "https://another.wechat.django/oauth"
        url = app.build_oauth_url(request, next)
        parsed_url = urlparse(url)
        parsed_query = dict(parse_qsl(parsed_url.query))
        self.assertEqual(url.split("?")[0], app.DEFAULT_AUTHORIZE_URL)
        self.assertEqual(parsed_query["appid"], app.appid)
        redirect_uri = "{0}?{1}".format(default_proxy_page,
                                        urlencode({"redirect_uri": next}))
        self.assertEqual(parsed_query["redirect_uri"], redirect_uri)
        self.assertEqual(parsed_query["scope"], app.DEFAULT_SCOPES)
        self.assertFalse(parsed_query.get("state"))
        self.assertEqual(parsed_url.fragment, "wechat_redirect")

        # 采用传入的值
        scope = WeChatOAuthScope.USERINFO
        state = "state"
        oauth_url = "/"
        url = app.build_oauth_url(request, next, scope=scope, state=state,
                                  oauth_url=oauth_url)
        parsed_url = urlparse(url)
        parsed_query = dict(parse_qsl(parsed_url.query))
        self.assertEqual(url.split("?")[0], app.DEFAULT_AUTHORIZE_URL)
        self.assertEqual(parsed_query["appid"], app.appid)
        redirect_uri = "{0}?{1}".format(request.build_absolute_uri(oauth_url),
                                        urlencode({"redirect_uri": next}))
        self.assertEqual(parsed_query["redirect_uri"], redirect_uri)
        self.assertEqual(parsed_query["scope"], scope)
        self.assertEqual(parsed_query["state"], state)
        self.assertEqual(parsed_url.fragment, "wechat_redirect")

        # 采用配置的oauth_url
        oauth_url = "http://baidu.com/oauth2"
        app.oauth_url = oauth_url
        url = app.build_oauth_url(request, next)
        parsed_url = urlparse(url)
        parsed_query = dict(parse_qsl(parsed_url.query))
        self.assertEqual(url.split("?")[0], app.DEFAULT_AUTHORIZE_URL)
        self.assertEqual(parsed_query["appid"], app.appid)
        redirect_uri = "{0}?{1}".format(oauth_url,
                                        urlencode({"redirect_uri": next}))
        self.assertEqual(parsed_query["redirect_uri"], redirect_uri)
        self.assertEqual(parsed_query["scope"], app.DEFAULT_SCOPES)
        self.assertFalse(parsed_query.get("state"))
        self.assertEqual(parsed_url.fragment, "wechat_redirect")

        # 测试配置的authorize_url
        del app.oauth_url
        app._authorize_url = oauth_url
        url = app.build_oauth_url(request, next)
        parsed_url = urlparse(url)
        parsed_query = dict(parse_qsl(parsed_url.query))
        self.assertEqual(url.split("?")[0], oauth_url)
        self.assertEqual(parsed_query["appid"], app.appid)
        redirect_uri = "{0}?{1}".format(
            default_proxy_page,
            urlencode({"redirect_uri": request.build_absolute_uri(next)}))
        self.assertEqual(parsed_query["redirect_uri"], redirect_uri)
        self.assertEqual(parsed_query["scope"], app.DEFAULT_SCOPES)
        self.assertFalse(parsed_query.get("state"))
        self.assertEqual(parsed_url.fragment, "wechat_redirect")
