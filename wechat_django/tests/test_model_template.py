# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..models import Template
from .base import WeChatTestCase


class TemplateTestCase(WeChatTestCase):
    def test_sync_miniprogram(self):
        """测试同步小程序模板"""
        pass

    def test_sync_service(self):
        """测试同步服务号模板"""
        pass

    def test_send_miniprogram(self):
        """测试发送小程序模板消息"""
        pass

    def test_send_service(self):
        """测试发送服务号模板消息"""
        pass
