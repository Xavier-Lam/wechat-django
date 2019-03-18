# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .base import mock, WeChatTestCase


class UserTestCase(WeChatTestCase):
    def test_sync(self):
        """测试同步用户"""
        pass

    def test_fetch_users(self):
        """测试拉取用户"""
        pass

    def test_upsert_users(self):
        """测试插入或更新用户"""
        pass

    def test_update(self):
        """测试更新用户"""
        pass
