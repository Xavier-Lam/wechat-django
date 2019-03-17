# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps
import logging

from django.conf.urls import url
from django.http import response
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests
from wechatpy.constants import WeChatErrorCode
from wechatpy.exceptions import WeChatClientException

from ..handler import handler
from ..models import WeChatApp, WeChatInfo
from ..utils.web import auto_response


class WeChatSite(object):
    name = "wechat_django"

    def wechat_view(self, view, methods=None):
        """通过wechat_view装饰的view
        request变为``wechat_django.models.request.WeChatHttpRequest``实例
        request中将带有``wechat_django.models.WeChatInfo``类型的wechat属性
        """
        methods = methods or ("GET",)

        @wraps(view)
        def decorated_view(request, appname, *args, **kwargs):
            # TODO: patch request应该移到site里来
            request = WeChatInfo.patch_request(request, appname)
            response = view(request, *args, **kwargs)
            return auto_response(response)

        rv = csrf_exempt(decorated_view)
        rv = require_http_methods(methods)(rv)

        return rv

    def get_url(self):
        route = lambda pattern: r"^(?P<appname>[-_a-zA-Z\d]+)/" + pattern

        return [
            url(
                route(r"materials/(?P<media_id>[_a-zA-Z\d]+)$"),
                self.wechat_view(self.material_proxy),
                name="material_proxy"
            ),
            url(
                route(r"$"),
                self.wechat_view(handler, ("GET", "POST")),
                name="handler"
            )
        ]

    @property
    def urls(self):
        return self.get_url(), "wechat_django", self.name

    @property
    def app_queryset(self):
        """本站点能查询到的所有app"""
        return WeChatApp.objects.get_queryset()

    def material_proxy(request, media_id):
        """代理下载微信的素材"""
        app = request.wechat.app
        try:
            resp = app.client.material.get(media_id)
        except WeChatClientException as e:
            if e.errcode == WeChatErrorCode.INVALID_MEDIA_ID:
                return response.HttpResponseNotFound()
            # TODO: 改成方法 views改site
            logging.getLogger("wechat.views.{0}".format(app.name)).warning(
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


default_site = WeChatSite()
"""默认微信站点,适用于一般状况"""
