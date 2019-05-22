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
from wechat_django.sites.wechat import BaseWeChatViewSet
from .exceptions import WeChatPayNotifyError


def make_response(msg=None):
    tpl = "<xml><return_msg><![CDATA[{msg}]]></return_msg><return_code><![CDATA[{code}]]></return_code></xml>"
    code = "FAIL" if msg else "SUCCESS"
    xml = tpl.format(code=code, msg=msg)
    return response.HttpResponse(xml, content_type="application/xml")


class NotifyViewSet(BaseWeChatViewSet):
    def notify_view(self, view):
        @csrf_exempt
        @wraps(view)
        def decorated_view(request, appname):
            try:
                pay, data = self._prepare(request, appname)
                return make_response(view(request, pay, data))
            except WeChatPayNotifyError as e:
                return make_response(e.msg)
            except:
                raise
                return make_response(_("Internal server error"))

        return decorated_view

    def _prepare(self, request, appname):
        """预处理请求"""
        if request.method != "POST":
            raise WeChatPayNotifyError(_("Method not allowed"))
        xml = request.body
        if not xml:
            raise WeChatPayNotifyError(_("Empty body"))

        try:
            app = self.site.app_queryset.prefetch_related("pay")\
                .get_by_name(appname)
        except WeChatApp.DoesNotExist as e:
            raise WeChatPayNotifyError(_("WeChat application not found"), e)

        if not app.abilities.pay:
            raise WeChatPayNotifyError(_("WeChat pay not configured"))

        try:
            return app.pay, app.pay.client.parse_payment_result(xml)
        except InvalidSignatureException as e:
            raise WeChatPayNotifyError(_("Invalid signature"), e)

    def get_urls(self):
        return [
            url(r"^pay/notify/", include([
                url(
                    r"^order$",
                    self.notify_view(self.order_notify),
                    name="order_notify"
                )
            ]))
        ]

    def order_notify(self, request, pay, data):
        out_trade_no = data["out_trade_no"]
        try:
            order = pay.orders.get(out_trade_no=out_trade_no)
        except ObjectDoesNotExist:
            return _("Order not found")
        order.update(data)
