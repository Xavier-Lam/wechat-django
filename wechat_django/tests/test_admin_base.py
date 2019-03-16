# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..models import appmethod, WeChatModel
from .base import WeChatTestCase


class AdminBaseTestCase(WeChatTestCase):
    def test_admin_view(self):
        """测试admin view"""
        # 测试request能正确拿到appid
        pass

        # 测试响应有extra_context
        pass

    def test_get_request_params(self):
        """测试从admin的request请求中获取参数的方法"""
        pass

    def test_get_queryset(self):
        """测试queryset拿到的是本app的queryset"""
        pass
