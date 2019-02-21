# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from django.conf.urls import url
from django.http import response
from django.utils.decorators import available_attrs
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from six import text_type

from . import url_patterns
from .models import WeChatApp, WeChatInfo
from .utils.web import auto_response

__all__ = ("message_handler", )


def message_handler(names=None):
    """自定义回复业务需加装该装饰器
    :params names: 允许使用该message_handler的appname 不填所有均允许
    """
    def decorator(view_func):
        # 防止副作用
        def wrapped_view(message):
            return view_func(message)

        wrapped_view.message_handler = names or True

        return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)

    if isinstance(names, text_type):
        names = [names]
    elif callable(names):
        return decorator(names)
    return decorator


def wechat_route(route, methods=None, name=""):
    """将view注册到<appname>/下
    :param route: 路由
    :param methods: 允许的方法
    :param name: 路由名 不填默认函数名
    """
    if not methods:
        methods = ("GET",)

    def decorator(func):
        func = csrf_exempt(func)
        func = require_http_methods(methods)(func)
        @wraps(func)
        def decorated_func(request, appname, *args, **kwargs):
            request = WeChatInfo.patch_request(request, appname)
            response = func(request, *args, **kwargs)
            return auto_response(response)

        pattern = url(
            r"^(?P<appname>[-_a-zA-Z\d]+)/" + route,
            decorated_func,
            name=name or func.__name__
        )
        url_patterns.append(pattern)
        return decorated_func
    return decorator
