# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from django.http.response import HttpResponse
from django.shortcuts import redirect
import six
from wechatpy import WeChatOAuthException

from wechat_django.constants import WeChatSNSScope
from wechat_django.rest_framework.views import APIView

from .mixins import WeChatOAuthViewMixin
from .permissions import WeChatAuthenticated


class WeChatOAuthView(WeChatOAuthViewMixin, APIView):

    required = True
    """真值必须授权 否则不授权亦可继续访问(只检查session)"""

    response = None
    """
    :type: django.http.response.HttpResponse or Callable[
        [
            django.http.request.HttpRequest,
            *args,
            **kwargs
        ],
        django.http.response.HttpResponse
    ]
    """

    permission_classes = tuple()

    @classmethod
    def prepare_init_kwargs(cls, **initKwargs):
        # 检查属性正确性
        appname = initKwargs.get("appname") or cls.appname
        assert appname and isinstance(appname, six.text_type),\
            "incorrect appname"

        response = initKwargs.get("response") or cls.response
        assert (
            response is None or callable(response)
            or isinstance(response, HttpResponse)
        ), "incorrect response param"

        scope = initKwargs.get("scope") or cls.scope
        if isinstance(scope, six.text_type):
            scope = (scope,)
        for s in scope:
            assert s in (WeChatSNSScope.BASE, WeChatSNSScope.USERINFO),\
                "incorrect scope"

        # 对于必须授权的请求 在permissions中添加WeChatAuthenticated
        required = initKwargs.get("required", cls.required)
        if required:
            base_permissions = getattr(cls, "permission_classes", tuple())
            if WeChatAuthenticated not in base_permissions:
                initKwargs["permission_classes"] = type(base_permissions)(
                    [WeChatAuthenticated] + list(base_permissions))

        return initKwargs

    @classmethod
    def as_view(cls, **initKwargs):
        initKwargs = cls.prepare_init_kwargs(**initKwargs)
        return super(WeChatOAuthView, cls).as_view(**initKwargs)

    def check_permissions(self, request):
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                if isinstance(permission, WeChatAuthenticated):
                    raise WeChatOAuthException(
                        0, getattr(permission, "message", None))
                else:
                    self.permission_denied(
                        request, message=getattr(permission, 'message', None)
                    )

    def handle_exception(self, exc):
        if isinstance(exc, WeChatOAuthException):
            return self.unauthorization_response(
                self.request, *self.args, **self.kwargs)

        return super(WeChatOAuthView, self).handle_exception(exc)

    def unauthorization_response(self, request, *args, **kwargs):
        """未授权的响应"""
        response = self.response
        if response and callable(response):
            response = response(request, *args, **kwargs)
        elif not response:
            oauth_uri = request.wechat.oauth_uri
            response = redirect(oauth_uri, permanent=False)
        return response


def wechat_auth(appname, scope=None, redirect_uri=None, required=True,
                response=None, state="", methods=None):
    """
    微信网页授权
    :param appname: WeChatApp的name
    :param scope: 默认WeChatSNSScope.BASE, 可选WeChatSNSScope.USERINFO
    :type scope: str or iterable
    :param redirect_uri: 未授权时的重定向地址 当未设置response时将自动执行授权
                        当ajax请求时默认取referrer 否则取当前地址
                        注意 请不要在地址上带有code及state参数 否则可能引发问题 
    :type redirect_uri: str or Callable[
        [
            django.http.request.HttpRequest,
            *args,
            **kwargs
        ],
        str
    ]
    :param state: 授权时需要携带的state
    :type state: str
                 or Callable[
                    [
                        django.http.request.HttpRequest,
                        *args,
                        **kwargs
                    ],
                    str
                 ]
    :param required: 真值必须授权 否则不授权亦可继续访问(只检查session)
    :param response: 未授权的返回 接受一个
    :type response: django.http.response.HttpResponse
                    or Callable[
                        [
                            django.http.request.HttpRequest,
                            *args,
                            **kwargs
                        ],
                        django.http.response.HttpResponse
                    ]
    :param methods: 允许的HTTP请求方法,默认仅GET
    :type methods: tuple

    使用示例:

        @wechat_auth("your_app_name")
        def your_view(request, *args, **kwargs):
            # request是一个``wechat_django.requests.WeChatOAuthRequest对象``
            user = request.wechat.user
    """

    methods = methods or ("GET",)

    def decorator(func):
        @wraps(func)
        def view(self, request, *args, **kwargs):
            return func(request, *args, **kwargs)

        View = type("WeChatOAuthView", (WeChatOAuthView,),
                    {method.lower(): view for method in methods})

        return View.as_view(appname=appname, scope=scope,
                            redirect_uri=redirect_uri, required=required,
                            response=response, state=state)
    return decorator
