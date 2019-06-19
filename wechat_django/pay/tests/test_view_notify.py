# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid4

import xmltodict

from wechat_django.sites.wechat import default_site
from ..exceptions import WeChatPayNotifyError
from ..models import UnifiedOrderResult
from ..notify import NotifyViewSet
from .base import mock, WeChatPayTestCase


class NotifyTestCase(WeChatPayTestCase):
    sign = "sign"

    def test_response(self):
        """测试响应"""
        url = self.app.build_url(
            "order_notify", kwargs=dict(payname=self.app.pay.name))
        # 测试成功响应
        order = self.app.pay.create_order(**self.minimal_example)
        xml = self.success_order_notify(self.app.pay, order)
        with mock.patch("wechatpy.pay.calculate_signature") as m:
            m.return_value = self.sign
            resp = self.client.post(
                url, data=xml, content_type="text/xml")
            data = xmltodict.parse(resp.content)["xml"]
            self.assertEqual(data["return_code"], "SUCCESS")
            self.assertNotEqual(data["return_msg"], "OK")

        # 测试失败响应
        resp = self.client.get(url)
        data = xmltodict.parse(resp.content)["xml"]
        self.assertEqual(data["return_code"], "FAIL")
        self.assertNotEqual(data["return_msg"], "OK")

    def test_prepare_request(self):
        """测试请求预处理"""
        appname = self.app.name
        url = self.app.build_url(
            "order_notify", kwargs=dict(payname=self.app.pay.name))
        # 测试签名正确
        order = self.app.pay.create_order(**self.minimal_example)
        xml = self.success_order_notify(self.app.pay, order)
        request = self.rf().post(
            url, data=xml, content_type="text/xml")

        viewset = NotifyViewSet(default_site)
        with mock.patch("wechatpy.pay.calculate_signature") as m:
            m.return_value = self.sign
            pay, data = viewset._prepare(
                request, self.app.name, self.app.pay.name)

        # 测试签名错误
        self.assertRaises(
            WeChatPayNotifyError, viewset._prepare,
            request, self.app.name, self.app.pay.name)

    def test_notify_order(self):
        """测试订单回调通知"""
        url = self.app.build_url(
            "order_notify", kwargs=dict(payname=self.app.pay.name))
        order = self.app.pay.create_order(**self.minimal_example)
        xml = self.success_order_notify(self.app.pay, order)
        request = self.rf().post(
            url, data=xml, content_type="text/xml")

        viewset = NotifyViewSet(default_site)
        with mock.patch("wechatpy.pay.calculate_signature") as m:
            m.return_value = self.sign
            pay, data = viewset._prepare(
                request, self.app.name, self.app.pay.name)

        viewset.order_notify(request, pay, data)
        self.assertEqual(order.result.transaction_id, order.out_trade_no)
        self.assertEqual(
            order.result.trade_state, UnifiedOrderResult.State.SUCCESS)

    @property
    def minimal_example(self):
        return dict(
            body="body",
            out_trade_no=str(uuid4()),
            total_fee=101
        )

    def success_order_notify(self, pay, order):
        return """
            <xml>
                <appid><![CDATA[{appid}]]></appid>
                <bank_type><![CDATA[CFT]]></bank_type>
                <cash_fee><![CDATA[1]]></cash_fee>
                <fee_type><![CDATA[CNY]]></fee_type>
                <is_subscribe><![CDATA[N]]></is_subscribe>
                <mch_id><![CDATA[{mch_id}]]></mch_id>
                <nonce_str><![CDATA[nonce_str]]></nonce_str>
                <openid><![CDATA[{openid}]]></openid>
                <out_trade_no><![CDATA[{out_trade_no}]]></out_trade_no>
                <result_code><![CDATA[SUCCESS]]></result_code>
                <return_code><![CDATA[SUCCESS]]></return_code>
                <sign><![CDATA[{sign}]]></sign>
                <time_end><![CDATA[20190618223614]]></time_end>
                <total_fee>101</total_fee>
                <trade_type><![CDATA[JSAPI]]></trade_type>
                <transaction_id><![CDATA[{out_trade_no}]]></transaction_id>
            </xml>
        """.format(
            appid=pay.appid,
            mch_id=pay.mch_id,
            openid="openid",
            out_trade_no=order.out_trade_no,
            sign=self.sign
        )
