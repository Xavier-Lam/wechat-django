# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps
import logging

from django.conf import settings
from django.conf.urls import include, url
from django.http import response
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests
from wechatpy.constants import WeChatErrorCode
from wechatpy.exceptions import WeChatClientException

from .. import settings as wechat_settings
from ..models import WeChatApp, WeChatInfo
from ..utils.web import auto_response


def patch_request(request, appname=None, cls=None, **kwargs):
    cls = cls or WeChatInfo
    appname = appname or request.wechat.appname
    wechat = cls(_appname=appname, _request=request)
    for key, value in kwargs.items():
        setattr(wechat, "_" + key, value)
    request.wechat = wechat
    return request


class WeChatSite(object):
    name = "wechat_django"
    _registered_viewsets = []

    def register(self, cls):
        viewset = cls(self)
        self._registered_viewsets.append(viewset)

    def unregister(self, cls):
        viewset = self.get_registered(cls)
        viewset and self._registered_viewsets.remove(viewset)

    def get_registered(self, cls):
        for viewset in self._registered_viewsets:
            if isinstance(viewset, cls):
                return viewset

    def get_urls(self):
        return [
            url(r"^(?P<appname>[-_a-zA-Z\d]+)/", include(viewset.urls))
            for viewset in self._registered_viewsets
        ]

    @property
    def urls(self):
        return self.get_urls(), "wechat_django", self.name

    @property
    def app_queryset(self):
        """本站点能查询到的所有app
        :rtype: wechat_django.models.app.WeChatAppQuerySet
        """
        return WeChatApp.objects.get_queryset()


class BaseWeChatViewSet(object):
    def __init__(self, site):
        """:type site: WeChatSite"""
        self.site = site

    def get_urls(self):
        raise NotImplementedError()

    @property
    def urls(self):
        return self.get_urls()


class WeChatViewSet(BaseWeChatViewSet):
    def wechat_view(self, view, methods=None):
        """通过wechat_view装饰的view
        request变为``wechat_django.requests.WeChatHttpRequest``实例
        request中将带有``wechat_django.models.WeChatInfo``类型的wechat属性
        """
        methods = methods or ("GET",)

        @wraps(view)
        def decorated_view(request, appname, *args, **kwargs):
            # 只允许queryset内的appname访问本站点
            try:
                app = self.site.app_queryset.get_by_name(appname)
            except WeChatApp.DoesNotExist:
                return response.HttpResponseNotFound()

            request = patch_request(request, appname, _app=app)
            resp = view(request, *args, **kwargs)
            return auto_response(resp)

        rv = csrf_exempt(decorated_view)
        rv = require_http_methods(methods)(rv)

        return rv

    def get_urls(self):
        from ..handler import handler

        return [
            url(
                r"^materials/(?P<media_id>[-_a-zA-Z\d]+)$",
                self.wechat_view(self.material_proxy),
                name="material_proxy"
            ),
            url(
                r"^$",
                self.wechat_view(handler, ("GET", "POST")),
                name="handler"
            )
        ]

    def material_proxy(self, request, media_id):
        """代理下载微信的素材"""
        app = request.wechat.app
        try:
            resp = app.client.material.get(media_id)
        except WeChatClientException as e:
            if e.errcode == WeChatErrorCode.INVALID_MEDIA_ID:
                return response.HttpResponseNotFound()
            self.get_logger(request.wechat.appname).warning(
                "an exception occurred when download material",
                exc_info=True)
            return response.HttpResponseServerError()
        if not isinstance(resp, requests.Response):
            # 暂时只处理image和voice
            return response.HttpResponseNotFound()

        rv = response.FileResponse(resp.content)
        for k, v in resp.headers.items():
            if k.lower().startswith("content-"):
                rv[k] = v
        return rv

    def get_logger(self, appname):
        return logging.getLogger("wechat.site.{0}".format(appname))


default_site = WeChatSite()
"""默认微信站点,适用于一般状况"""
default_site.register(WeChatViewSet)
