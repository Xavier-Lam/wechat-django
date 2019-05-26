# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings

PAYCLIENT = getattr(
    settings, "WECHAT_PAYCLIENT", "wechat_django.pay.client.WeChatPayClient")
