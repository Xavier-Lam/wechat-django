# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps
import logging

from django.conf import settings
from django.conf.urls import include, url
from django.http import response
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests
from wechatpy.constants import WeChatErrorCode
from wechatpy.exceptions import WeChatClientException

from wechat_django import settings as wechat_settings


class WeChatSite(object):
    name = "wechat_django"

    _registered_views = []

    @property
    def app_queryset(self):
        """取用WeChatApp实例时的默认查询集合,可重载为其他代理类查询集合"""
        if not hasattr(self, "_app_queryset"):
            from wechat_django.models import WeChatApp

            return WeChatApp.objects

        return self._app_queryset

    def register(self, cls):
        self._registered_views.append(cls)
        return cls

    def unregister(self, cls):
        self._registered_views.remove(cls)

    def get_urls(self):
        return [
            url(r"^(?P<appname>[-_a-zA-Z\d]+)/", include([
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

    def _create_view(self, cls):
        return cls.as_view(app_queryset=getattr(self, "_app_queryset", None))


default_site = WeChatSite()
"""默认微信站点,适用于一般状况"""
