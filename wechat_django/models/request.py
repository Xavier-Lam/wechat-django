# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http.request import HttpRequest
from wechatpy import parse_message
from wechatpy.crypto import WeChatCrypto

from . import WeChatApp, WeChatUser

class WeChatHttpRequest(HttpRequest):
    @property
    def wehcat(self):
        """wechat_django.models.WeChatInfo"""
        pass


class WeChatMessageRequest(HttpRequest):
    @property
    def wehcat(self):
        """wechat_django.models.WeChatMessageInfo"""
        pass


class WeChatOAuthRequest(HttpRequest):
    @property
    def wehcat(self):
        """wechat_django.models.WeChatOAuthInfo"""
        pass


class WeChatInfo(object):
    @classmethod
    def patch_request(cls, request, appname=None):
        """
        :type request: django.http.request.HttpRequest
        :rtype: cls
        """
        request.wechat = cls(
            _appname=appname or request.wechat._appname,
            _request=request
        )
        return request

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def app(self):
        """
        :rtype: wechat_django.models.WeChatApp
        """
        if not hasattr(self, "_app"):
            self._app = WeChatApp.get_by_name(self._appname)
        return self._app

    @property
    def user(self):
        """
        :rtype: wechat_django.models.WeChatUser
        """
        if not hasattr(self, "_user"):
            raise NotImplementedError()
        return self._user

    @property
    def request(self):
        """
        :rtype: django.http.request.HttpRequest
        """
        return self._request


class WeChatMessageInfo(WeChatInfo):
    """由微信接收到的消息"""
    @property
    def message(self):
        """
        :raises: xmltodict.expat.ExpatError
        :rtype: wechatpy.messages.BaseMessage
        """
        if not hasattr(self, "_message"):
            app = self.app
            request = self.request
            raw = self.raw
            if app.encoding_mode == WeChatApp.EncodingMode.SAFE:
                crypto = WeChatCrypto(
                    app.token,
                    app.encoding_aes_key,
                    app.appid
                )
                raw = crypto.decrypt_message(
                    self.raw,
                    request.GET["signature"],
                    request.GET["timestamp"],
                    request.GET["nonce"]
                )
            self._message = parse_message(raw)
        return self._message

    @property
    def user(self):
        """
        :rtype: wechat_django.models.WeChatUser
        """
        if not hasattr(self, "_user"):
            self._user = WeChatUser.get_by_openid(
                self.app, self.message.source)
        return self._user

    @property
    def raw(self):
        """原始消息
        :rtype: str
        """
        return self.request.body


class WeChatSNSScope(object):
    BASE = "snsapi_base"
    USERINFO = "snsapi_userinfo"


class WeChatOAuthInfo(WeChatInfo):
    """附带在request上的微信对象
    """
    @classmethod
    def patch_request(cls, request, redirect_uri, scope, state):
        """rtype: wechat_django.models.WeChatOAuthRequest"""
        rv = super(WeChatOAuthInfo, cls).patch_request(request, appname)
        rv._redirect_uri = redirect_uri
        rv._scope = scope
        rv._state = state
        return rv

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
    
    @property
    def openid(self):
        if not hasattr(self, "_openid"):
            self._openid = self.request.get_signed_cookie(
                self.session_key, None)
        return self._openid

    @property
    def user(self):
        if not hasattr(self, "_user"):
            self._user = WeChatUser.get_by_openid(self.openid)
        return super(WeChatOAuthInfo, self).user

    @property
    def session_key(self):
        return "wechat_{0}_user".format(self._appname)

    def __str__(self):
        return "WeChatOuathInfo: " + "\t".join(
            "{k}: {v}".format(k=attr, v=getattr(self, attr, None))
            for attr in
            ("app", "user", "redirect", "oauth_uri", "state", "scope")
        )
