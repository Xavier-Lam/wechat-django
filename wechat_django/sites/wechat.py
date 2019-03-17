# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..models import WeChatApp


url_patterns = []


class WeChatSite(object):
    name = "wechat_django"

    def register(self, view):
        pass

    def unregister(self, view):
        pass

    def get_url(self):
        return url_patterns

    @property
    def urls(self):
        return self.get_url(), "wechat_django", self.name

    @property
    def app_queryset(self):
        """本站点能查询到的所有app"""
        return WeChatApp.objects.get_queryset()


default_site = WeChatSite()
"""默认微信站点,适用于一般状况"""
