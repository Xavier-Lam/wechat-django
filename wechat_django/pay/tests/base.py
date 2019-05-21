# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os
try:
    from unittest import mock
except ImportError:
    import mock

from django.test import RequestFactory, TestCase

from wechat_django.models import WeChatApp
from wechat_django.tests.base import WeChatTestCaseBase
from ..models import WeChatPay


class WeChatPayTestCase(WeChatTestCaseBase):
    @classmethod
    def setUpTestData(cls):
        super(WeChatPayTestCase, cls).setUpTestData()
        pay = WeChatPay(mch_id="mch_id", api_key="api_key")
        WeChatApp.objects.create(title="pay", name="pay", appid="appid",
            appsecret="secret", pay=pay)
        WeChatApp.objects.create(title="miniprogram", name="miniprogram",
            appid="miniprogram", appsecret="secret",
            type=WeChatApp.Type.MINIPROGRAM, pay=pay)

    def setUp(self):
        self.app = WeChatApp.objects.get_by_name("pay")
        # self.pay = self.app.pay
        self.miniprogram = WeChatApp.objects.get_by_name("miniprogram")
