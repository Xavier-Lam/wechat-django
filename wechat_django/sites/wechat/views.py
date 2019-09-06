# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import response
import requests
from wechatpy.constants import WeChatErrorCode
from wechatpy.exceptions import WeChatClientException

from .base import WeChatView
from .permissions import StaffOnly
from .sites import default_site


@default_site.register
class MaterialProxy(WeChatView):
    url_name = "material_proxy"
    url_pattern = r"^materials/(?P<media_id>[-_a-zA-Z\d]+)$"

    permissions = (StaffOnly,)  # 只有在后台允许访问素材代理

    def get(self, request, appname, media_id):
        """代理下载微信的素材"""
        app = request.wechat.app
        try:
            resp = app.download_material(media_id)
        except WeChatClientException as e:
            if e.errcode == WeChatErrorCode.INVALID_MEDIA_ID:
                return response.HttpResponseNotFound()
            app.logger("site").warning(
                "an exception occurred when download material",
                exc_info=True)
            raise
        if not isinstance(resp, requests.Response):
            # 暂时只处理image和voice
            return response.HttpResponseNotFound()

        rv = response.FileResponse(resp.content)
        for k, v in resp.headers.items():
            if k.lower().startswith("content-"):
                rv[k] = v
        return rv
