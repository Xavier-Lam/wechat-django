from unittest.mock import patch

from django.http.response import HttpResponse

from wechat_django.enums import WeChatOAuthScope

from wechat_django.oauth import WeChatOAuthView, wechat_oauth
from wechat_django.rest_framework.exceptions import NotAuthenticated
from ..base import TestOnlyException, WeChatDjangoTestCase


def dummy_view(*args, **kwargs):
    pass


class OAuthTestCase(WeChatDjangoTestCase):
    def test_view_creation(self):
        """测试创建View"""
        app = self.officialaccount
        path = "/path"
        scope = (WeChatOAuthScope.USERINFO,)
        state = "state"
        request = self.make_request(path=path)

        # 必须授权的view
        view = WeChatOAuthView(
            wechat_app_name=app.name,
            scope=scope,
            state=state
        )
        request = view.initialize_request(request)
        view.request = request
        self.assertRaises(NotAuthenticated, view.initial, request)

        # 非必须授权的
        request = self.make_request(path=path)
        view = WeChatOAuthView(
            wechat_app_name=app.name,
            oauth_required=False,
            scope=scope,
            state=state
        )
        request = view.initialize_request(request)
        view.request = request
        view.initial(request)

        self.assertTrue(not request.user or request.user.is_anonymous)
        self.assertEqual(view.redirect_uri, request.build_absolute_uri(path))
        redirect_uri = view.get_redirect_uri(request, view.redirect_uri,
                                             scope, state)
        self.assertEqual(redirect_uri,
                         app.build_oauth_url(request, view.redirect_uri,
                                             scope, state))
        response = view.unauthorized_response(redirect_uri, request)
        self.assertEqual(response.url, redirect_uri)
        self.assertEqual(view.wechat_authentication(request).url,
                         redirect_uri)
        with patch.object(view, "get_redirect_uri",
                          return_value=redirect_uri) as f:
            view.wechat_authentication(request)
            f.assert_called_once_with(request, view.redirect_uri, view.scope,
                                      view.state)

    def test_decorator(self):
        """测试wechat_oauth装饰器"""

        def with_dummy_view(**kwargs):
            view_name = "{0}.{1}".format(
                dummy_view.__module__, dummy_view.__name__)
            return patch(view_name, **kwargs)

        app = self.officialaccount
        redirect_uri = "/redirect"
        scope = WeChatOAuthScope.USERINFO
        state = "state"
        request_id = "request_id"
        request = self.make_request()
        request.id = request_id
        response = HttpResponse()

        # 测试一般参数设置
        initKwargs = {
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "oauth_required": False
        }

        def assert_call(request):
            self.assertEqual(request.id, request_id)
            return response

        with with_dummy_view(side_effect=assert_call):
            view = wechat_oauth(app.name, methods=("GET", "POST"),
                                **initKwargs)(dummy_view)
            self.assertTrue(hasattr(view.view_class, "get"))
            self.assertTrue(hasattr(view.view_class, "post"))
            self.assertFalse(hasattr(view.view_class, "put"))
            self.assertEqual(view.view_initkwargs["redirect_uri"],
                             redirect_uri)
            self.assertEqual(view.view_initkwargs["scope"], scope)
            self.assertEqual(view.view_initkwargs["state"], state)
            self.assertFalse(view.view_initkwargs["oauth_required"])
            resp = view(request)
            dummy_view.assert_called_once()
            self.assertIs(resp, response)

        # 测试传入function
        initKwargs = {
            "redirect_uri": lambda view: redirect_uri,
            "scope": lambda view: scope,
            "state": lambda view: state,
            "oauth_required": False,
            "unauthorized_response": lambda view, url, request: ""
        }

        with with_dummy_view(side_effect=assert_call):
            view = wechat_oauth(app.name, methods=("GET", "POST"),
                                **initKwargs)(dummy_view)
            self.assertTrue(hasattr(view.view_class, "get"))
            self.assertTrue(hasattr(view.view_class, "post"))
            self.assertFalse(hasattr(view.view_class, "put"))
            view_obj = view.view_class(**view.view_initkwargs)
            self.assertEqual(view_obj.redirect_uri, redirect_uri)
            self.assertEqual(view_obj.scope, scope)
            self.assertEqual(view_obj.state, state)
            self.assertFalse(view_obj.oauth_required)
            self.assertIs(
                view_obj.unauthorized_response("", request), "")
            resp = view(request)
            dummy_view.assert_called_once()
            self.assertIs(resp, response)

        # 测试未绑定
        def unbound_view(request):
            self.assertEqual(request.id, request_id)
            raise TestOnlyException

        view = wechat_oauth(app.name, methods=("GET",), oauth_required=False)(
            unbound_view)
        self.assertRaises(TestOnlyException, view, request)

        # 测试绑定
        def bound_view(view, request):
            self.assertEqual(view.state, state)
            self.assertEqual(request.id, request_id)
            raise TestOnlyException

        view = wechat_oauth(app.name, methods=("GET",), state=state,
                            bind=True, oauth_required=False)(bound_view)
        self.assertRaises(TestOnlyException, view, request)
