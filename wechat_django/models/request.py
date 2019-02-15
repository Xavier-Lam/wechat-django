# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechatpy import parse_message
from wechatpy.crypto import WeChatCrypto

from . import WeChatApp, WeChatUser

class WeChatRequest(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    _app = None
    @property
    def app(self):
        """
        :rtype: wechat_django.models.WeChatApp
        """
        return self._app

    _user = None
    @property
    def user(self):
        """
        :rtype: wechat_django.models.WeChatUser
        """
        return self._user


class WeChatMessage(WeChatRequest):
    """由微信接收到的消息"""
    @classmethod
    def from_request(cls, request, app):
        rv = cls(_app=app, _request=request)
        request.wechat = rv
        return rv

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

    @property
    def request(self):
        """
        :rtype: django.http.request.HttpRequest
        """
        return self._request
