# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid4 as uuid

from django.contrib.admin import site
from django.contrib.auth.models import ContentType, Permission, User
from django.urls import ResolverMatch

from ..models import permission as pm, WeChatApp
from ..pay.admin.payapp import WeChatPayInline, WeChatAppWithPayAdmin
from ..pay.models.app import WeChatPay
from .base import WeChatTestCase


class PermissionTestCase(WeChatTestCase):
    def test_permission_grant(self):
        """测试授权"""
        perm_names = pm.list_perm_names(self.app)
        self.assertEqual(len(perm_names), len(pm.permissions) + 1)

        # 测试相关权限是否一起授权
        for perm_name in perm_names:
            user = self._create_user(perm_name)
            needed_perms = pm.get_require_perm_names(self.app.name, perm_name)
            for permission in needed_perms:
                self.assertHasPermission(user, permission)

        # 测试组授权
        pass

    def test_index_menu(self):
        """测试首页菜单权限"""
        def assertMenuCorrect(perm_name, manage=False, apps=None):
            request = self.rf().get("/admin/")
            request.user = self._create_user(perm_name)

            app_dict = site._build_app_dict(request)

            if apps is None:
                apps = set([self.app.name])

            if manage:
                self.assertEqual(len(app_dict["wechat_django"]["models"]), 1)
            else:
                self.assertNotIn("wechat_django", app_dict)

            if apps:
                appnames = {
                    app["object_name"]
                    for app in app_dict["wechat_django_apps"]["models"]
                }
                self.assertEqual(apps, appnames)
            else:
                self.assertNotIn("wechat_django_apps", app_dict)

        perm_names = pm.list_perm_names(self.app)

        # 拥有全部权限
        all_perm_name = pm.get_perm_name(self.app)
        assertMenuCorrect(all_perm_name, manage=True)

        # 仅拥有管理权限
        manage_perm_name = pm.get_perm_name(self.app, "manage")
        manage_permission = manage_perm_name
        assertMenuCorrect(manage_permission, manage=True, apps=[])

        for perm_name in perm_names - set([manage_perm_name, all_perm_name]):
            assertMenuCorrect(perm_name, manage=False)

    def test_app_menu(self):
        """测试各微信号菜单权限"""
        def assertMenuCorrect(perm_name):
            request = self.rf().get("/admin/wechat_django/apps/" + str(self.app.id))
            request.user = self._create_user(perm_name)
            request.app = self.app
            request.app_id = self.app.id

            app_dict = site._build_app_dict(request, "wechat_django")
            permissions = pm.get_user_permissions(
                request.user, self.app, exclude_manage=True, exclude_sub=True)
            # 只有子权限是不会拥有菜单权限的 遂去掉子权限
            if permissions:
                all_permissions = {
                    model["object_name"].lower().replace("wechat", "")
                    for model in app_dict["models"]
                    if list(filter(None, model["perms"].values()))
                }
                self.assertEqual(permissions, all_permissions)
            else:
                self.assertIsNone(app_dict)

        for perm_name in pm.list_perm_names(self.app):
            assertMenuCorrect(perm_name)

    def assertHasPermission(self, user, permission):
        permission = pm.get_perm_model(permission)
        self.assertIn(permission, user.user_permissions.all())

    def _create_user(self, perm_name=None):
        user = User.objects.create_user(str(uuid()))
        if perm_name:
            user.user_permissions.add(pm.get_perm_model(perm_name))
            user.save()
        return user
