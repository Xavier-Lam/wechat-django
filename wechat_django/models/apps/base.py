# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django import forms
from django.apps import apps
from django.db import models as m
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
import six
from wechatpy.crypto import WeChatCrypto

from wechat_django import settings
from wechat_django.constants import AppType, WeChatSNSScope
from wechat_django.exceptions import WeChatAbilityError
from wechat_django.models import MsgLogFlag
from wechat_django.oauth import WeChatOAuthClient
from wechat_django.utils.func import Static
from wechat_django.utils.model import enum2choices
from .ability import Abilities


class WeChatAppQuerySet(m.QuerySet):
    def get_by_name(self, name):
        return self.get(name=name)

    def create(self, **kwargs):
        obj = super(WeChatAppQuerySet, self).create(**kwargs)
        # create 返回子代理类
        obj.__class__ = self.model.get_apptype_cls(obj.type)
        return obj


class AppAdminProperty(property):
    field_type = forms.CharField


class ConfigurationProperty(AppAdminProperty):
    def __init__(self, key, default=None, doc="", **kw):
        kwargs = dict(
            fget=lambda self: self.configurations.get(
                key, default(self) if callable(default) else default),
            fset=lambda self, v: self.configurations.update({key: v}),
            fdel=lambda self: self.configurations.pop(key, None),
            doc=doc
        )
        kw["help_text"] = doc
        super(ConfigurationProperty, self).__init__(**kwargs)

        for k, v in kw.items():
            setattr(self, k, v)


class FlagProperty(AppAdminProperty):
    field_type = forms.BooleanField

    def __init__(self, flag, default=None, doc="", **kw):
        def fset(self, value):
            self.flags = self.flags | flag
            if not value:
                self.flags ^= flag

        kwargs = dict(
            fget=lambda self: bool(self.flags & flag),
            fset=fset,
            fdel=lambda self: (self.flags | flag) ^ flag,
            doc=doc
        )
        kw["help_text"] = doc
        super(FlagProperty, self).__init__(**kwargs)

        for k, v in kw.items():
            setattr(self, k, v)


class WeChatApp(m.Model):
    _registered_type_cls = dict()

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
        UNAUTH = 0x01  # 未认证

    title = m.CharField(_("title"), max_length=16, null=False,
                        help_text=_("公众号名称,用于后台辨识公众号"))
    name = m.CharField(_("name"), max_length=16, blank=False, null=False,
                       unique=True,
                       help_text=_("公众号唯一标识,可采用微信号,设定后不可修改,用于程序辨识"))
    desc = m.TextField(_("description"), default="", blank=True)

    appid = m.CharField(_("AppId"), max_length=32, null=False)
    appsecret = m.CharField(_("AppSecret"), max_length=64, blank=True,
                            null=True)
    type = m.PositiveSmallIntegerField(_("type"), default=AppType.SERVICEAPP,
                                       choices=enum2choices(AppType))

    token = m.CharField(max_length=32, null=True, blank=True)
    encoding_aes_key = m.CharField(_("EncodingAESKey"), max_length=43,
                                   null=True, blank=True)
    encoding_mode = m.PositiveSmallIntegerField(_("encoding mode"),
                                                default=EncodingMode.PLAIN,
                                                choices=enum2choices(EncodingMode))

    flags = m.IntegerField(_("flags"), default=0)

    ext_info = JSONField(db_column="ext_info", default={})
    configurations = JSONField(db_column="configurations", default={})

    created_at = m.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated at"), auto_now=True)

    objects = WeChatAppQuerySet.as_manager()

    abilities = Abilities()

    @cached_property
    def pay(self):
        if apps.is_installed("wechat_django.pay"):
            return self.pays.first()

    @cached_property
    def staticname(self):
        """发送信号的sender"""
        if not self.pk:
            raise AttributeError
        return Static("{appname}".format(appname=self.name))

    site_https = ConfigurationProperty("SITE_HTTPS",
                                       default=settings.SITE_HTTPS,
                                       doc="回调地址是否为https",
                                       field_type=forms.BooleanField)
    site_host = ConfigurationProperty("SITE_HOST", default=settings.SITE_HOST,
                                      doc="接收微信回调的域名")

    class Meta(object):
        verbose_name = _("WeChat app")
        verbose_name_plural = _("WeChat apps")

    def __init__(self, *args, **kwargs):
        super(WeChatApp, self).__init__(*args, **kwargs)
        if hasattr(self.__class__, "_APPTYPE"):
            self.type = self._APPTYPE

    @classmethod
    def register_apptype_cls(cls, apptype):
        """注册某一种类型App的代理类"""
        def decorator(sub_cls):
            cls._registered_type_cls[apptype] = sub_cls
            sub_cls._APPTYPE = apptype
            return sub_cls
        return decorator

    @classmethod
    def get_apptype_cls(cls, apptype):
        """获取某一种类型App的代理类"""
        try:
            sub_model = cls._registered_type_cls[apptype]
        except KeyError:
            raise RuntimeError(_("You didn't register this app type!"))

        if cls is WeChatApp:
            model_cls = sub_model
        elif issubclass(cls, sub_model):
            # 已经是子类或者是用户设置的子类代理类
            model_cls = cls
        else:
            # 用户设置的普通代理类,优先采用用户设置的属性及方法
            model_cls = type(cls.__name__, (cls, sub_model), dict())

        return model_cls

    @classmethod
    def from_db(cls, db, field_names, values):
        app_type = dict(zip(field_names, values)).get("type")

        if not app_type:
            raise ValueError(_("You must select `type` field!"))

        model_cls = cls.get_apptype_cls(app_type)
        return m.Model.from_db.__func__(model_cls, db, field_names, values)

    @property
    def type_name(self):
        if self.type == AppType.MINIPROGRAM:
            return _("MINIPROGRAM")
        elif self.type == AppType.SERVICEAPP:
            return _("SERVICEAPP")
        elif self.type == AppType.SUBSCRIBEAPP:
            return _("SUBSCRIBEAPP")
        elif self.type == AppType.PAYPARTNER:
            return _("PAYPARTNER")
        elif self.type == AppType.WEB:
            return _("WEBAPP")
        else:
            return _("unknown")

    def build_url(self, urlname, kwargs=None, request=None, absolute=False):
        """构建url"""
        kwargs = kwargs or dict()
        kwargs["appname"] = self.name
        location = reverse("wechat_django:{0}".format(urlname), kwargs=kwargs)
        if not absolute:
            return location

        if request and not self.site_host:
            baseurl = "{}://{}".format(
                "https" if self.site_https else request.scheme,
                request.get_host())
        else:
            protocol = "https://" if self.site_https else "http://"
            if self.site_host:
                host = self.site_host
            else:
                allowed_hosts = settings.settings.ALLOWED_HOSTS
                if not allowed_hosts:
                    raise RuntimeError("You need setup a WECHAT_SITE_HOST "
                                       "when build absolute url.")
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


