# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechat_django.rest_framework.permissions import BasePermission


class StaffOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user and hasattr(request.user, "is_staff")\
            and request.user.is_staff
