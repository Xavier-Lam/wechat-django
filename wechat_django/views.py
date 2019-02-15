# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.http import response
import requests
from wechatpy.constants import WeChatErrorCode
from wechatpy.exceptions import WeChatClientException

from .decorators import wechat_route

__all__ = ("material_proxy", )

@wechat_route(r"materials/(?P<media_id>[_a-zA-Z\d]+)$")
def material_proxy(request, media_id):
    """代理下载微信的素材"""
    app = request.wechat.app
    try:
        resp = app.client.material.get(media_id)
    except WeChatClientException as e:
        if e.errcode == WeChatErrorCode.INVALID_MEDIA_ID:
            return response.HttpResponseNotFound()
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
