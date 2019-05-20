# -*- coding: utf-8 -*-

"""微信通知处理起"""

from __future__ import unicode_literals


def order_notify(request):
    xml = request.body
    if not xml:
        return
    # raises AttributeError
    pay = request.wechat.app.pay
    # raises InvalidSignatureException
    data = pay.client.parse_payment_result(xml)
