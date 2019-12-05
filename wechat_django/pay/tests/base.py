# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from unittest import mock
except ImportError:
    import mock

from wechat_django.constants import AppType
from wechat_django.models import WeChatApp
from wechat_django.tests.base import WeChatTestCaseBase
from ..models import WeChatPay, WeChatSubPay


class WeChatPayTestCase(WeChatTestCaseBase):
    @classmethod
    def setUpTestData(cls):
        super(WeChatPayTestCase, cls).setUpTestData()
        app = WeChatApp.objects.create(
            title="pay", name="pay", appid="appid", appsecret="secret")
        pay = WeChatPay.objects.create(
            app=app, mch_id="mch_id", api_key="api_key", mch_cert=b"mch_cert",
            mch_key=b"mch_key")

        app_nocert = WeChatApp.objects.create(
            title="pay_nocert", name="pay_nocert", appid="pay_nocert",
            appsecret="secret")
        pay = WeChatPay.objects.create(
            app=app_nocert, mch_id="mch_id", api_key="api_key")

        miniprogram = WeChatApp.objects.create(
            title="miniprogram", name="miniprogram", appid="miniprogram",
            appsecret="secret", type=AppType.MINIPROGRAM)
        pay = WeChatPay.objects.create(
            app=miniprogram, mch_id="mch_id", api_key="api_key",
            mch_cert=b"mch_cert", mch_key=b"mch_key")

        app_sub = WeChatApp.objects.create(title="pay_sub", name="pay_sub",
                                           appid="pay_sub_appid",
                                           type=AppType.PAYPARTNER)
        app_sub.mch_id = "mch_id"
        app_sub.api_key = "api_key"
        app_sub.save()
        WeChatSubPay.objects.create(app=app_sub, sub_mch_id="sub_mch_id",
                                    sub_appid=app.appid)

    def setUp(self):
        self.app = WeChatApp.objects.get_by_name("pay")
        self.miniprogram = WeChatApp.objects.get_by_name("miniprogram")
        self.app_sub = WeChatApp.objects.get_by_name("pay_sub")
        self.app_nocert = WeChatApp.objects.get_by_name("pay_nocert")
