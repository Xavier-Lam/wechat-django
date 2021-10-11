from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from wechat_django.authentication import OAuthSessionAuthentication
from wechat_django.core.view import WeChatViewMixin
from wechat_django.rest_framework.exceptions import NotAuthenticated
from wechat_django.rest_framework.permissions import IsAuthenticated
from wechat_django.rest_framework.views import APIView


class WeChatOAuthViewMixin(WeChatViewMixin):
    wechat_app_name = None

    wechat_oauth_required = True
    """真值必须授权 否则不授权亦可继续访问(只检查session)"""

    scopes = None

    _redirect_uri = ""

    state = ""

    authentication_classes = (OAuthSessionAuthentication,)

    @property
    def redirect_uri(self):
        request = self.request
        return request.build_absolute_uri(
            # 优先已配置的redirect_uri
            self._redirect_uri
            # ajax page取referrer
            or (request.is_ajax() and request.META.get("HTTP_REFERER"))
            # 使用当前url
            or None
        )

    @redirect_uri.setter
    def redirect_uri(self, value):
        self._redirect_uri = value

    def wechat_authentication(self, request, redirect_uri=None, scopes=None,
                              state=""):
        """未进行OAuth授权响应"""
        # 默认进行重定向,如有其他需求请覆盖
        if not redirect_uri:
            if callable(self.redirect_uri):
                redirect_uri = self.redirect_uri(request)
            else:
                redirect_uri = self.redirect_uri

        if not state:
            if callable(self.state):
                state = self.state(request)
            else:
                state = self.state

        url = request.wechat_app.build_oauth_url(
            request,
            next=redirect_uri,
            scope=scopes or self.scopes,
            state=state
        )
        return self.unauthorized_response(url, request)

    def unauthorized_response(self, url, request):
        return HttpResponseRedirect(url)

    def handle_exception(self, exc):
        if isinstance(exc, NotAuthenticated):
            # 进行微信授权
            return self.wechat_authentication(self.request)
        return super().handle_exception(exc)

    def get_app_name(self, request, *args, **kwargs):
        return self.wechat_app_name

    @classmethod
    def as_view(cls, **initKwargs):
        # 检查属性正确性
        app_name = initKwargs.pop("wechat_app_name", cls.wechat_app_name)
        assert app_name and isinstance(app_name, str),\
            _("Incorrect wechat_app_name")
        initKwargs["wechat_app_name"] = app_name

        # 对于必须授权的请求 在permissions中添加WeChatAuthenticated
        required = initKwargs.pop("wechat_oauth_required",
                                  cls.wechat_oauth_required)
        initKwargs["wechat_oauth_required"] = required

        # 重新处理permission_classes
        permission_classes = initKwargs.pop("permission_classes",
                                            cls.permission_classes)
        if required and IsAuthenticated not in permission_classes:
            permission_classes = [IsAuthenticated] + list(permission_classes)
        initKwargs["permission_classes"] = tuple(permission_classes)

        return super().as_view(**initKwargs)


class WeChatOAuthView(WeChatOAuthViewMixin, APIView):
    pass


def wechat_oauth(app_name, scope=None, redirect_uri=None, required=True,
                 unauthorized_response=None, state="", methods=None,
                 bind=False):
    """
    微信网页授权
    :param app_name: WeChat应用名
    :param redirect_uri: 未授权时的重定向地址 当未设置response时将自动执行授权
                        当ajax请求时默认取referrer 否则取当前地址
                        注意 请不要在地址上带有code及state参数 否则可能引发问题
    :param state: 授权时需要携带的state
    :param required: 真值必须授权 否则不授权亦可继续访问(只检查session)
    :param unauthorized_response: 未授权的返回
    :param methods: 允许的HTTP请求方法,默认仅GET

    使用示例:
        @wechat_oauth("your_app_name")
        def your_view(request, *args, **kwargs):
            user = request.user
    """

    methods = methods or ("GET",)

    def decorator(func):
        kwargs = {
            "wechat_app_name": app_name,
            "scopes": scope,
            "wechat_oauth_required": required
        }
        if bind:
            attrs = {method.lower(): func for method in methods}
            View = type(str("WeChatOAuthView"), (WeChatOAuthView,), attrs)
            view = View.as_view(**kwargs)
        else:
            view = WeChatOAuthView.as_view(**kwargs)
            for method in methods:
                setattr(view, method.lower(), func)
        view.redirect_uri = redirect_uri
        view.state = state
        view.unauthorized_response = unauthorized_response
        return view
    return decorator
