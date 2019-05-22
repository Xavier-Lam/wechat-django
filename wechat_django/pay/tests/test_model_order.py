# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid4

from django.utils import timezone as tz
from wechatpy import WeChatPay as WeChatPayBaseClient

from wechat_django.models import WeChatUser
from wechat_django.utils.web import get_ip
from ..models import UnifiedOrder, WeChatPay
from .base import mock, WeChatPayTestCase


class OrderTestCase(WeChatPayTestCase):
    def test_create(self):
        """测试生成订单"""
        openid = "openid"
        body = "body"
        total_fee = 100

        # 最简订单
        minimal = dict(
            body=body,
            total_fee=total_fee
        )
        user_main = self.app.users.create(openid=openid)
        request = self.rf().get("/")
        order = self.app.pay.create_order(
            user_main, request, out_trade_no=uuid4(), **minimal)
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
            user_sub, request, out_trade_no=uuid4(), **minimal)
        self.assertIsNone(order.openid)
        self.assertEqual(order.sub_openid, user_sub.openid)
        order = self.app_sub.pay.create_order(
            user_main, request, out_trade_no=uuid4(), **minimal)
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
        request = self.rf().get("/")
        order = self.app.pay.create_order(request=request, **full)
        call_args = order.call_args(request)
        self.assertEqual(call_args, order._call_args)
        self.assertEqual(call_args, order.call_args())
        self.assertEqual(
            call_args["notify_url"],
            self.app.build_url(
                "order_notify", request=request, absolute=True))
        self.assertEqual(call_args["client_ip"], get_ip(request))
        for k, v in full.items():
            fixed_key = key_map[k] if k in key_map else k
            self.assertEqual(call_args[fixed_key], v)

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
            fixed_val = update[fixed_key] if fixed_key in update else v
            self.assertEqual(call_args[fixed_key], fixed_val)

    def test_update(self):
        """测试更新订单"""
        pass

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
    def full_example(self):
        return dict(
            device_info="013467007045764",
            body="body",
            receipt="Y",
            detail="detail",
            out_trade_no=uuid4(),
            total_fee=100,
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
