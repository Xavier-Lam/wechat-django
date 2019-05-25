# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..admin.base import WeChatModelAdmin
from ..models import WeChatUser
from ..sites.admin import WeChatAdminSite
from .base import WeChatTestCase


class AdminBaseTestCase(WeChatTestCase):
    def test_get_request_params(self):
        """测试从admin的request请求中获取参数的方法"""
        pass

    def test_get_queryset(self):
        """测试queryset拿到的是本app的queryset"""
        openid = "openid"
        WeChatUser.objects.create(app=self.app, openid=openid)
        WeChatUser.objects.create(app=self.another_app, openid=openid)

        site = WeChatAdminSite()
        model_admin = WeChatModelAdmin(WeChatUser, site)
        request = self.rf().get("/")
        request.app_id = self.app.id
        request.app = self.app
        queryset = model_admin.get_queryset(request)
        self.assertEqual(
            queryset.filter(openid=openid).count(),
            1
        )
        self.assertEqual(
            queryset.count(),
            queryset.filter(app=self.app).count()
        )
        self.assertEqual(
            queryset.exclude(app=self.app).count(),
            0
        )

    def test_add_model(self):
        """测试新增数据时,会把appid附上"""
        pass
