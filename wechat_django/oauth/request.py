# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six.moves.urllib.parse import urlparse

from wechat_django.constants import WeChatSNSScope
from wechat_django.sites.wechat import WeChatInfo


class WeChatOAuthInfo(WeChatInfo):
    """附带在request上的微信对象
    """

    @property
    def scope(self):
        """授权的scope
        :rtype: tuple
        """
        if not getattr(self, "_scope", None):
            self._scope = (WeChatSNSScope.BASE,)
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
            ",".join(self.scope),
            self.state
        )

    _redirect_uri = None

    @property
    def redirect_uri(self):
        """授权后重定向回的地址"""
        # 绝对路径
        if self._redirect_uri and urlparse(self._redirect_uri).netloc:
            return self._redirect_uri

        request = self.request
        return request.build_absolute_uri(
            self._redirect_uri
            or (request.is_ajax() and request.META.get("HTTP_REFERER"))
            or None
        )

    @redirect_uri.setter
    def redirect_uri(self, value):
        self._redirect_uri = value

    @property
    def openid(self):
        if not hasattr(self, "_openid"):
            self._openid = self.request.session.get(self.session_key)
        return self._openid

    @property
    def session_key(self):
        return "wechat_{0}_user".format(self.appname)

    def __str__(self):
        return "WeChatOuathInfo: " + "\t".join(
            "{k}: {v}".format(k=attr, v=getattr(self, attr, None))
            for attr in
            ("app", "user", "redirect", "oauth_uri", "state", "scope")
        )
