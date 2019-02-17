# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.http.response import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect
from django.views import View
from six.moves.urllib.parse import parse_qsl, urlparse
from wechatpy import WeChatOAuthException

from .models import WeChatApp, WeChatOAuthInfo, WeChatSNSScope, WeChatUser

__all__ = ("wechat_auth", "WeChatOAuthHandler", "WeChatSNSScope")


class wechat_auth(object):
    def __init__(
        self, appname, scope=None, redirect_uri=None, required=True,
        response=None, state=""
    ):
        """微信网页授权
        :param appname: WeChatApp的name
        :param scope: 默认WeChatSNSScope.BASE, 可选WeChatSNSScope.USERINFO
        :param redirect_uri: 未授权时的重定向地址 当未设置response时将自动执行授权
                            当ajax请求时默认取referrer 否则取当前地址
                            注意 请不要在地址上带有code及state参数 否则可能引发问题
        :param state: 授权时需要携带的state
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
        scope = scope or WeChatSNSScope.BASE
        assert (
            response is None or callable(response)
            or isinstance(response, HttpResponse)
        ), "incorrect response"
        assert scope in (WeChatSNSScope.BASE, WeChatSNSScope.USERINFO), \
            "incorrect scope"

        self.appname = appname
        self.scope = scope
        self._redirect_uri = redirect_uri
        self.required = required
        self._response = response
        self.state = state  # TODO: 改为可接受lambda

    def redirect_uri(self, request):
        return (
            self._redirect_uri
            or (request.is_ajax() and request.META.get("HTTP_REFERER"))
            or request.build_absolute_uri()
        )

    def __call__(self, view):
        return WeChatOAuthHandler(self, view).as_view()


class WeChatOAuthHandler(View):
    def __init__(self, oauth_info, view):
        """
        :type oauth_info: wechat_django.oauth.wechat_auth
        """
        self.oauth_info = oauth_info
        self.get = view

    @property
    def code(self):
        if not hasattr(self, "_code"):
            request = self.request
            if request.is_ajax():
                try:
                    referrer = request.META["HTTP_REFERER"]
                    query = dict(parse_qsl(urlparse(referrer).query))
                    self._code = query.get("code")
                except:
                    self._code = None
            else:
                self._code = request.GET.get("code")
        return self._code

    def auth(self):
        # 检查code有效性
        app = self.request.wechat.app
        data = app.oauth.fetch_access_token(self.code)

        if self.oauth_info.scope == WeChatSNSScope.USERINFO:
            # 同步数据
            try:
                user_info = app.oauth.get_user_info()
                data.update(user_info)
            except WeChatOAuthException:
                self.logger.warning("get userinfo failed", exc_info=True)

        return data

    def unauthorization_response(self, *args, **kwargs):
        """未授权的响应"""
        response = self.oauth_info.response
        if response and callable(response):
            response = response(self.request, *args, **kwargs)
        elif not response:
            # TODO: 检查是否需要permanent = True
            oauth_uri = self.request.wechat.oauth_uri
            response = redirect(oauth_uri, permanent=True)
        return response

    def dispatch(self, request, *args, **kwargs):
        try:
            return self._dispatch(request, *args, **kwargs)
        except WeChatApp.DoesNotExist:
            return HttpResponseNotFound()

    def _dispatch(self, request, *args, **kwargs):
        self.request = WeChatOAuthInfo.patch_request(
            request=request,
            appname=self.oauth_info.appname,
            redirect_uri=self.oauth_info.redirect_uri(request),
            scope=self.oauth_info.scope,
            state=self.oauth_info.state
        )
        wechat = self.request.wechat

        if not wechat.openid and self.code:
            # 有code 先授权
            try:
                user_dict = self.auth()
                # 更新user_dict
                WeChatUser.upsert_by_oauth(wechat.app, user_dict)
                wechat._openid = user_dict["openid"]
                # 用当前url的state替换传入的state
                wechat._state = request.GET.get("state", "")
            except WeChatOAuthException:
                self.logger.warning("auth code failed: {0}".format(dict(
                    info=wechat,
                    code=self.code
                )), exc_info=True)
            except AssertionError:
                self.logger.error("incorrect auth response: {0}".format(dict(
                    info=wechat,
                    user_dict=user_dict
                )), exc_info=True)

        # 没有openid 响应未授权
        if self.oauth_info.required and not wechat.openid:
            return self.unauthorization_response(request, *args, **kwargs)

        response = super(WeChatOAuthHandler, self).dispatch(
            request, *args, **kwargs)
        wechat.openid and response.set_signed_cookie(
            wechat.session_key, wechat.openid)
        return response

    @property
    def logger(self):
        appname = self.oauth_info.appname
        return logging.getLogger("wechat:oauth:{0}".format(appname))
