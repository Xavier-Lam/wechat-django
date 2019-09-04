# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
                return self.str2dt(value)
        except ValueError:
            pass
        return super(PayDateTimeField, self).to_python(value)

    def value_to_string(self, obj):
        rv = self.value_from_object(obj)
        return self.dt2str(rv)

    def value_from_object(self, obj):
        rv = super(PayDateTimeField, self).value_from_object(obj)
        return self.fixdt(rv)

    @classmethod
    def fixdt(cls, dt):
        return dt and dt.astimezone(cls._tz) or None

    @classmethod
    def dt2str(cls, dt):
        dt = cls.fixdt(dt)
        return dt.strftime(cls._format) if dt else ""

    @classmethod
    def str2dt(cls, s):
        if not s:
            return None
        dt = tz.datetime.strptime(s, cls._format)
        return tz.make_aware(dt, cls._tz)


class PayBooleanField(m.NullBooleanField):
    def to_python(self, value):
        if value in (True, "Y"):
            return True
        elif value in (False, "N"):
            return False
        return None

    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        if val is True:
            return "Y"
        elif val is False:
            return "N"
        return ""
