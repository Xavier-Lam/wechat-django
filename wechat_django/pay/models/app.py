# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from wechat_django.models import WeChatApp
from .. import settings
from ..client import WeChatPayClient


class WeChatPay(m.Model):
    app = m.ForeignKey(
        WeChatApp, on_delete=m.CASCADE, related_name="pays")

    title = m.CharField(
        _("title"), max_length=16, blank=True,
        help_text=_("商户号标识,用于后台辨识商户号"))
    name = m.CharField(
        _("name"), max_length=16, null=False, default=_("default"),
        help_text=_("商户号程序标识"))
    weight = m.IntegerField(_("weight"), default=0, null=False)

    mch_id = m.CharField(
        _("mch_id"), max_length=32, help_text=_("微信支付分配的商户号"))
    api_key = m.CharField(
        _("WeChatPay api_key"), max_length=128, help_text=_("商户号key"))

    sub_mch_id = m.CharField(
        _("sub_mch_id"), max_length=32, blank=True, null=True,
        help_text=_("子商户号，受理模式下填写"))
    mch_app_id = m.CharField(
        _("mch_app_id"), max_length=32,
        help_text=_("微信分配的主商户号appid，受理模式下填写"),
        blank=True, null=True)

    mch_cert = m.BinaryField(_("mch_cert"), blank=True, null=True)
    mch_key = m.BinaryField(_("mch_key"), blank=True, null=True)

    @property
    def appid(self):
        return self.mch_app_id if self.mch_app_id else self.app.appid

    @property
    def sub_appid(self):
        return self.app.appid if self.mch_app_id else None

    class Meta(object):
        verbose_name = _("WeChat pay")
        verbose_name_plural = _("WeChat pay")
        unique_together = (("app", "name"),)
        ordering = ("app", "-weight", "pk")

    @property
    def client(self):
        """:rtype: wechat_django.client.WeChatPayClient"""
        if not hasattr(self, "_client"):
            client_factory = import_string(settings.PAYCLIENT)
            self._client = client_factory(self)
        return self._client

    def __str__(self):
        return "{0} ({1})".format(self.title, self.name)