class ApiClientApp(WeChatApp):
    """可以调用api"""

    class Meta(object):
        proxy = True

    accesstoken_url = ConfigurationProperty("ACCESSTOKEN_URL",
                                            widget=forms.URLInput,
                                            doc="获取accesstoken的url,不填直"
                                                "接从微信取")

    @property
    def client(self):
        """
        :rtype: wechat_django.client.WeChatClient
                or wechatpy.client.api.wxa.WeChatWxa
        """
        if not self.abilities.api:
            raise WeChatAbilityError(WeChatAbilityError.API)
        if not hasattr(self, "_client"):
            self._client = self._get_client()
        return self._client

    def _get_client(self):
        """
        :rtype: wechat_django.client.WeChatClient
                or wechatpy.client.api.wxa.WeChatWxa
        """
        from wechat_django.client import WeChatClient
        return WeChatClient(self)


class InteractableApp(WeChatApp):
    """可以进行消息交互"""

    class Meta(object):
        proxy = True

    log_message = FlagProperty(MsgLogFlag.LOG_MESSAGE, False,
                               doc="log messages")
    log_reply = FlagProperty(MsgLogFlag.LOG_REPLY, False, doc="log reply")

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


class OAuthApp(WeChatApp):
    """可以进行OAuth授权的app"""

    class Meta(object):
        proxy = True


    oauth_url = ConfigurationProperty("OAUTH_URL",
                                      default=lambda self: self.OAUTH_URL,
                                      widget=forms.URLInput,
                                      doc="授权重定向的url,用于第三方网页授权"
                                          "换取code,默认直接微信授权")

    @property
    def oauth(self):
        """
        :rtype: wechat_django.WeChatOAuthClient
        """
        if not hasattr(self, "_oauth"):
            self._oauth = self._get_oauth()
        return self._oauth

    def auth(self, code, scope=None):
        """
        用code进行微信授权
        :rtype: (wechat_django.models.WeChatUser, dict)
        :raises: wechatpy.exceptions.WeChatClientException
        :raises: wechatpy.exceptions.WeChatOAuthException
        """
        if isinstance(scope, six.text_type):
            scope = (scope,)
        data = self.oauth.fetch_access_token(code)
        if scope and WeChatSNSScope.USERINFO in scope:
            # TODO: 优化授权流程 记录accesstoken及refreshtoken 延迟取userinfo
            user_info = self.oauth.get_user_info()
            data.update(user_info)
        return self.users.upsert_by_dict(data), data

    def _get_oauth(self):
        """
        :rtype: wechat_django.WeChatOAuthClient
        """
        return WeChatOAuthClient(self)
