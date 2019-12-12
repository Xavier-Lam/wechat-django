# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.functional import cached_property

from wechat_django.models import MiniProgramApp
from .base import ProxyField, WeChatUser
from .session import MiniProgramSession


@MiniProgramApp.register_model
class MiniProgramUser(WeChatUser):
    """小程序用户"""

    avatarurl = ProxyField("headimgurl")

    @property
    def sessions(self):
        queryset = super(MiniProgramUser, self).sessions
        queryset.model = MiniProgramSession
        return queryset

    @cached_property
    def session(self):
        return self.sessions.first()

    class Meta(object):
        proxy = True
