# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid4

from django.utils import timezone as tz
from wechatpy import WeChatPay as WeChatPayBaseClient

from wechat_django.models import WeChatUser
from wechat_django.utils.web import get_ip
from ..models import UnifiedOrder, UnifiedOrderResult, WeChatPay
from ..models.base import PayDateTimeField
from ..signals import order_updated
from .base import mock, WeChatPayTestCase


class OrderTestCase(WeChatPayTestCase):
    def test_create(self):
        """测试生成订单"""
        openid = "openid"

        # 最简订单
        minimal = self.minimal_example
        body = minimal["body"]
        total_fee = minimal["total_fee"]
        user_main = self.app.users.create(openid=openid)
        request = self.rf().get("/")
        order = self.app.pay.create_order(user_main, request, **minimal)
        # 默认值
        self.assertEqual(order.trade_type, UnifiedOrder.TradeType.JSAPI)
        self.assertEqual(order.fee_type, UnifiedOrder.FeeType.CNY)
        self.assertAlmostEqual(
            order.time_start, tz.now(), delta=tz.timedelta(seconds=1))
        self.assertAlmostEqual(
            order.time_expire, tz.now() + tz.timedelta(hours=2),
            delta=tz.timedelta(seconds=1))

        self.assertEqual(order.openid, openid)
        self.assertEqual(order.body, body)
        self.assertEqual(order.total_fee, total_fee)

        # 子商户订单
        user_sub = self.app_sub.users.create(openid=openid)
        order = self.app_sub.pay.create_order(
            user_sub, request, **self.minimal_example)
        self.assertIsNone(order.openid)
        self.assertEqual(order.sub_openid, user_sub.openid)
        order = self.app_sub.pay.create_order(
            user_main, request, **self.minimal_example)
        self.assertIsNone(order.sub_openid)
        self.assertEqual(order.openid, user_main.openid)

        # 完整示例
        full = self.full_example
        order = self.app.pay.create_order(user_main, request, **full)
        for k, v in full.items():
            self.assertEqual(getattr(order, k), v)

    def test_call_args(self):
        """测试调用参数"""
        key_map = dict(
            spbill_create_ip="client_ip",
            openid="user_id",
            sub_openid="sub_user_id"
        )
        full = self.full_example
        full["openid"] = "openid"
        # 将时间转换为字符串
        timezone = tz.pytz.timezone("Asia/Shanghai")
        timeformat = "%Y%m%d%H%M%S"
        request = self.rf().get("/")
        order = self.app.pay.create_order(request=request, **full)
        call_args = order.call_args(request, dt2py=True)
        self.assertEqual(call_args, order.call_args(dt2py=True))
        _call_args = order.call_args(request)
        self.assertEqual(_call_args, order._call_args)
        self.assertEqual(
            call_args["notify_url"],
            self.app.build_url(
                "order_notify", kwargs=dict(payname=self.app.pay.name),
                request=request, absolute=True))
        self.assertEqual(call_args["client_ip"], get_ip(request))
        for k, v in full.items():
            fixed_key = key_map[k] if k in key_map else k
            if k in ("time_start", "time_expire"):
                v = PayDateTimeField.dt2str(v)
            self.assertEqual(_call_args[fixed_key], v)

        # 更新参数
        update = dict(
            client_ip="127.0.0.1",
            total_fee=200
        )
        full = self.full_example
        order = self.app.pay.create_order(request=request, **full)
        call_args = order.call_args(request, **update)
        self.assertEqual(call_args, order._call_args)
        self.assertEqual(call_args, order.call_args())
        for k, v in full.items():
            fixed_key = key_map[k] if k in key_map else k
            if k in ("time_start", "time_expire"):
                v = v.astimezone(timezone).strftime(timeformat)
            fixed_val = update[fixed_key] if fixed_key in update else v
            self.assertEqual(call_args[fixed_key], fixed_val)

    def test_update(self):
        """测试更新订单"""
        # 测试无result更新待支付订单
        with mock.patch.object(UnifiedOrder, "verify"):
            order = self.app.pay.create_order(**self.minimal_example)
            result = self.notpay(self.app.pay, order)
            order.update(result)
            for key, value in result.items():
                if key in UnifiedOrder.ALLOW_UPDATES:
                    v = getattr(order, key)
                    v = v if v is None else str(v)
                    self.assertEqual(v, value)
                if key in self.list_fields(UnifiedOrderResult):
                    v = getattr(order.result, key)
                    v = v if v is None else str(v)
                    self.assertEqual(v, value)
            self.assertEqual(UnifiedOrder.verify.call_count, 1)

        # 测试无result更新已完成订单
        with mock.patch.object(UnifiedOrder, "verify"):
            order = self.app.pay.create_order(**self.minimal_example)
            result = self.success(self.app.pay, order)
            order.update(result)
            for key, value in result.items():
                if key in UnifiedOrder.ALLOW_UPDATES:
                    v = getattr(order, key)
                    v = v if v is None else str(v)
                    self.assertEqual(v, value)
                if key in self.list_fields(UnifiedOrderResult):
                    v = getattr(order.result, key)
                    v = v if v is None else str(v)
                    self.assertEqual(v, value)
            self.assertEqual(UnifiedOrder.verify.call_count, 1)

        # 测试有result更新待支付订单
        order = self.app.pay.create_order(**self.minimal_example)
        result = self.notpay(self.app.pay, order)
        order.update(result)
        with mock.patch.object(UnifiedOrder, "verify"):
            result = self.notpay(self.app.pay, order)
            order.update(result)
            for key, value in result.items():
                if key in UnifiedOrder.ALLOW_UPDATES:
                    v = getattr(order, key)
                    v = v if v is None else str(v)
                    self.assertEqual(v, value)
                if key in self.list_fields(UnifiedOrderResult):
                    v = getattr(order.result, key)
                    v = v if v is None else str(v)
                    self.assertEqual(v, value)
            self.assertEqual(UnifiedOrder.verify.call_count, 1)

        # 测试有result更新已完成订单
        order = self.app.pay.create_order(**self.minimal_example)
        result = self.notpay(self.app.pay, order)
        order.update(result)
        with mock.patch.object(UnifiedOrder, "verify"):
            result = self.success(self.app.pay, order)
            order.update(result)
            for key, value in result.items():
                if key in UnifiedOrder.ALLOW_UPDATES:
                    v = getattr(order, key)
                    v = v if v is None else str(v)
                    self.assertEqual(v, value)
                if key in self.list_fields(UnifiedOrderResult):
                    v = getattr(order.result, key)
                    v = v if v is None else str(v)
                    self.assertEqual(v, value)
            self.assertEqual(UnifiedOrder.verify.call_count, 1)

        # 测试再度更新已完成订单
        with mock.patch.object(UnifiedOrder, "verify"):
            result = self.success(self.app.pay, order)
            order.update(result)
            for key, value in result.items():
                if key in UnifiedOrder.ALLOW_UPDATES:
                    v = getattr(order, key)
                    v = v if v is None else str(v)
                    self.assertEqual(v, value)
                if key in self.list_fields(UnifiedOrderResult):
                    v = getattr(order.result, key)
                    v = v if v is None else str(v)
                    self.assertEqual(v, value)
            self.assertEqual(UnifiedOrder.verify.call_count, 1)

        # 测试回调更新
        result = self.notify(self.app.pay, order)
        order.update(result)
        for key, value in result.items():
            if key in UnifiedOrder.ALLOW_UPDATES:
                v = getattr(order, key)
                v = v if v is None else str(v)
                self.assertEqual(v, value)
            if key in self.list_fields(UnifiedOrderResult):
                v = getattr(order.result, key)
                v = v if v is None else str(v)
                self.assertEqual(v, value)

        # 测试回调更新
        order = self.app.pay.create_order(**self.minimal_example)
        result = self.notify(self.app.pay, order)
        order.update(result)
        for key, value in result.items():
            if key in UnifiedOrder.ALLOW_UPDATES:
                v = getattr(order, key)
                v = v if v is None else str(v)
                self.assertEqual(v, value)
            if key in self.list_fields(UnifiedOrderResult):
                v = getattr(order.result, key)
                v = v if v is None else str(v)
                self.assertEqual(v, value)

    def test_verify(self):
        """测试订单参数是否一致"""
        order = self.app.pay.create_order(**self.minimal_example)
        result = self.success(self.app.pay, order)
        result["total_fee"] = 1
        self.assertRaises(AssertionError, order.verify, result)

        result = self.success(self.app.pay, order)
        result["out_trade_no"] = "123"
        self.assertRaises(AssertionError, order.verify, result)

        result = self.success(self.app.pay, order)
        result["mch_id"] = "abc"
        self.assertRaises(AssertionError, order.verify, result)

        result = self.success(self.app.pay, order)
        order.verify(result)

    def test_signal(self):
        """测试订单状态更新信号"""
        with mock.patch.object(order_updated, "send"):
            order = self.app.pay.create_order(**self.minimal_example)
            result = self.success(self.app.pay, order)
            order.update(result)
            self.assertEqual(order_updated.send.call_count, 1)
            kwargs = dict(
                result=order.result,
                order=order,
                state=UnifiedOrderResult.State.SUCCESS,
                attach=result.get("attach")
            )
            self.assertCallArgsEqual(order_updated.send, kwargs=kwargs)

        with mock.patch.object(order_updated, "send"):
            order = self.app.pay.create_order(**self.minimal_example)
            result = self.success(self.app.pay, order)
            order.update(result, signal=False)
            self.assertEqual(order_updated.send.call_count, 0)

    def test_sync(self):
        """测试同步订单"""
        pass

    def test_prepay(self):
        """测试prepay"""
        pass

    def test_close(self):
        """测试关闭订单"""
        pass

    @property
    def minimal_example(self):
        return dict(
            body="body",
            out_trade_no=str(uuid4()),
            total_fee=101
        )

    @property
    def full_example(self):
        return dict(
            device_info="013467007045764",
            body="body",
            # receipt="Y",
            detail="detail",
            out_trade_no=uuid4(),
            total_fee=101,
            time_start=tz.now(),
            time_expire=tz.now() + tz.timedelta(minutes=30),
            goods_tag="goods_tag",
            trade_type=UnifiedOrder.TradeType.APP,
            product_id="product_id",
            limit_pay=UnifiedOrder.LimitPay.NOCREDIT,
            scene_info={
                "store_info": {
                    "id": "SZTX001",
                    "name": "腾大餐厅",
                    "area_code": "440305",
                    "address": "科技园中一路腾讯大厦"
                }
            }
        )

    def notpay(self, pay, order):
        return {
            "return_code": "SUCCESS",
            "return_msg": "OK",
            "appid": str(pay.appid),
            "mch_id": str(pay.mch_id),
            "device_info": None,
            "nonce_str": str(uuid4()),
            "sign": str(uuid4()),
            "result_code": "SUCCESS",
            "total_fee": "101",
            "out_trade_no": order.out_trade_no,
            "trade_state": "NOTPAY",
            "trade_state_desc": "订单未支付"
        }

    def success(self, pay, order):
        """
        :type pay: wechat_django.pay.models.WeChatPay
        :type order: wechat_django.pay.models.UnifiedOrder
        """
        return {
            "openid": "openid",
            "sub_mch_id": None,
            "cash_fee_type": "CNY",
            "settlement_total_fee": "101",
            "nonce_str": str(uuid4()),
            "return_code": "SUCCESS",
            "err_code_des": "SUCCESS",
            "time_end": "20190613190854",
            "mch_id": str(pay.mch_id),
            "trade_type": "JSAPI",
            "trade_state_desc": "ok",
            "trade_state": "SUCCESS",
            "sign": str(uuid4()),
            "cash_fee": "101",
            "is_subscribe": "Y",
            "return_msg": "OK",
            "fee_type": "CNY",
            "bank_type": "CMC",
            "attach": "sandbox_attach",
            "device_info": "sandbox",
            "out_trade_no": order.out_trade_no,
            "transaction_id": order.out_trade_no,
            "total_fee": "101",
            "appid": str(pay.appid),
            "result_code": "SUCCESS",
            "err_code": "SUCCESS"
        }

    def notify(self, pay, order):
        rv = {
            "appid": pay.appid,
            "bank_type": "CFT",
            "cash_fee": "1",
            "fee_type": "CNY",
            "is_subscribe": "N",
            "mch_id": pay.mch_id,
            "nonce_str": "nonce_str",
            "openid": "openid",
            "out_trade_no": order.out_trade_no,
            "result_code": "SUCCESS",
            "return_code": "SUCCESS",
            "time_end": "20190618223614",
            "total_fee": "101",
            "trade_type": "JSAPI",
            "transaction_id": order.out_trade_no,
            "sign": "sign"
        }
        rv["trade_state"] = rv["result_code"]
        return rv
