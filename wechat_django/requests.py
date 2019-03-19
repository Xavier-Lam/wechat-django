# -*- coding: utf-8 -*-

"""
微信相关的请求类声明,这些请求类中,包含一个WeChatInfo对象wechat
实际上这些请求类没有真正被使用
但是可以通过docstring声明传参是这些请求类,让你的IDE更加智能地提示代码
"""

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
