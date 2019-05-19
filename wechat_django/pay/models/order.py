# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from wechat_django.models import WeChatModel
from . import WeChatPay


class UnifiedOrder(WeChatModel):
    pay = m.ForeignKey(WeChatPay, on_delete=m.CASCADE)

    device_info = m.CharField(_("device_info"), max_length=32, null=True)
    body = m.CharField(_("order body"), max_length=128)
    detail = m.TextField(_("order detail"), max_length=6000, null=True)
    # attach = m.CharField(_("order attach"), max_length=127, null=True)
    out_trade_no = m.CharField(_("out_trade_no"), max_length=32)
    fee_type = m.CharField(_("fee_type"), max_length=16, null=True)
    total_fee = m.PositiveIntegerField(_("total_fee"))
    spbill_create_ip = m.CharField(_("spbill_create_ip"), max_length=64)
    time_start = m.DateTimeField("time_start", null=True)
    time_expire = m.DateTimeField("time_expire", null=True)
    goods_tag = m.CharField(_("goods_tag"), max_length=32, null=True)
    trade_type = m.CharField(_("trade_type"), max_length=16) # TODO: choices
    product_id = m.CharField(_("product id"), max_length=32, null=True)
    limit_pay = m.CharField(_("limit_pay"), null=True) # TODO: choice no_credit
    openid = m.CharField(_("openid"), max_length=128, null=True)
    sub_openid = m.CharField(_("sub openid"), max_length=128, null=True)
    receipt = m.CharField(_("recept"), max_length=8, null=True) # TODO: choice Y
    scene_info = JSONField(_("scene_info"), max_length=256, null=True)

    # return_code = m.CharField(_("return_code"), max_length=16, null=True)
    # return_msg = m.CharField(_("return_msg"), max_length=128, null=True)
    # result_code = m.CharField(_("return_code"), max_length=16, null=True)
    # err_code = m.CharField(_("err_code"), max_length=32, null=True)
    # err_code_des = m.CharField(_("err_code_des"), max_length=128, null=True)

    prepay_id = m.CharField(_("prepay_id"), max_length=64, null=True)
    code_url = m.CharField(_("code_url"), max_length=64, null=True)

    extinfo = JSONField(default=dict, editable=False)

    created_at = m.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated at"), auto_now=True)

    class Meta(object):
        verbose_name = _("Unified order")
        verbose_name_plural = _("Unified orders")

        index_together = (("pay", "created_at"), )
        unique_together = (("pay", "out_trade_no"),)

    @classmethod
    def create(cls, pay, **kwargs):
        """:type pay: wechat_django.pay.models.WeChatPay"""
        pass

    def sync(self):
        """更新订单状态"""
        try:
            return self.result.sync()
        except AttributeError:
            result = self.pay.client.order.query(
                out_trade_no=self.out_trade_no)
            self.update(result)
            return self.result, result

    def update(self, result):
        updated = False
        allowed_fields = (
            "device_info", "openid", "sub_openid", "trade_type", "total_fee",
            "fee_type")
        for field in allowed_fields:
            data = result.get(field)
            if not getattr(self, field) and data:
                setattr(self, field, data)
                updated = True
        updated and self.save()

        try:
            self.result.update(result)
        except AttributeError:
            from . import UnifiedOrderResult
            obj = UnifiedOrderResult(
                order=self, transaction_id=result["transaction_id"])
            obj.update(result)
