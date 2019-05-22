# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from unittest import mock
except ImportError:
    import mock

from wechat_django.models import WeChatApp
from wechat_django.tests.base import WeChatTestCaseBase
from ..models import WeChatPay


class WeChatPayTestCase(WeChatTestCaseBase):
    @classmethod
    def setUpTestData(cls):
        super(WeChatPayTestCase, cls).setUpTestData()
        app = WeChatApp.objects.create(
            title="pay", name="pay", appid="appid", appsecret="secret")
        app.pay = WeChatPay.objects.create(
            mch_id="mch_id", api_key="api_key", mch_cert=b"mch_cert",
            mch_key=b"mch_key")

        app_nocert = WeChatApp.objects.create(
            title="pay_nocert", name="pay_nocert", appid="pay_nocert",
            appsecret="secret")
        app_nocert.pay = WeChatPay.objects.create(
            mch_id="mch_id", api_key="api_key")

        miniprogram = WeChatApp.objects.create(
            title="miniprogram", name="miniprogram", appid="miniprogram",
            appsecret="secret", type=WeChatApp.Type.MINIPROGRAM)
        miniprogram.pay = WeChatPay.objects.create(
            mch_id="mch_id", api_key="api_key", mch_cert=b"mch_cert",
            mch_key=b"mch_key")

        app_sub = WeChatApp.objects.create(
            title="pay_sub", name="pay_sub", appid="pay_sub_appid",
            appsecret="secret")
        app_sub.pay = WeChatPay.objects.create(
            mch_id="mch_id", api_key="api_key", sub_mch_id="sub_mch_id",
            mch_app_id=app.appid, mch_cert=b"mch_cert",
            mch_key=b"mch_key")

    def setUp(self):
        self.app = WeChatApp.objects.get_by_name("pay")
        self.miniprogram = WeChatApp.objects.get_by_name("miniprogram")
        self.app_sub = WeChatApp.objects.get_by_name("pay_sub")
        self.app_nocert = WeChatApp.objects.get_by_name("pay_nocert")
