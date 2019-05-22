# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import xmltodict

from ..notify import NotifyViewSet
from .base import mock, WeChatPayTestCase


class NotifyTestCase(WeChatPayTestCase):
    def test_response(self):
        """测试响应"""
        url = self.app.build_url("order_notify")
        # 测试成功响应
        pass

        # 测试失败响应
        resp = self.client.get(url)
        data = xmltodict.parse(resp.content)["xml"]
        self.assertEqual(data["return_code"], "FAIL")
        self.assertNotEqual(data["return_msg"], "OK")

    def test_prepare_request(self):
        """测试请求预处理"""
        appname = self.app.name
        url = self.app.build_url("order_notify")
        request = self.rf().post(url)

    def test_notify_order(self):
        """测试订单回调通知"""
        pass
