# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import response as django_response
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from six import text_type

from wechat_django.rest_framework.views import APIView


class WeChatViewMixin(object):
    """微信相关业务的View"""

    app_queryset = None
    """取用WeChatApp实例时的默认查询集合,可重载为其他代理类查询集合"""

    url_pattern = None
    """注册的url pattern"""

    url_name = None
    """注册的url名"""

    def initialize_request(self, request, *args, **kwargs):
        request = super(WeChatViewMixin, self).initialize_request(
            request, *args, **kwargs)
        if not hasattr(request, "wechat"):
            request.wechat = self._create_wechat_info(
                request, *args, **kwargs)
        request.wechat = self._update_wechat_info(
            request, *args, **kwargs)
        return request

    def finalize_response(self, request, response, *args, **kwargs):
        if isinstance(response, text_type):
            response = django_response.HttpResponse(response)
        elif isinstance(response, dict):
            response = django_response.JsonResponse(response)
        return super(WeChatViewMixin, self).finalize_response(
            request, response, *args, **kwargs)

    @classmethod
    def as_view(cls, **initKwargs):
        from wechat_django.models import WeChatApp

        initKwargs["app_queryset"] = initKwargs.get("app_queryset")\
            or cls.app_queryset\
            or WeChatApp.objects
        view = super(WeChatViewMixin, cls).as_view(**initKwargs)
        return csrf_exempt(view)

    def _create_wechat_info(self, request, *args, **kwargs):
        """
        构建request的wechat属性
        :rtype: wechat_django.models.WeChatInfo
        """
        from wechat_django.models import WeChatInfo

        appname = self._get_appname(request, *args, **kwargs)
        return WeChatInfo(_request=request, _appname=appname,
                          _app_queryset=self.app_queryset)

    def _update_wechat_info(self, request, *args, **kwargs):
        """
        构建request的wechat属性
        :rtype: wechat_django.models.WeChatInfo
        """
        return request.wechat

    def _get_appname(self, request, *args, **kwargs):
        raise NotImplementedError()


class WeChatView(WeChatViewMixin, APIView):
    authentication_classes = tuple()
    permission_classes = tuple()

    def _get_appname(self, request, appname, *args, **kwargs):
        return appname


def wechat_view(regex, name, methods=None):
    """函数view装饰器,方便生成非class-based View"""

    methods = methods or ("GET",)

    def decorator(view):
        """
        :rtype: wechat_django.sites.wechat.WeChatView
        """
        attrs = {method.lower(): view for method in methods}
        attrs["url_pattern"] = regex
        attrs["url_name"] = name
        return type(str("WeChatView"), (WeChatView,), attrs)

    return decorator
