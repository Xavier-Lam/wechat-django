# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WeChatPayConfig(AppConfig):
    name = "wechat_django.pay"
    label = "wechat_django_pay"
    verbose_name = _("WeChat Pay")
    verbose_name_plural = _("WeChat Pay")

    def ready(self):
        # 处理微信支付相关权限
        import wechat_django.models.permission as base_pm
        from .models.permisssion import permissions, permission_required
        base_pm.permissions.update(permissions)
        base_pm.permission_required.update(permission_required)
