# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from wechat_django.models import WeChatApp
from wechat_django.models.base import ShortcutBound
from wechat_django.utils.func import Static
from wechat_django.pay.client import WeChatPayClient


class ReadonlyProperty(property):
    def __init__(self, fget, *args, **kwargs):
        def fset(self, value):
            if hasattr(self, "_ready"):
                raise AttributeError

        super(ReadonlyProperty, self).__init__(fget, fset, *args, **kwargs)


class WeChatPayManager(m.Manager):
    def get_queryset(self):
        queryset = super(WeChatPayManager, self).get_queryset()
        return queryset.prefetch_related("app")


class WeChatPay(m.Model, ShortcutBound):
    app = m.ForeignKey(WeChatApp, on_delete=m.CASCADE, related_name="pays")

    title = m.CharField(_("title"), max_length=16, blank=True,
                        help_text=_("商户号标识,用于后台辨识商户号"))
    name = m.CharField(_("name"), max_length=16, null=False,
                       default="default", help_text=_("商户号程序标识"))

    _mch_id = m.CharField(_("mch_id"), max_length=32, db_column="mch_id",
                          help_text=_("微信支付分配的商户号,若为服务商,则为"
                                      "子商户号"))
    api_key = m.CharField(_("WeChatPay api_key"), max_length=128, blank=True,
                          help_text=_("商户号key"))

    sub_appid = m.CharField(_("sub_appid"), max_length=32, blank=True,
                            null=True,
                            help_text=_("微信分配的子商户公众账号ID,受理模式"
                                        "下填写"))

    mch_cert = m.BinaryField(_("mch_cert"), blank=True, null=True)
    mch_key = m.BinaryField(_("mch_key"), blank=True, null=True)

    weight = m.IntegerField(_("weight"), default=0, null=False)

    created_at = m.DateTimeField(_("created at"), null=True,
                                 auto_now_add=True)
    updated_at = m.DateTimeField(_("updated at"), auto_now=True)

    objects = WeChatPayManager()

    @property
    def mch_id(self):
        return self._mch_id

    @mch_id.setter
    def mch_id(self, value):
        self._mch_id = value

    @property
    def appid(self):
        return self.app.appid

    def __init__(self, *args, **kwargs):
        if "mch_id" in kwargs:
            kwargs["_mch_id"] = kwargs.pop("mch_id")
        super(WeChatPay, self).__init__(*args, **kwargs)

    @cached_property
    def staticname(self):
        """发送信号的sender"""
        if not self.pk:
            raise AttributeError
        return Static("{appname}.{payname}".format(
            appname=self.app.name, payname=self.name))

    @property
    def client(self):
        """:rtype: wechat_django.client.WeChatPayClient"""
        if not hasattr(self, "_client"):
            self._client = self._get_client()
        return self._client

    def _get_client(self):
        """:rtype: wechat_django.client.WeChatPayClient"""
        return WeChatPayClient(self)

    def __str__(self):
        return "{0} ({1})".format(self.title, self.name)

    class Meta(object):
        verbose_name = _("WeChat pay")
        verbose_name_plural = _("WeChat pay")
        unique_together = (("app", "name"),)
        ordering = ("app", "-weight", "pk")


class WeChatSubPay(WeChatPay):
    """微信支付子商户"""

    def __init__(self, *args, **kwargs):
        sub_mch_id = kwargs.pop("sub_mch_id", None)
        super(WeChatSubPay, self).__init__(*args, **kwargs)
        self.sub_mch_id = sub_mch_id
        self._ready = True

    @ReadonlyProperty
    def mch_id(self):
        return self.app.mch_id

    @ReadonlyProperty
    def api_key(self):
        return self.app.api_key

    @property
    def sub_mch_id(self):
        return self._mch_id

    @sub_mch_id.setter
    def sub_mch_id(self, value):
        self._mch_id = value

    @ReadonlyProperty
    def mch_cert(self):
        return self.app.mch_cert

    @ReadonlyProperty
    def mch_key(self):
        return self.app.mch_key

    class Meta(object):
        proxy = True
