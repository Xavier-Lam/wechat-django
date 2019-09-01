# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from contextlib import contextmanager

from django.http import response
from six.moves.urllib.parse import parse_qsl, urlparse
from six import text_type


@contextmanager
def mutable_GET(request):
    request.GET._mutable = True
    try:
        yield request.GET
    finally:
        request.GET._mutable = False


def get_ip(request):
    """获取客户端ip"""
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def auto_response(resp):
    if isinstance(resp, text_type):
        return response.HttpResponse(resp)
    elif isinstance(resp, dict):
        return response.JsonResponse(resp)
    else:
        return resp
