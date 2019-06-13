# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import models as m
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
import six
from wechatpy.crypto import WeChatCrypto
from wechatpy.constants import WeChatErrorCode
from wechatpy.exceptions import WeChatClientException

from .. import settings
from ..exceptions import WeChatAbilityError
from ..utils.model import enum2choices
from . import MsgLogFlag
from .ability import Abilities
from ..constants import AppType


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

    class Flag(object):
        UNAUTH = 0x01 # 未认证

    Type = AppType # TODO: deprecated

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

    @cached_property
    def pay(self):
        return self.pays.first()

    class Meta(object):
        verbose_name = _("WeChat app")
        verbose_name_plural = _("WeChat apps")

    @property
    def site_https(self):
        return self.configurations.get("SITE_HTTPS", settings.SITE_HTTPS)

    @property
    def site_host(self):
        return self.configurations.get("SITE_HOST", settings.SITE_HOST)

    @property
    def type_name(self):
        if self.type == WeChatApp.Type.MINIPROGRAM:
            return _("MINIPROGRAM")
        elif self.type == WeChatApp.Type.SERVICEAPP:
            return _("SERVICEAPP")
        elif self.type == WeChatApp.Type.SUBSCRIBEAPP:
            return _("SUBSCRIBEAPP")
        else:
            return _("unknown")

    @property
    def log_message(self):
        return bool(self.flags & MsgLogFlag.LOG_MESSAGE)

    @property
    def log_reply(self):
        return bool(self.flags & MsgLogFlag.LOG_REPLY)

    @property
    def client(self):
        """
        :rtype: wechat_django.client.WeChatClient
                or wechatpy.client.api.wxa.WeChatWxa
        """
        if not self.abilities.api:
            raise WeChatAbilityError(WeChatAbilityError.API)
        if not hasattr(self, "_client"):
            client_factory = import_string(settings.WECHATCLIENT)
            self._client = client_factory(self)
            if self.type == self.Type.MINIPROGRAM:
                self._client = self._client.wxa
        return self._client

    @property
    def oauth(self):
        """
        :rtype: wechat_django.WeChatOAuthClient
        """
        if not self.abilities.oauth:
            raise WeChatAbilityError(WeChatAbilityError.OAUTH)
        if not hasattr(self, "_oauth"):
            client_factory = import_string(settings.OAUTHCLIENT)
            self._oauth = client_factory(self)
        return self._oauth

    @property
    def crypto(self):
        if not self.abilities.interactable:
            raise WeChatAbilityError(WeChatAbilityError.INTERACTABLE)
        if self.encoding_mode != self.EncodingMode.SAFE:
            return
        if not hasattr(self, "_crypto"):
            self._crypto = WeChatCrypto(
                self.token,
                self.encoding_aes_key,
                self.appid
            )
        return self._crypto

    def auth(self, code, scope=None):
        """用code进行微信授权
        :rtype: (wechat_django.models.WeChatUser, dict)
        :raises: wechatpy.exceptions.WeChatClientException
        :raises: wechatpy.exceptions.WeChatOAuthException
        """
        if not self.abilities.api:
            raise WeChatAbilityError(WeChatAbilityError.API)

        if self.type == WeChatApp.Type.SERVICEAPP:
            if not self.abilities.oauth:
                raise WeChatAbilityError(WeChatAbilityError.OAUTH)
            return self._auth_service(code, scope)
        elif self.type == WeChatApp.Type.MINIPROGRAM:
            return self._auth_miniprogram(code)
        else:
            raise WeChatClientException(WeChatErrorCode.UNAUTHORIZED_API)

    def _auth_service(self, code, scope=None):
        """服务号授权
        :rtype: (wechat_django.models.WeChatUser, dict)
        :raises: wechatpy.exceptions.WeChatOAuthException
        """
        from ..oauth import WeChatSNSScope
        if isinstance(scope, six.text_type):
            scope = (scope,)
        data = self.oauth.fetch_access_token(code)
        if scope and WeChatSNSScope.USERINFO in scope:
            # TODO: 优化授权流程 记录accesstoken及refreshtoken 延迟取userinfo
            user_info = self.oauth.get_user_info()
            data.update(user_info)
        return self.users.upsert_by_dict(data), data

    def _auth_miniprogram(self, code):
        """小程式授权
        :rtype: (wechat_django.models.WeChatUser, dict)
        :raises: wechatpy.exceptions.WeChatClientException
        """
        from . import Session
        data = self.client.code_to_session(code)
        user = self.users.upsert_by_dict(data)
        # 持久化session_key
        user.sessions.all().delete()
        user.sessions.add(Session(
            type=Session.Type.MINIPROGRAM,
            auth=dict(session_key=data["session_key"])
        ), bulk=False)
        # 移除session缓存
        try:
            del user.session
        except AttributeError:
            pass
        return user, data

    def build_url(self, urlname, kwargs=None, request=None, absolute=False):
        """构建url"""
        kwargs = kwargs or dict()
        kwargs["appname"] = self.name
        location = reverse("wechat_django:{0}".format(urlname), kwargs=kwargs)
        if not absolute:
            return location

        if request and not self.site_host:
            baseurl = "{}://{}".format(request.scheme, request.get_host())
        else:
            protocol = "https://" if self.site_https else "http://"
            if self.site_host:
                host = self.site_host
            else:
                allowed_hosts = settings.settings.ALLOWED_HOSTS
                if not allowed_hosts:
                    raise RuntimeError(
                        "You need setup a WECHAT_SITE_HOST when build "
                        "absolute url.")
                host = allowed_hosts[0]
            baseurl = protocol + host
        return baseurl + location

    def logger(self, name):
        return logging.getLogger(
            "wechat.{name}.{app}".format(name=name, app=self.name))

    def __str__(self):
        rv = "{title} ({name}) - {type}".format(
            title=self.title, name=self.name, type=self.type_name)
        if six.PY2:
            rv = rv.encode("utf-8")
        return rv
