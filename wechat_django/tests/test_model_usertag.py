# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .bases import WeChatTestCase


class UserTestCase(WeChatTestCase):
    def test_sync(self):
        """测试同步用户"""
        # 测试同步是否调用同步接口
        pass

    def test_change_tags(self):
        """测试标签变更"""
        # 测试用户添加标签
        pass

        # 测试用户加减标签
        pass

        # 测试用户加减标签异常
        pass

        # 测试标签添加用户
        pass

        # 测试标签加减用户
        pass

        # 测试标签加减用户异常
        pass

    def test_edit_tag(self):
        """测试标签的增删改查"""
        pass
