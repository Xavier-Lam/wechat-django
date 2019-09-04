# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from wechat_django.models import WeChatModel
from wechat_django.utils.model import enum2choices, model_fields
from ..signals import order_updated
from . import UnifiedOrder
from .base import PayBooleanField, PayDateTimeField


class UnifiedOrderResult(WeChatModel):
    class State(object):
        SUCCESS = "SUCCESS"  # 成功
        REFUND = "REFUND"  # 转入退款
        NOTPAY = "NOTPAY"  # 未支付
        CLOSED = "CLOSED"  # 已关闭
        REVOKED = "REVOKED"  # 已撤销(刷卡支付)
        USERPAYING = "USERPAYING"  # 用户支付中
        PAYERROR = "PAYERROR"  # 支付失败(其他原因，如银行返回失败)
        FAIL = "FAIL"  # 回调拿到失败

    order = m.OneToOneField(
        UnifiedOrder, on_delete=m.CASCADE, related_name="result")

    transaction_id = m.CharField(
        _("transaction_id"), max_length=32, null=True)
    trade_state = m.CharField(
        _("trade_state"), max_length=32, choices=enum2choices(State))
    time_end = PayDateTimeField(_("pay time_end"), null=True)

    settlement_total_fee = m.PositiveIntegerField(
        _("settlement_total_fee"), null=True)
    cash_fee = m.PositiveIntegerField(_("cash_fee"), null=True)
    cash_fee_type = m.CharField(_("cash_fee_type"), max_length=16, null=True)
    coupon_fee = m.PositiveIntegerField(_("coupon_fee"), null=True)

    bank_type = m.CharField(_("bank_type"), max_length=16, null=True)
    detail = m.TextField(_("detail"), max_length=8192, null=True)

    is_subscribe = PayBooleanField(_("is_subscribe"), null=True)
    sub_is_subscribe = PayBooleanField(_("sub_is_subscribe"), null=True)

    ext_info = JSONField(default=dict, editable=False)

    created_at = m.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated at"), auto_now=True)

    class Meta(object):
        verbose_name = _("Unified order result")
        verbose_name_plural = _("Unified order results")

    def update(self, result, signal=True, verify=True):
        """根据参数更新订单状态"""
        verify and self.order.verify(result)
        # TODO: 支付成功后写入用户
        excludes = ("transaction_id",) if self.transaction_id else tuple()
        all_fields = model_fields(UnifiedOrderResult, excludes=excludes)
        ignore_fields = (
            "return_code", "return_msg", "appid", "mch_id", "device_info",
            "nonce_str", "sign", "result_code", "openid", "trade_type",
            "fee_type", "out_trade_no")
        for k, v in result.items():
            if k not in ignore_fields:
                if k in all_fields:
                    setattr(self, k, v)
                else:
                    self.ext_info[k] = v
        self.save()
        if signal:
            order_updated.send(sender=self.order.pay.staticname, result=self,
                               order=self.order, state=self.trade_state,
                               attach=result.get("attach"))

    def __str__(self):
        return _("%(order)s reuslt") % dict(order=self.order)
