# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps
import logging

from django.http.response import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect
from six.moves.urllib.parse import parse_qsl, urlparse
from wechatpy import WeChatOAuth, WeChatOAuthException

from .models import WeChatApp, WeChatRequest, WeChatUser

__all__ = ("wechat_auth", "WeChatSNSScope")


class WeChatSNSScope(object):
    BASE = "snsapi_base"
    USERINFO = "snsapi_userinfo"


class WeChatOAuthInfo(WeChatRequest):
    """附带在request上的微信对象
    """
    _scope = WeChatSNSScope.BASE
    @property
    def scope(self):
        """授权的scope"""
        return self._scope
    
    _state = ""
    @property
    def state(self):
        """授权携带的state"""
        return self._state

    @property
    def oauth_uri(self):
        return self.app.oauth.authorize_url(
            self.redirect_uri,
            self.scope,
            self.state
        )
    
    _redirect_uri = None
    @property
    def redirect_uri(self):
        """授权后重定向回的地址"""
        return self._redirect_uri

    _oauth_uri = None
    @property
    def oauth_uri(self):
        """授权地址"""
        return self._oauth_uri

    def __setattr__(self, k, v):
        if k.startswith("_"):
            self.__dict__[k] = v
        else:
            setattr(self, "_" + k, v)

    def __str__(self):
        return "WeChatOuathInfo: " + "\t".join(
            "{k}: {v}".format(k=attr, v=getattr(self, attr, None))
            for attr in
            ("app", "user", "redirect", "oauth_uri", "state", "scope")
        )


def wechat_auth(appname, scope=WeChatSNSScope.BASE, redirect_uri=None,
    required=True, response=None, state=""):
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
    assert (response is None or callable(response)
        or isinstance(response, HttpResponse)), "incorrect response"
    assert scope in (WeChatSNSScope.BASE, WeChatSNSScope.USERINFO), \
        "incorrect scope"
    logger = _logger(appname)

    def decorator(func):
        @wraps(func)
        def decorated_func(request, *args, **kwargs):
            """:type request: django.http.request.HttpRequest"""
            # 优先检查session
            session_key = "wechat_{0}_user".format(appname)
            openid = request.get_signed_cookie(session_key, None)

            # 未设置redirect_uri ajax取referrer 否则取当前地址
            if redirect_uri:
                redirect_url = redirect_uri
            else:
                full_url = request.build_absolute_uri()
                redirect_url = ((request.META.get("HTTP_REFERER") or full_url)
                    if request.is_ajax() else full_url)

            try:
                app = WeChatApp.get_by_name(appname)
            except WeChatApp.DoesNotExist:
                logger.warning("wechat app not exists: {0}".format(appname))
                return HttpResponseNotFound()
            request.wechat = wechat = WeChatOAuthInfo(
                app=app, redirect_uri=redirect_url, state=state, scope=scope)

            if required and not openid:
                # 设定了response优先返回response
                if response:
                    if callable(response):
                        return response(request, *args, **kwargs)
                    return response

                code = get_request_code(request)
                # 根据code获取用户信息
                if code:
                    try:
                        user_dict = auth_by_code(app, code, scope)
                        # 更新user_dict
                        WeChatUser.upsert_by_oauth(app, user_dict)
                        openid = user_dict["openid"]
                    except WeChatOAuthException:
                        logger.warning("auth code failed: {0}".format(dict(
                            info=wechat,
                            code=code
                        )), exc_info=True)
                    except AssertionError:
                        logger.error("incorrect auth response: {0}".format(dict(
                            info=wechat,
                            user_dict=user_dict
                        )), exc_info=True)
                    else:
                        # 用当前url的state替换传入的state
                        wechat.state = request.GET.get("state", "")

                if required and not openid:
                    # 最后执行重定向授权
                    return redirect(wechat.oauth_uri, permanent=True)

            if openid:
                wechat.user = WeChatUser.get_by_openid(app, openid)

            rv = func(request, *args, **kwargs)
            openid and rv.set_signed_cookie(session_key, openid)
            return rv

        return decorated_func
    return decorator


def get_request_code(request):
    if request.is_ajax():
        try:
            referrer = request.META["HTTP_REFERER"]
            query = dict(parse_qsl(urlparse(referrer).query))
            code = query.get("code")
        except:
            code = None
    else:
        code = request.GET.get("code")
    return code


def auth_by_code(app, code, scope):
    # 检查code有效性
    data = app.oauth.fetch_access_token(code)

    if scope == WeChatSNSScope.USERINFO:
        # 同步数据
        try:
            user_info = app.oauth.get_user_info()
            data.update(user_info)
        except WeChatOAuthException:
            _logger(app.name).warning("get userinfo failed", exc_info=True)

    return data


def _logger(appname):
    return logging.getLogger("wechat:oauth:{0}".format(appname))
