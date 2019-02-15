# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import response

from ..decorators import wechat_route
from .bases import WeChatTestCase


class UtilDecoratorTestCase(WeChatTestCase):
    def test_wechat_route(self):
        """测试wechat_route 装饰器"""
        def test(request, *args, **kwargs):
            return response.HttpResponse(status=204)
