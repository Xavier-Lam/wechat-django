# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechat_django.constants import WeChatSNSScope
from wechat_django.utils.web import auto_response

from .authentication import WeChatOAuthSessionAuthentication


class WeChatOAuthViewMixin(object):

    appname = None
    """
    微信appname 必填
    """

    scope = (WeChatSNSScope.BASE,)
    """
    :type: str or iterable
    微信授权的scope 默认WeChatSNSScope.BASE
    """

    redirect_uri = None
    """
    :type: str or Callable[
        [
            django.http.request.HttpRequest,
            *args,
            **kwargs
        ],
        str
    ]

    未授权时的重定向地址 当未设置response时将自动执行授权
    当ajax请求时默认取referrer 否则取当前地址
    注意 请不要在地址上带有code及state参数 否则可能引发问题
    """

    state = ""
    """
    :type: str or Callable[
        [
            django.http.request.HttpRequest,
            *args,
            **kwargs
        ],
        str
    ]

    授权时需要携带的state
    """

    authentication_classes = (WeChatOAuthSessionAuthentication,)

    def initialize_request(self, request, *args, **kwargs):
        request = super(WeChatOAuthViewMixin, self).initialize_request(
            request, *args, **kwargs)
        return self._initialize_wechat_request(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        response = auto_response(response)
        response = super(WeChatOAuthViewMixin, self).finalize_response(
            request, response, *args, **kwargs)
        return response

    def _initialize_wechat_request(self, request, *args, **kwargs):
        from wechat_django.models import WeChatOAuthInfo
        from wechat_django.sites.wechat import patch_request

        state = self.state(request, *args, **kwargs) if callable(self.state)\
            else self.state
        redirect_uri = self.redirect_uri(request, *args, **kwargs)\
            if callable(self.redirect_uri)\
            else self.redirect_uri
        return patch_request(
            request=request,
            appname=self.appname,
            cls=WeChatOAuthInfo,
            redirect_uri=redirect_uri,
            scope=self.scope,
            state=state
        )
