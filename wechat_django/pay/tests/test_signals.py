# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .. import signals
from .base import WeChatPayTestCase


class SignalTestCase(WeChatPayTestCase):
    def test_order_updated(self):
        """测试订单更新信号"""
        pass
