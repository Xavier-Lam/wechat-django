# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from six import text_type
from wechatpy.crypto import WeChatCrypto

from .. import settings
from ..utils.admin import enum2choices
from . import MsgLogFlag


class Abilities(object):
    """微信号能力"""

    def __init__(self, app=None):
        self._app = app

    @property
    def interactable(self):
        """是否可与微信进行消息交互"""
        rv = self._app.token
        if self._app.encoding_mode == WeChatApp.EncodingMode.SAFE:
            rv = rv and self._app.encoding_aes_key
        return bool(rv)


class WeChatAppQuerySet(m.QuerySet):
    def get_by_name(self, name):
        return self.get(name=name)


class WeChatAppManager(m.Manager.from_queryset(WeChatAppQuerySet)):
    pass


class WeChatApp(m.Model):
    @staticmethod
    def __new__(cls, *args, **kwargs):
        self = super(WeChatApp, cls).__new__(cls)
        self.abilities = Abilities(self)
        return self

    class EncodingMode(object):
        PLAIN = 0
        # BOTH = 1
        SAFE = 2

    class Type(object):
        SERVICEAPP = 1
        SUBSCRIBEAPP = 2
        MINIPROGRAM = 3

    title = m.CharField(
        _("title"), max_length=16, null=False,
        help_text=_("公众号名称,用于后台辨识公众号"))
    name = m.CharField(
        _("name"), max_length=16, blank=False, null=False, unique=True,
        help_text=_("公众号唯一标识,可采用微信号,设定后不可修改,用于程序辨识"))
    desc = m.TextField(_("description"), default="", blank=True)

    appid = m.CharField(_("AppId"), max_length=32, null=False)
    appsecret = m.CharField(_("AppSecret"), max_length=64, blank=True, null=True)
    type = m.PositiveSmallIntegerField(_("type"), default=Type.SERVICEAPP,
        choices=enum2choices(Type))

    token = m.CharField(max_length=32, null=True, blank=True)
    encoding_aes_key = m.CharField(
        _("EncodingAESKey"), max_length=43, null=True, blank=True)
    encoding_mode = m.PositiveSmallIntegerField(
        _("encoding mode"), default=EncodingMode.PLAIN,
        choices=enum2choices(EncodingMode))

    flags = m.IntegerField(_("flags"), default=0)

    ext_info = JSONField(db_column="ext_info", default={})
    configurations = JSONField(db_column="configurations", default={})

    created_at = m.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated at"), auto_now=True)

    objects = WeChatAppManager()

    abilities = Abilities()

    class Meta(object):
        verbose_name = _("WeChat app")
        verbose_name_plural = _("WeChat apps")

    @property
    def log_message(self):
        return bool(self.flags & MsgLogFlag.LOG_MESSAGE)

    @property
    def log_reply(self):
        return bool(self.flags & MsgLogFlag.LOG_REPLY)

    @property
    def client(self):
        """:rtype: wechatpy.WeChatClient"""
        if not hasattr(self, "_client"):
            # session
            if isinstance(settings.SESSIONSTORAGE, text_type):
                settings.SESSIONSTORAGE = import_string(settings.SESSIONSTORAGE)
            if callable(settings.SESSIONSTORAGE):
                session = settings.SESSIONSTORAGE(self)
            else:
                session = settings.SESSIONSTORAGE

            client_factory = import_string(settings.WECHATCLIENTFACTORY)
            self._client = client = client_factory(self)(
                self.appid,
                self.appsecret,
                session=session
            )
            client.appname = self.name
            # API BASE URL
            # client.ACCESSTOKEN_URL = self.configurations.get("ACCESSTOKEN_URL")

        return self._client

    @property
    def oauth(self):
        if not hasattr(self, "_oauth"):
            from ..patches import WeChatOAuth
            self._oauth = WeChatOAuth(self.appid, self.appsecret)

            if self.configurations.get("OAUTH_URL"):
                self._oauth.OAUTH_URL = self.configurations["OAUTH_URL"]

        return self._oauth

    @property
    def crypto(self):
        if not hasattr(self, "_crypto"):
            self._crypto = (self.encoding_mode == self.EncodingMode.SAFE
                and self.abilities.interactable
                and WeChatCrypto(
                    self.token,
                    self.encoding_aes_key,
                    self.appid
                )) or None
        return self._crypto

    def __str__(self):
        return "{title} ({name})".format(title=self.title, name=self.name)
