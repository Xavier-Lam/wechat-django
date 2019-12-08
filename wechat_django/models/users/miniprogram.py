# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.functional import cached_property

from .base import ProxyField, WeChatUser


class MiniProgramUser(WeChatUser):
    """小程序用户"""

    avatarurl = ProxyField("headimgurl")

    @cached_property
    def session(self):
        return self.sessions.first()

    class Meta(object):
        proxy = True
