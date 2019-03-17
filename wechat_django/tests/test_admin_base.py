# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..admin.base import WeChatModelAdmin
from ..models import appmethod, WeChatModel, WeChatUser
from ..sites.admin import wechat_admin_view, WeChatAdminSite
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
        make_request = wechat_admin_view(lambda o: o, site)
        request = make_request(self.rf().get("/?app_id=" + str(self.app.id)))
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
