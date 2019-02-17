# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six.moves.urllib.parse import parse_qsl, urlparse


def get_ip(request):
    """获取客户端ip"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_params(request, key, default=None):
    """获取url上的参数"""
    if request.is_ajax():
        try:
            referrer = request.META["HTTP_REFERER"]
            query = dict(parse_qsl(urlparse(referrer).query))
            return query.get(key, default)
        except:
            return default
    else:
        return request.GET.get(key, default)