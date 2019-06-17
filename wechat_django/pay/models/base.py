# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models as m
from django.utils import timezone as tz
import six

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
            if isinstance(value, six.text_type):
                dt = tz.datetime.strptime(value, self._format)
                return tz.make_aware(dt, self._tz)
        except ValueError:
            pass
        return super(PayDateTimeField, self).to_python(value)

    def value_to_string(self, obj):
        rv = self.value_from_object(obj)
        return rv.strftime(self._format) if val else ""

    def value_from_object(self, obj):
        rv = super(PayDateTimeField, self).value_from_object(obj)
        if rv:
            # 将服务器时区显式转换为上海区
            rv = rv.astimezone(self._tz)
        return rv


class PayBooleanField(m.NullBooleanField):
    def to_python(self, value):
        return value in (True, "Y") or None

    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        return "Y" if val else ""
