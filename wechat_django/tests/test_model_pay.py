# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from wechatpy import WeChatPay as WeChatPayBaseClient

from ..pay.models import WeChatPay
from .base import mock, WeChatTestCase


class PayTestCase(WeChatTestCase):
    def test_client_init(self):
        """测试WeChatPayClient的构建"""
        mch_id = "mch_id"
        api_key = "api_key"
        sub_mch_id = "sub_mch_id"
        mch_app_id = "mch_app_id"
        pay = WeChatPay(app=self.app, api_key=api_key, mch_id=mch_id)
        sub_pay = WeChatPay(
            app=self.app, api_key=api_key, mch_id=mch_id,
            sub_mch_id=sub_mch_id, mch_app_id=mch_app_id)
        with mock.patch.object(WeChatPayBaseClient, "__init__"):
            pay.client
            self.assertCallArgsEqual(
                WeChatPayBaseClient.__init__, kwargs=dict(
                    mch_id=mch_id,
                    api_key=api_key,
                    appid=self.app.appid
                ))

            sub_pay.client
            self.assertCallArgsEqual(
                WeChatPayBaseClient.__init__, kwargs=dict(
                    mch_id=mch_id,
                    api_key=api_key,
                    appid=mch_app_id,
                    sub_appid=self.app.appid,
                    sub_mch_id=sub_mch_id
                ))

    def test_client_cert(self):
        """测试请求时证书是否正确使用"""
        mch_id = "mch_id"
        api_key = "api_key"
        mch_cert = b"mch_cert"
        mch_key = b"mch_key"
        pay = WeChatPay(app=self.app, api_key=api_key, mch_id=mch_id)
        cert_pay = WeChatPay(
            app=self.app, api_key=api_key, mch_id=mch_id, mch_cert=mch_cert,
            mch_key=mch_key)

        that = self
        origin_request = WeChatPayBaseClient._request
        try:
            # 无证书请求时不带证书文件
            def mock_request(self, *args, **kwargs):
                that.assertFalse(self.mch_cert)
                that.assertFalse(self.mch_key)
            WeChatPayBaseClient._request = mock_request
            pay.client.order.query("1")

            # 有证书请求时带证书文件
            def mock_request(self, *args, **kwargs):
                that.assertTrue(self.mch_cert)
                that.assertTrue(self.mch_key)
                with open(self.mch_cert, "rb") as mch_cert_file,\
                    open(self.mch_key, "rb") as mch_key_file:
                    that.assertEqual(mch_cert_file.read(), mch_cert)
                    that.assertEqual(mch_key_file.read(), mch_key)
                return self.mch_cert, self.mch_key
            WeChatPayBaseClient._request = mock_request
            mch_cert_name, mch_key_name = cert_pay.client.order.query("1")

            # 请求结束后已移除证书文件
            self.assertFalse(os.path.exists(mch_cert_name))
            self.assertFalse(os.path.exists(mch_key_name))
        finally:
            WeChatPayBaseClient._request = origin_request
