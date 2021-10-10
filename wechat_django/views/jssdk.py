import json
import time
from uuid import uuid4

from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from wechat_django.core.view import WeChatView
from wechat_django.exceptions import JSAPIError
from wechat_django.models.apps import OrdinaryApplication
from wechat_django.sites import default_site
from django.conf import settings


@default_site.register
class JSSDKConfig(WeChatView):
    include_application_classes = (OrdinaryApplication,)
    url_pattern = r"^jssdk.config.js$"
    url_name = "jsconfig"

    def get(self, request, *args, **kwargs):
        """jssdk配置"""
        url = request.META.get("HTTP_REFERER")
        if not url:
            raise JSAPIError(_("Losing Referer header"))

        js_api_list = request.GET.get("jsApiList", "").split(",")
        js_api_list = list(filter(None, js_api_list))
        debug = bool(settings.DEBUG and request.GET.get("debug"))

        try:
            ticket = request.wechat_app.jsapi_ticket
        except Exception:
            msg = _("Couldn't get jsapi ticket")
            request.wechat_app.logger("jssdk").warning(msg)
            raise JSAPIError(msg)
        noncestr = str(uuid4()).replace("-", "")
        timestamp = int(time.time())
        signature = request.wechat_app.client.jsapi.get_jsapi_signature(
            noncestr, ticket, timestamp, url)

        config = dict(
            debug=debug,
            appId=request.wechat_app.appid,
            timestamp=timestamp,
            nonceStr=noncestr,
            signature=signature,
            jsApiList=js_api_list
        )

        context = dict(config=json.dumps(config))

        return render(request, "wechat-django/jsconfig.js", context,
                      content_type="application/javascript")

    def handle_exception(self, exc):
        allowed_exceptions = (JSAPIError,)
        if isinstance(exc, allowed_exceptions):
            msg = "JSAPI config error: %s" % exc
            return HttpResponse('console.error("' + msg + '");',
                                content_type="application/javascript")
        super().handle_exception(exc)
