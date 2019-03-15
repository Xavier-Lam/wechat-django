# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m


def appmethod(func):
    """可以把方法注册到WeChatApp上的语法糖"""
    return func


class WeChatModel(m.Model):
    class Meta(object):
        abstract = True
