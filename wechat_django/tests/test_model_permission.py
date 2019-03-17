# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import ContentType, Permission

from ..models import permission as p, WeChatApp
from .base import WeChatTestCase


class PermissionTestCase(WeChatTestCase):
    def test_migrate(self):
        """测试迁移权限"""
        name = "debug"
        p.permissions[name] = "debug %(appname)s permission"
        # 测试upgrade
        p.upgrade_perms((name,))

        content_type = ContentType.objects.get_for_model(WeChatApp)
        Permission.objects.get(
            content_type=content_type,
            codename=p.get_perm_name(self.app, name)
        )

        # 测试downgrade
        p.downgrade_perms((name,))
        count = Permission.objects.filter(
            content_type=content_type,
            codename=p.get_perm_name(self.app, name)
        ).count()
        self.assertEqual(count, 0)
