# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m
from django.utils.translation import ugettext as _
from jsonfield import JSONField

from ..utils.admin import enum2choices
from . import Rule, WeChatApp, WeChatUser


class MessageLog(m.Model):
    class Flag(object):
        LOG_REQUEST = 0x01
        LOG_REQUEST_RAW = 0x02
        LOG_RESPONSE = 0x04
        LOG_RESPONSE_RAW = 0x08

    app = m.ForeignKey(WeChatApp, on_delete=m.CASCADE)
    user = m.ForeignKey(WeChatUser, on_delete=m.CASCADE)

    msg_id = m.BigIntegerField(_("msgid"))
    type = m.CharField(_("message type"), max_length=24,
        choices=enum2choices(Rule.ReceiveMsgType))
    content = JSONField()
    # raw = m.TextField()
    createtime = m.IntegerField(_("createtime"))

    created = m.DateTimeField(_("created_at"), auto_now_add=True)

    class Meta(object):
        index_together = (("app", "created"),)
        ordering = ("app", "-created")

    @classmethod
    def from_msg(cls, message, app=None):
        """
        :type message: wechatpy.messages.BaseMessage
        :type app: WeChatApp
        """
        # TODO: 是否记录原始记录
        content = {
            key: getattr(message, key)
            for key in message._fields
            if key not in ("id", "source", "target", "create_time", "time")
        }

        return cls.objects.create(
            app=app,
            user=WeChatUser.get_by_openid(app, message.source),
            msg_id=message.id,
            type=message.type,
            createtime=message.time,
            content=content
        )
