from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from wechat_django.authentication import (
    OAuthCodeSessionAuthentication, OAuthSessionAuthentication)
from wechat_django.core.view import WeChatViewMixin
from wechat_django.rest_framework.exceptions import NotAuthenticated
from wechat_django.rest_framework.permissions import IsAuthenticated
from wechat_django.rest_framework.views import APIView


class WeChatOAuthViewMixin(WeChatViewMixin):
    wechat_app_name = None
    """The name of the WeChat application used for authorization"""

    oauth_required = True
    """If true, this view is accessible only when authorized"""

    scope = None
    """The OAuth2 scope parameter"""

    state = ""
    """The OAuth2 state parameter"""

    _redirect_uri = None

    @property
    def redirect_uri(self):
        """Redirect callback URL after authorization."""
        request = self.request
        return request.build_absolute_uri(
            # 优先取配置的
            self._redirect_uri
            # ajax page取referrer
            or (request.is_ajax() and request.META.get("HTTP_REFERER"))
            # 否则取当前地址
            or None)

    @redirect_uri.setter
    def redirect_uri(self, value):
        self._redirect_uri = value

    authentication_classes = (OAuthSessionAuthentication,)

    def __init__(self, **initKwargs):
        # 检查属性正确性
        app_name = initKwargs.pop("wechat_app_name", self.wechat_app_name)
        assert app_name and isinstance(app_name, str),\
            _("Incorrect wechat_app_name")
        initKwargs["wechat_app_name"] = app_name

        # 对于必须授权的请求 在permissions中添加WeChatAuthenticated
        required = initKwargs.pop("oauth_required", self.oauth_required)
        initKwargs["oauth_required"] = required

        # 重新处理permission_classes
        permission_classes = initKwargs.pop("permission_classes",
                                            self.permission_classes)
        if required and IsAuthenticated not in permission_classes:
            permission_classes = [IsAuthenticated] + list(permission_classes)
        initKwargs["permission_classes"] = tuple(permission_classes)

        super().__init__(**initKwargs)

    def wechat_authentication(self, request, redirect_uri=None, scope=None,
                              state=""):
        """
        Called when a WeChat webpage authorization is required, returns a
        :class:`~django.http.HttpResponse` to client.
        """
        redirect_uri = redirect_uri or self.redirect_uri
        scope = scope or self.scope
        state = state or self.state

        url = self.get_redirect_uri(request, redirect_uri, scope, state)
        return self.unauthorized_response(url, request)

    def get_redirect_uri(self, request, redirect_uri, scope, state):
        """
        Get the redirect uri parameter sent to WeChat, in most case, it
        returns the proxy page's url.
        """
        return request.wechat_app.build_oauth_url(
            request, next=redirect_uri, scope=scope, state=state)

    def unauthorized_response(self, url, request):
        """
        :return: The :class:`~django.http.HttpResponse` send to client when
                 user's authorization is needed
        """
        return HttpResponseRedirect(url)

    def handle_exception(self, exc):
        if isinstance(exc, NotAuthenticated):
            # 进行微信授权
            return self.wechat_authentication(self.request)
        return super().handle_exception(exc)

    def get_app_name(self, request, *args, **kwargs):
        return self.wechat_app_name


class WeChatOAuthView(WeChatOAuthViewMixin, APIView):
    """The basic view used for WeChat webpage authorization"""
    pass


def wechat_oauth(app_name, methods="GET", unauthorized_response=None,
                 bind=False, view_cls=None, **kwargs):
    """
    A decorator to make WeChat webpage authorization for non-class-based
    view

    :param app_name: The name of your WeChat application used for
                     authorization
    :param methods: Allowed HTTP methods, default GET only
    :param redirect_uri: The callback url after authorization
    :param scope: OAuth2 scope parameter
    :param state: OAuth2 state parameter
    :param oauth_required: If true, this view is accessible only if user has
                           authorized
    :param unauthorized_response: The response sent to client when the request
                                  is unauthorized
    :param bind: If true, the view instance will be passed into your view as
                 the first parameter

    Example::

        from wechat_django import wechat_oauth

        @wechat_oauth("your_app_name")
        def your_view(request, *args, **kwargs):
            user = request.user
            return response
    """

    if isinstance(methods, str):
        methods = (methods,)
    view_cls = view_cls or WeChatOAuthView

    def create_view(func):
        func = func if bind else staticmethod(func)
        initKwargs = {"wechat_app_name": app_name}
        attrs = {method.lower(): func for method in methods}
        if unauthorized_response is not None:
            attrs["unauthorized_response"] = unauthorized_response\
                if not isinstance(unauthorized_response, HttpResponse)\
                else lambda view, url, request: unauthorized_response
        for attr, value in kwargs.items():
            if callable(value):
                value = property(value)
            if isinstance(value, property):
                attrs[attr] = value
            else:
                initKwargs[attr] = value

        cls = type(view_cls.__name__, (view_cls,), attrs)
        return cls.as_view(**initKwargs)

    return create_view


def oauth_login(user, redirect_uri, scope, state, request):
    """
    Being used for login a WeChat user after authorization.
    """
    # 登录用户
    for authenticator in request.authenticators:
        if isinstance(authenticator, OAuthCodeSessionAuthentication):
            sk = authenticator.get_session_key(request.wechat_app)
            request.session[sk] = user.openid
            break
    else:
        raise NotAuthenticated

    return HttpResponseRedirect(redirect_uri)
