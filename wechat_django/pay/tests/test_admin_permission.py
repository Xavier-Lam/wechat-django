# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid4 as uuid

from django.contrib.admin import site
from django.contrib.auth.models import ContentType, Permission, User
from django.urls import ResolverMatch

from wechat_django.models import permission as pm, WeChatApp
from wechat_django.pay import admin as pay_admin
from wechat_django.pay.admin.payapp import WeChatPayInline, WeChatAppWithPayAdmin
from wechat_django.pay import models as pay_models
from .base import WeChatPayTestCase


class PermissionTestCase(WeChatPayTestCase):
    def test_app_menu(self):
        """测试各微信号菜单权限"""
        request = self.rf().get("/admin/wechat_django/%s/" % self.app.id)
        request.app = self.app
        n_user = self._create_user()

        permission_map = dict(
            pay_order=(pay_models.UnifiedOrder, pay_admin.order.OrderAdmin)
        )
        for permission, ma in permission_map.items():
            perm_name = pm.get_perm_name(self.app, permission)
            Model, Admin = ma
            p_user = self._create_user(perm_name)
            request.user = p_user
            admin = Admin(Model, site)
            perms = admin.get_model_perms(request)
            self.assertTrue(perms["change"])
            request.user = n_user
            perms = admin.get_model_perms(request)
            self.assertFalse(perms.get("change"))

    def test_pay_manage(self):
        """测试支付权限"""
        perm_name = pm.get_perm_name(self.app, "pay_manage")
        p_user = self._create_user(perm_name)
        n_user = self._create_user()
        admin = WeChatAppWithPayAdmin(WeChatApp, site)

        request = self.rf().get("/admin/wechat_django/apps?id=" + str(self.app.id))
        request.user = p_user
        inlines = admin.get_inline_instances(request, self.app)
        self.assertTrue(list(filter(
            lambda o: isinstance(o, WeChatPayInline), inlines)))

        request.user = n_user
        inlines = admin.get_inline_instances(request, self.app)
        self.assertFalse(list(filter(
            lambda o: isinstance(o, WeChatPayInline), inlines)))

    def _create_user(self, perm_name=None):
        user = User.objects.create_user(str(uuid()))
        if perm_name:
            user.user_permissions.add(pm.get_perm_model(perm_name))
            user.save()
        return user
