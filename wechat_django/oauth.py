# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.http.response import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect
from django.views import View
import six
from wechatpy import WeChatOAuthException

from .models import WeChatApp, WeChatOAuthInfo, WeChatSNSScope, WeChatUser
from .utils.web import auto_response, get_params

__all__ = ("wechat_auth", "WeChatOAuthView", "WeChatSNSScope")


class wechat_auth(object):
    def __init__(
        self, appname, scope=None, redirect_uri=None, required=True,
        response=None, state=""
    ):
        """微信网页授权
        :param appname: WeChatApp的name
        :param scope: 默认WeChatSNSScope.BASE, 可选WeChatSNSScope.USERINFO
        :type scope: str or iterable
        :param redirect_uri: 未授权时的重定向地址 当未设置response时将自动执行授权
                            当ajax请求时默认取referrer 否则取当前地址
                            注意 请不要在地址上带有code及state参数 否则可能引发问题
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
        """
        scope = scope or (WeChatSNSScope.BASE,)
        if isinstance(scope, six.text_type):
            scope = (scope,)

        assert appname and isinstance(appname, six.text_type),\
            "incorrect appname"
        assert (
            response is None or callable(response)
            or isinstance(response, HttpResponse)
        ), "incorrect response param"
        for s in scope:
            assert s in (WeChatSNSScope.BASE, WeChatSNSScope.USERINFO),\
                "incorrect scope"

        self.appname = appname
        self.scope = scope
        self._redirect_uri = redirect_uri
        self.required = required
        self.response = response
        self.state = state

    def redirect_uri(self, request):
        return request.build_absolute_uri(
            self._redirect_uri
            or (request.is_ajax() and request.META.get("HTTP_REFERER"))
            or request.build_absolute_uri()
        )

    def __call__(self, view):
        return WeChatOAuthView(self, view)

    def __str__(self):
        return "<wechat_auth appname: {appname} scope: {scope}>".format(
            appname=self.appname,
            scope=self.scope
        )


class WeChatOAuthView(View):
    @property
    def oauth_info(self):
        """:rtype: wechat_django.oauth.wechat_auth"""
        if not self._oauth_info:
            self._oauth_info = wechat_auth(
                self.appname, scope=self.scope, state=self.state,
                redirect_uri=self.redirect_uri, required=self.required,
                response=self.response)
        return self._oauth_info

    #region class based view properties
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
    #endregion


    def __init__(self, oauth_info=None, view=None, **kwargs):
        """
        :type oauth_info: wechat_django.oauth.wechat_auth
        """
        self._oauth_info = oauth_info
        if view:
            self.get = view
        super(WeChatOAuthView, self).__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self._patch_request(request)
        try:
            return self._dispatch(request, *args, **kwargs)
        except WeChatApp.DoesNotExist:
            return HttpResponseNotFound()

    def _dispatch(self, request, *args, **kwargs):
        wechat = request.wechat

        code = get_params(self.request, "code")
        if not wechat.openid and code:
            # 有code 先授权
            try:
                user_dict = self.auth()
                # 更新user_dict
                WeChatUser.upsert_by_oauth(wechat.app, user_dict)
                wechat._openid = user_dict["openid"]
                # 用当前url的state替换传入的state
                wechat._state = get_params(request, "state", "")
            except WeChatOAuthException:
                self.logger.warning("auth code failed: {0}".format(dict(
                    info=wechat,
                    code=code
                )), exc_info=True)
            except AssertionError:
                self.logger.error("incorrect auth response: {0}".format(dict(
                    info=wechat,
                    user_dict=user_dict
                )), exc_info=True)

        # 没有openid 响应未授权
        if self.oauth_info.required and not wechat.openid:
            return self.unauthorization_response(request, *args, **kwargs)

        response = super(WeChatOAuthView, self).dispatch(
            request, *args, **kwargs)
        response = auto_response(response)
        wechat.openid and response.set_signed_cookie(
            wechat.session_key, wechat.openid)
        return response

    def auth(self):
        """执行微信授权 返回微信接口响应的json数据
        :rtype: dict
        """
        # 检查code有效性
        app = self.request.wechat.app
        code = get_params(self.request, "code")
        data = app.oauth.fetch_access_token(code)

        if WeChatSNSScope.USERINFO in self.oauth_info.scope:
            # TODO: 优化授权流程 记录accesstoken及refreshtoken 延迟取userinfo
            # 同步数据
            try:
                user_info = app.oauth.get_user_info()
                data.update(user_info)
            except WeChatOAuthException:
                self.logger.warning("get userinfo failed", exc_info=True)

        return data

    def unauthorization_response(self, request, *args, **kwargs):
        """未授权的响应"""
        response = self.oauth_info.response
        if response and callable(response):
            response = response(request, *args, **kwargs)
        elif not response:
            oauth_uri = request.wechat.oauth_uri
            response = redirect(oauth_uri, permanent=False)
        return response

    @property
    def logger(self):
        appname = self.oauth_info.appname
        return logging.getLogger("wechat:oauth:{0}".format(appname))

    def _patch_request(self, request, *args, **kwargs):
        info = self.oauth_info
        state = info.state(request, *args, **kwargs) if callable(info.state)\
            else info.state
        self.request = WeChatOAuthInfo.patch_request(
            request=request,
            appname=info.appname,
            redirect_uri=info.redirect_uri(request),
            scope=info.scope,
            state=state
        )
        self.args = args
        self.kwargs = kwargs

    __call__ = dispatch
