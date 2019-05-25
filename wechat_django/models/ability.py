# -*- coding: utf-8 -*-

"""公众号能力"""

from __future__ import unicode_literals

from functools import wraps

from .constants import AppType


def ability(func):
    @wraps(func)
    def decorated_func(self):
        return bool(func(self))
    return property(decorated_func)


def apptypes(*args, **kwargs):
    def decorator(func):
        @wraps(func)
        def decorated_func(self):
            if kwargs:
                rv = self.app.type not in kwargs["excludes"]
            else:
                rv = self.app.type in args
            return rv and func(self)
        return decorated_func
    return decorator


class Abilities(object):
    """微信号能力"""

    def __init__(self, app=None):
        """:type app: wechat_django.models.self.app"""
        self._app = app

    @ability
    def authed(self):
        """已认证"""
        return self.app.Flag.UNAUTH ^ (self.app.flags & self.app.Flag.UNAUTH)

    @ability
    def api(self):
        """是否可调用微信api(可换取accesstoken)"""
        return self.app.appsecret

    @ability
    def interactable(self):
        """是否可与微信进行消息交互"""
        rv = self.app.token
        if self.app.encoding_mode == self.app.EncodingMode.SAFE:
            rv = rv and self.app.encoding_aes_key
        return rv

    @ability
    @apptypes(AppType.SERVICEAPP)
    def oauth(self):
        """是否可进行网页授权"""
        return self.authed and self.api

    @ability
    @apptypes(AppType.SERVICEAPP, AppType.SUBSCRIBEAPP)
    def menus(self):
        """是否可配置菜单"""
        return self.authed and self.api

    @ability
    @apptypes(AppType.SERVICEAPP, AppType.MINIPROGRAM)
    def template(self):
        """发送模板消息"""
        return self.authed and self.api

    @ability
    @apptypes(AppType.SUBSCRIBEAPP, AppType.SERVICEAPP)
    def user_manager(self):
        """管理用户能力"""
        return self.authed and self.api

    @ability
    @apptypes(AppType.SUBSCRIBEAPP, AppType.SERVICEAPP)
    def material(self):
        """管理用户能力"""
        return self.api

    @ability
    @apptypes(excludes=(AppType.SUBSCRIBEAPP,))
    def pay(self):
        """微信支付能力"""
        return self.authed and self.app.pay

    @property
    def app(self):
        return self._app
