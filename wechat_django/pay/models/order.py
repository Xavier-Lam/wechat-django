# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models as m
from django.dispatch import receiver
from django.utils import timezone as tz
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from wechatpy.pay.utils import get_external_ip

from wechat_django.models import WeChatModel
from wechat_django.utils.model import enum2choices, model_fields
from wechat_django.utils.web import get_ip
from . import WeChatPay
from .base import PayDateTimeField, paymethod


class UnifiedOrder(WeChatModel):
    ALLOW_UPDATES = (
        "device_info", "openid", "sub_openid", "trade_type", "total_fee",
        "fee_type")

    class TradeType(object):
        JSAPI = "JSAPI"
        NATIVE = "NATIVE"
        APP = "APP"
        MWEB = "MWEB"
        MICROPAY = "MICROPAY"

    class LimitPay(object):
        NONE = None
        NOCREDIT = "no_credit"

    class Receipt(object):
        NONE = None
        TRUE = "Y"

    class FeeType(object):
        CNY = "CNY"

    pay = m.ForeignKey(WeChatPay, on_delete=m.CASCADE, related_name="orders")

    device_info = m.CharField(_("device_info"), max_length=32, null=True)
    body = m.CharField(_("order body"), max_length=128)
    detail = m.TextField(_("order detail"), max_length=6000, null=True)
    out_trade_no = m.CharField(_("out_trade_no"), max_length=32)
    fee_type = m.CharField(
        _("fee_type"), max_length=16, null=True, default=FeeType.CNY)
    total_fee = m.PositiveIntegerField(_("total_fee"))
    spbill_create_ip = m.CharField(_("spbill_create_ip"), max_length=64) # TODO: 生成时是否应该赋值?
    time_start = PayDateTimeField("time_start", default=tz.now)
    time_expire = PayDateTimeField("time_expire")
    goods_tag = m.CharField(_("goods_tag"), max_length=32, null=True)
    trade_type = m.CharField(
        _("trade_type"), max_length=16, choices=enum2choices(TradeType))
    product_id = m.CharField(_("product id"), max_length=32, null=True)
    limit_pay = m.CharField(
        _("limit_pay"), max_length=32, null=True, default=LimitPay.NONE,
        choices=enum2choices(LimitPay))
    openid = m.CharField(_("openid"), max_length=128, null=True)
    sub_openid = m.CharField(_("sub openid"), max_length=128, null=True)
    receipt = m.CharField(
        _("recept"), max_length=8, null=True, default=Receipt.NONE,
        choices=enum2choices(Receipt))
    scene_info = JSONField(_("scene_info"), max_length=256, null=True)

    comment = m.TextField(_("comment"), blank=True)

    ext_info = JSONField(default=dict, editable=False)
    _call_args = JSONField(
        db_column="call_args", default=dict, null=True, editable=False)

    created_at = m.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated at"), auto_now=True)

    class Meta(object):
        verbose_name = _("Unified order")
        verbose_name_plural = _("Unified orders")

        index_together = (("pay", "created_at"), )
        unique_together = (("pay", "out_trade_no"),)

    @property
    def app_id(self):
        return self.pay.app_id

    def transaction_id(self):
        try:
            return self.result.transaction_id
        except AttributeError:
            return None
    transaction_id.short_description = _("transaction_id")

    def trade_state(self):
        try:
            return self.result.trade_state
        except AttributeError:
            return None
    trade_state.short_description = _("trade_state")

    @classmethod
    @paymethod("create_order")
    def create(cls, pay, user=None, request=None, **kwargs):
        """
        :type pay: wechat_django.pay.models.WeChatPay
        :param user: 发生支付的用户,如不填写,请填写openid或sub_openid
        :type user: wechat_django.models.WeChatUser
        :param request: 发生此次请求的request
        :param kwargs: 参见模型其他各字段的值
        """
        data = {}

        if user:
            if pay.sub_appid and user.app.appid == pay.sub_appid:
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
        # 更新ip
        self.spbill_create_ip = kwargs.pop(
            "client_ip",
            get_ip(request) or self.spbill_create_ip or get_external_ip())
        if self._call_args:
            self._call_args["client_ip"] = self.spbill_create_ip
        else:
            if not self.time_start:
                self.time_start = self.created_at
            if not self.time_expire:
                self.time_expire = self.created_at + datetime.timedelta(hours=2)
            # 构建call_args并缓存
            notify_url = self.pay.app.build_url(
                "order_notify", request=request,
                kwargs=dict(payname=self.pay.name), absolute=True)
            time_start_field = self._meta.get_field("time_start")
            time_expire_field = self._meta.get_field("time_expire")
            self._call_args = dict(
                trade_type=self.trade_type,
                body=self.body,
                total_fee=self.total_fee,
                notify_url=notify_url,
                client_ip=self.spbill_create_ip,
                user_id=self.openid,
                out_trade_no=self.out_trade_no,
                detail=self.detail,
                fee_type=self.fee_type,
                time_start=time_start_field.value_to_string(self),
                time_expire=time_expire_field.value_to_string(self),
                goods_tag=self.goods_tag,
                product_id=self.product_id,
                device_info=self.device_info,
                limit_pay=self.limit_pay,
                scene_info=self.scene_info,
                sub_user_id=self.sub_openid,
                receipt=self.receipt
            )
            self._call_args.update(kwargs)
        self.save()
        return self._call_args

    def prepay(self, request=None, **kwargs):
        """调用统一下单接口"""
        call_args = self.call_args(request, **kwargs)
        time_start_field = self._meta.get_field("time_start")
        call_args["time_start"] = time_start_field.to_python(call_args["time_start"])
        time_expire_field = self._meta.get_field("time_expire")
        call_args["time_expire"] = time_expire_field.to_python(call_args["time_expire"])
        return self.pay.client.order.create(**call_args)

    def jsapi_params(self, prepay_id, *args, **kwargs):
        return self.pay.client.jsapi.get_jsapi_params(
            prepay_id, *args, **kwargs)

    def close(self):
        """关闭订单"""
        rv = self.pay.client.order.close(out_trade_no=self.out_trade_no)
        self.sync()
        return rv

    def reverse(self):
        """撤销订单"""
        rv = self.pay.client.order.reverse(out_trade_no=self.out_trade_no)
        self.sync()
        return rv

    def sync(self):
        """更新订单状态"""
        result = self.pay.client.order.query(
            out_trade_no=self.out_trade_no)
        self.update(result)
        return self.result, result

    def update(self, result, signal=True, verify=True):
        """由字典更新数据"""
        verify and self.verify(result)
        updated = False
        for field in self.ALLOW_UPDATES:
            data = result.get(field)
            if not getattr(self, field) and data:
                setattr(self, field, data)
                updated = True
        updated and self.save()

        try:
            self.result.update(result, signal=signal, verify=False)
        except AttributeError:
            from . import UnifiedOrderResult
            transaction_id = result.get("transaction_id") or None
            obj = UnifiedOrderResult(
                order=self, transaction_id=transaction_id)
            obj.update(result, signal=signal, verify=False)

    def verify(self, result):
        """检查订单结果参数"""
        from . import UnifiedOrderResult
        # 检查mch_id是否一致
        assert result["mch_id"] == self.pay.mch_id, "incorrect mch_id"

        # 检查out_order_no是否一致
        assert result["out_trade_no"] == self.out_trade_no,\
            "incorrect out trade no"

        # 检查金额一致
        if result["trade_state"] == UnifiedOrderResult.State.SUCCESS:
            assert str(result["total_fee"]) == str(self.total_fee),\
                "incorrect total fee"

    def __str__(self):
        return "{0} ({1})".format(self.out_trade_no, self.body)


@receiver(m.signals.pre_save, sender=UnifiedOrder)
def on_order_created(sender, instance, *args, **kwargs):
    """订单保存前初始化订单参数"""
    if instance.time_expire is None:
        # 订单过期时间默认创建时间2小时后
        instance.time_expire = instance.time_start + tz.timedelta(hours=2)
