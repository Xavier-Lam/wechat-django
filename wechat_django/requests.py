# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http.request import HttpRequest


class WeChatHttpRequest(HttpRequest):
    @property
    def wechat(self):
        """:rtype: wechat_django.models.WeChatInfo"""
        pass


class WeChatMessageRequest(HttpRequest):
    @property
    def wechat(self):
        """:rtype: wechat_django.models.WeChatMessageInfo"""
        pass


class WeChatOAuthRequest(HttpRequest):
    @property
    def wechat(self):
        """:rtype: wechat_django.models.WeChatOAuthInfo"""
        pass
