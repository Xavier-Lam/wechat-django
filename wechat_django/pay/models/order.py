# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from wechatpy.pay.utils import get_external_ip

from wechat_django.models import WeChatModel
from wechat_django.utils.model import enum2choices, model_fields
from wechat_django.utils.web import get_ip
from . import WeChatPay
from .base import PayDateTimeField, paymethod


class UnifiedOrder(WeChatModel):
    class TradeType(object):
        JSAPI = "JSAPI"
        NATIVE = "NATIVE"
        APP = "APP"
        MWEB = "MWEB"
        MICROPAY = "MICROPAY"

    class LimitPay(object):
        DEFAULT = None
        NOCREDIT = "no_credit"

    class Receipt(object):
        DEFAULT = None
        TRUE = "Y"
    
    pay = m.ForeignKey(WeChatPay, on_delete=m.CASCADE, related_name="orders")

    device_info = m.CharField(_("device_info"), max_length=32, null=True)
    body = m.CharField(_("order body"), max_length=128)
    detail = m.TextField(_("order detail"), max_length=6000, null=True)
    out_trade_no = m.CharField(_("out_trade_no"), max_length=32)
    fee_type = m.CharField(_("fee_type"), max_length=16, null=True)
    total_fee = m.PositiveIntegerField(_("total_fee"))
    spbill_create_ip = m.CharField(_("spbill_create_ip"), max_length=64)
    time_start = PayDateTimeField("time_start", null=True)
    time_expire = PayDateTimeField("time_expire", null=True)
    goods_tag = m.CharField(_("goods_tag"), max_length=32, null=True)
    trade_type = m.CharField(
        _("trade_type"), max_length=16, choices=enum2choices(TradeType))
    product_id = m.CharField(_("product id"), max_length=32, null=True)
    limit_pay = m.CharField(
        _("limit_pay"), max_length=32, null=True, default=LimitPay.DEFAULT,
        choices=enum2choices(LimitPay))
    openid = m.CharField(_("openid"), max_length=128, null=True)
    sub_openid = m.CharField(_("sub openid"), max_length=128, null=True)
    receipt = m.CharField(
        _("recept"), max_length=8, null=True, default=Receipt.DEFAULT,
        choices=enum2choices(Receipt))
    scene_info = JSONField(_("scene_info"), max_length=256, null=True)

    ext_info = JSONField(default=dict, editable=False)
    _call_args = JSONField(db_column="call_args", default=dict, editable=False)

    created_at = m.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated at"), auto_now=True)

    class Meta(object):
        verbose_name = _("Unified order")
        verbose_name_plural = _("Unified orders")

        index_together = (("pay", "created_at"), )
        unique_together = (("pay", "out_trade_no"),)

    @classmethod
    @paymethod
    def create(cls, pay, user=None, request=None, **kwargs):
        """
        :type pay: wechat_django.pay.models.WeChatPay
        :param user: 发生支付的用户,如不填写,请填写openid或sub_openid
        :type user: wechat_django.models.WeChatUser
        :param request: 发生此次请求的request
        :param kwargs: 参见数据库其他各字段的值,以及
                       `wechatpy.pay.api.order.WeChatOrder.create`方法的传参
        """
        data = {}

        if user:
            if user.app.appid == pay.mch_app_id:
                data["sub_openid"] = user.openid
            else:
                data["openid"] = user.openid

        # 自动构造trade_type
        data["trade_type"] = cls.TradeType.JSAPI

        fields = model_fields(UnifiedOrder)
        data.update({k: v for k, v in kwargs.items() if k in fields})

        return cls.objects.create(pay=pay, **data)

    def call_args(self, request=None, **kwargs):
        """调用统一下单接口的参数
        :param attach: 附加数据
        :param kwargs: 覆盖默认生成的数据
        """
        if not self._call_args:
            # TODO: attach和client_ip是否应该拿到外头
            self.spbill_create_ip = self.spbill_create_ip or get_ip(request)\
                or get_external_ip()
            notify_url = self.pay.app.build_url(
                "order_notify", request=request, absolute=True)
            call_args = dict(
                trade_type=self.trade_type,
                body=self.body,
                total_fee=self.total_fee,
                notify_url=notify_url,
                client_ip=self.spbill_create_ip,
                user_id=self.openid,
                out_trade_no=self.out_trade_no,
                detail=self.detail,
                fee_type=self.fee_type,
                time_start=self.time_start and str(self.time_start),
                time_expire=self.time_expire and str(self.time_expire),
                goods_tag=self.goods_tag,
                product_id=self.product_id,
                device_info=self.device_info,
                limit_pay=self.limit_pay,
                scene_info=self.scene_info,
                sub_user_id=self.sub_openid
            )
            call_args.update(kwargs)
            self._call_args = call_args
            self.save()
        return self._call_args

    def prepay(self, request=None, **kwargs):
        """调用统一下单接口"""
        return self.pay.client.order.create(
            **self.call_args(request, **kwargs))

    def close(self):
        """关闭订单"""
        return self.pay.client.order.close(self.out_trade_no)

    def reverse(self):
        """撤销订单"""
        return self.pay.client.order.reverse(out_trade_no=self.out_trade_no)

    def sync(self):
        """更新订单状态"""
        try:
            return self.result.sync()
        except AttributeError:
            result = self.pay.client.order.query(
                out_trade_no=self.out_trade_no)
            self.update(result)
            return self.result, result

    def update(self, result, signal=True):
        """由字典更新数据"""
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
            self.result.update(result, signal)
        except AttributeError:
            from . import UnifiedOrderResult
            obj = UnifiedOrderResult(
                order=self, transaction_id=result["transaction_id"])
            obj.update(result, signal)
