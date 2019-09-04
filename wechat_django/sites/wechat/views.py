# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import response
from wechatpy.constants import WeChatErrorCode
from wechatpy.exceptions import WeChatClientException

from .base import wechat_view
from .sites import default_site


@default_site.register
@wechat_view(r"^materials/(?P<media_id>[-_a-zA-Z\d]+)$",
             name="material_proxy")
def material_proxy(request, media_id):
    """代理下载微信的素材"""
    app = request.wechat.app
    try:
        resp = app.client.material.get(media_id)
    except WeChatClientException as e:
        if e.errcode == WeChatErrorCode.INVALID_MEDIA_ID:
            return response.HttpResponseNotFound()
        app.logger("site").warning(
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
