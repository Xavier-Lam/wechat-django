# -*- coding: utf-8 -*-

"""微信通知处理器"""

from __future__ import unicode_literals

from functools import wraps

from django.conf.urls import include, url
from django.core.exceptions import ObjectDoesNotExist
from django.http import response
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from wechatpy.exceptions import InvalidSignatureException

from wechat_django.models import WeChatApp
from wechat_django.sites.wechat import default_site, WeChatView
from .exceptions import WeChatPayNotifyError


@default_site.register
class NotifyView(WeChatView):
    url_pattern = r"^pay/(?P<payname>[-_a-zA-Z\d]+)/notify/"
    url_name = "order_notify"

    def finalize_response(self, request, msg, *args, **kwargs):
        tpl = "<xml><return_msg><![CDATA[{msg}]]></return_msg><return_code><![CDATA[{code}]]></return_code></xml>"  # noqa
        code = "FAIL" if msg else "SUCCESS"
        xml = tpl.format(code=code, msg=msg or "OK")
        return response.HttpResponse(xml, content_type="application/xml")

    def handle_exception(self, exc):
        if isinstance(exc, WeChatPayNotifyError):
            return exc.msg
        log = self.request.wechat.app.logger("handler")
        log.exception("WeChat Pay notify server error")
        return _("Internal server error")

    def post(self, request, appname, payname):
        pay, data = self._prepare(request, payname)
        out_trade_no = data["out_trade_no"]
        try:
            order = pay.orders.get(out_trade_no=out_trade_no)
        except ObjectDoesNotExist:
            return _("Order not found")
        data["trade_state"] = data["result_code"]
        order.update(data)

    def _prepare(self, request, payname):
        xml = request.body
        if not xml:
            raise WeChatPayNotifyError(_("Empty body"))

        try:
            pay = request.wechat.app.pays.get(name=payname)
        except ObjectDoesNotExist as e:
            raise WeChatPayNotifyError(_("WeChat Pay not found"), e)
        try:
            return pay, pay.client.parse_payment_result(xml)
        except InvalidSignatureException as e:
            raise WeChatPayNotifyError(_("Invalid signature"), e)
