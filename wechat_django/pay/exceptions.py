# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class WeChatPayNotifyError(ValueError):
    def __init__(self, msg, inner=None):
        self.msg = msg
        self.inner = inner
