# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import ContentType, Permission, User

from ..models import permission as pm, WeChatApp
from .bases import WeChatTestCase


class PermissionTestCase(WeChatTestCase):
    def test_permission_grant(self):
        """测试授权"""
        permissions = pm.list_permissions(self.app)
        # self.assertEqual(len(permissions), len(pm.permissions))

        # 测试相关权限是否一起授权
        for p in permissions:
            user = User.objects.create_user(p)
            perm = self._get_permission(p)
            user.user_permissions.add(perm)
            user.save()
            needed_perms = pm.get_require_permissions(self.app.name, p)
            codenames = list(map(lambda o: o.split(".")[1], needed_perms))
            for codename in codenames:
                self.assertHasPermission(user, codename)
        
        # 测试组授权
        pass

    def test_permissions(self):
        """测试权限"""
        pass

    def test_menus_permissions(self):
        """测试菜单权限"""
        pass
    
    def _get_permission(self, codename):
        return Permission.objects.get(
            codename=codename,
            content_type__app_label="wechat_django"
        )

    def assertHasPermission(self, user, permission):
        permission = self._get_permission(permission)
        self.assertIn(permission, user.user_permissions.all())
