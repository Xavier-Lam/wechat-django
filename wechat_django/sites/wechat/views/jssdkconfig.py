# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import time
from uuid import uuid4

from django.conf import settings
from django.http.response import Http404, HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from wechatpy.exceptions import WeChatClientException

from wechat_django.constants import AppType
from wechat_django.exceptions import JSAPIError
from ..base import WeChatView
from ..sites import default_site


@default_site.register
class JSSDKConfig(WeChatView):
    url_name = "jsconfig"
    url_pattern = r"^wx.config.js"

    def initial(self, request, appname):
        if not request.wechat.app.type & AppType.SERVICEAPP:
            raise Http404

        url = request.META.get("HTTP_REFERER")
        if not url:
            raise JSAPIError(_("Referer header lost"))

    def get(self, request, appname):
        """jssdk配置"""
        js_api_list = request.GET.get("jsApiList", "").split(",")
        js_api_list = list(filter(None, js_api_list))
        debug = bool(settings.DEBUG and request.GET.get("debug"))

        app = request.wechat.app
        ticket = app.client.jsapi.get_jsapi_ticket()
        noncestr = str(uuid4()).replace("-", "")
        timestamp = int(time.time())
        url = request.META["HTTP_REFERER"]
        signature = app.client.jsapi.get_jsapi_signature(noncestr, ticket,
                                                         timestamp, url)

        config = dict(
            debug=debug,
            appId=app.appid,
            timestamp=timestamp,
            nonceStr=noncestr,
            signature=signature,
            jsApiList=js_api_list
        )

        context = dict(config=json.dumps(config))

        return render(request, "wechat-django/jsconfig.js", context,
                      content_type="application/javascript")

    def handle_exception(self, exc):
        allowed_exceptions = (WeChatClientException, JSAPIError)
        if isinstance(exc, allowed_exceptions):
            msg = "JSAPI config error: %s" % exc
            return HttpResponse('console.error("' + msg + '");',
                                content_type="application/javascript")
        raise exc
