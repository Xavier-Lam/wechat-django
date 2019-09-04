# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, url


class WeChatSite(object):
    name = "wechat_django"

    base_url = r"^(?P<appname>[-_a-zA-Z\d]+)/"

    _registered_views = []

    app_queryset = None

    def register(self, cls):
        self._registered_views.append(cls)
        return cls

    def unregister(self, cls):
        self._registered_views.remove(cls)

    def get_urls(self):
        return [
            url(self.base_url, include([
                url(
                    cls.url_pattern,
                    self._create_view(cls),
                    name=cls.url_name
                )
            ]))
            for cls in self._registered_views
        ]

    @property
    def urls(self):
        return self.get_urls(), "wechat_django", self.name

    def get_app_queryset(self):
        """取用WeChatApp实例时的默认查询集合,可重载为其他代理类查询集合"""
        if not self.app_queryset:
            from wechat_django.models import WeChatApp

            return WeChatApp.objects

        return self.app_queryset

    def _create_view(self, cls):
        return cls.as_view(app_queryset=self.app_queryset)


default_site = WeChatSite()
"""默认微信站点,适用于一般状况"""
