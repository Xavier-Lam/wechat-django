# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from rest_framework.permissions import BasePermission
except ImportError:
    BasePermission = object


class WeChatAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return bool(request.wechat.openid)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
