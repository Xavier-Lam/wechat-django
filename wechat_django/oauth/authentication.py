# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from rest_framework.authentication import BaseAuthentication
except ImportError:
    BaseAuthentication = object
from six.moves.urllib.parse import parse_qsl, urlparse
from wechatpy import WeChatOAuthException


class WeChatOAuthAuthentication(BaseAuthentication):
    """
    兼容drf的网页授权认证,仅可通过code授权
    """
    def authenticate(self, request):
        wechat = request.wechat
        code = self._get_code(request)
        if wechat.openid:
            return wechat.user, wechat.openid
        elif code:
            try:
                user = self._auth(wechat.app, code, wechat.scope)
                wechat._openid = user.openid
                wechat._user = user
                # 用当前url的state替换传入的state
                wechat._state = self._get_state(request)
                return wechat.user, wechat.openid
            except WeChatOAuthException:
                err_msg = "auth code failed: {0}".format(dict(
                    info=wechat,
                    code=code
                ))
                wechat.app.logger("oauth").warning(err_msg, exc_info=True)

    def authenticate_header(self, request):
        return 'WOAuth realm="{0}"'.format(request.wechat.app.appid)

    def _get_code(self, request):
        return self._get_params(request, "code")

    def _get_state(self, request):
        return self._get_params(request, "state", "")

    def _auth(self, app, code, scope):
        return app.auth(code, scope)[0]

    def _get_params(self, request, key, default=None):
        """获取url上的参数"""
        if request.is_ajax():
            try:
                referrer = request.META["HTTP_REFERER"]
                query = dict(parse_qsl(urlparse(referrer).query))
                return query.get(key, default)
            except:
                return default
        else:
            return request.GET.get(key, default)


class WeChatOAuthSessionAuthentication(WeChatOAuthAuthentication):
    """
    兼容drf的网页授权认证,包含session设置,一般使用该认证
    """

    def authenticate(self, request):
        session_key = request.wechat.session_key
        request.wechat._openid = request.session.get(session_key)
        rv = super(WeChatOAuthSessionAuthentication, self).authenticate(
            request)
        if rv is not None:
            request.session[session_key] = rv[1]
        return rv
