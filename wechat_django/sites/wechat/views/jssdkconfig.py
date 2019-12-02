# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import time
from uuid import uuid4

from django.conf import settings
from django.http import response
from django.shortcuts import render
from wechatpy.exceptions import WeChatClientException

from ..base import WeChatView
from ..sites import default_site


@default_site.register
class JSSDKConfig(WeChatView):
    url_name = "jsconfig"
    url_pattern = r"^wx.config.js"

    def get(self, request, appname):
        """jssdk配置"""
        from wechat_django.models import WeChatApp

        app = request.wechat.app
        if app.type != WeChatApp.Type.SERVICEAPP:
            return response.HttpResponseNotFound()

        js_api_list = request.GET.get("jsApiList", "").split(",")
        js_api_list = list(filter(None, js_api_list))
        debug = bool(settings.DEBUG and request.GET.get("debug"))

        client = app.client.jsapi

        url = request.META.get("HTTP_REFERER")
        if not url:
            return response.HttpResponseBadRequest()

        try:
            ticket = client.get_jsapi_ticket()
        except WeChatClientException as e:
            return response.HttpResponse('console.error("' + str(e) + '");',
                                         content_type="application/javascript")

        noncestr = str(uuid4()).replace("-", "")
        timestamp = int(time.time())
        signature = client.get_jsapi_signature(noncestr, ticket, timestamp,
                                               url)

        config = dict(
            debug=debug,
            appId=app.appid,
            timestamp=timestamp,
            nonceStr=noncestr,
            signature=signature,
            jsApiList=js_api_list
        )

        context = dict(
            config=json.dumps(config)
        )

        return render(request, "wechat-django/jsconfig.js", context,
                      content_type="application/javascript")
