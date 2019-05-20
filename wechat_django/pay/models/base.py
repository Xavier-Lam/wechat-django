# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m
from django.utils import timezone as tz

from wechat_django.models.base import create_shortcut
from . import WeChatPay


paymethod = create_shortcut(WeChatPay)


class PayDateTimeField(m.DateTimeField):
    _format = "%Y%m%d%H%M%S"
    _tz = tz.pytz.timezone("Asia/Shanghai")

    def to_python(self, value):
        try:
            # 由微信字符串格式转换
            # TODO: 不知道会否有潜在时区问题
            dt = tz.datetime.strptime(value, self._format)
            return tz.make_aware(dt, self._tz)
        except ValueError:
            return super(PayDateTimeField, self).to_python(value)

    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        return val.astimezone(self._tz).strftime(self._format) if val else ""


class PayBooleanField(m.BooleanField):
    def to_python(self, value):
        return value in (True, "Y") or None

    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        return "Y" if val else ""
