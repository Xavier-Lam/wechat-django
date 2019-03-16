# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from django.conf.urls import url
from django.http import response
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from six import text_type

from . import url_patterns
from .models import WeChatApp, WeChatInfo
from .utils.web import auto_response

__all__ = ("message_handler", )


def message_handler(names_or_func=None):
    """自定义回复业务需加装该装饰器
    被装饰的自定义业务接收一个``wechat_django.models.WeChatMessageInfo``对象
    并且返回一个``wechatpy.replies.BaseReply``对象

    :param names_or_func: 允许使用该message_handler的appname 不填所有均允许
    :type names_or_func: str or list or tuple or callable

        @message_handler
        def custom_business(message):
            user = message.user
            # ...
            return TextReply("hello", message=message.message)

        @message_handler(("app_a", "app_b"))
        def app_ab_only_business(message):
            # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def decorated_view(message):
            return view_func(message)
        decorated_view.message_handler = names or True

        return decorated_view

    if isinstance(names_or_func, text_type):
        names = [names_or_func]
    elif callable(names_or_func):
        names = None
        return decorator(names_or_func)

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
