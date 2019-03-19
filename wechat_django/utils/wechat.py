# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re


def in_wechat(request):
    """判断是否时微信环境"""
    ua = request.META["HTTP_USER_AGENT"]
    return bool(re.search(r"micromessenger", ua, re.IGNORECASE))
