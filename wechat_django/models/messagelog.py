# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from ..utils.model import enum2choices
from . import Rule, WeChatApp, WeChatModel, WeChatUser


class MessageLog(WeChatModel):
    class Direct(object):
        USER2APP = False
        APP2USER = True

    app = m.ForeignKey(WeChatApp, on_delete=m.CASCADE)
    user = m.ForeignKey(WeChatUser, on_delete=m.CASCADE)

    msg_id = m.BigIntegerField(_("msgid"), null=True)
    type = m.CharField(
        _("message type"), max_length=24,
        choices=enum2choices(Rule.ReceiveMsgType))
    content = JSONField(_("content"))
    direct = m.BooleanField(_("direct"), default=Direct.USER2APP)

    raw = m.TextField(null=True, blank=True, default=None)

    created_at = m.DateTimeField(_("created at"), auto_now_add=True)

    class Meta(object):
        verbose_name = _("message log")
        verbose_name_plural = _("message logs")

        index_together = (("app", "created_at"),)
        ordering = ("app", "-created_at")

    @classmethod
    def from_message_info(cls, message_info):
        """
        :type message_info: wechat_django.models.WeChatMessageInfo
        """
        return cls._from_message(
            message_info.message,
            message_info.app,
            message_info.user,
            # message_info.raw
        )

    @classmethod
    def _from_message(cls, message, app, user, raw=""):
        content = {
            key: getattr(message, key)
            for key in message._fields
            if key not in ("id", "source", "target", "create_time", "time")
        }

        kwargs = dict(
            app=app,
            user=user,
            msg_id=message.id,
            type=message.type,
            content=content,
            raw=raw,
            direct=cls.Direct.USER2APP
        )
        if message.time:
            kwargs["created_at"] = timezone.datetime.fromtimestamp(
                message.time)
        return cls.objects.create(**kwargs)

    @classmethod
    def from_reply(cls, reply, app, user):
        """:type reply: wechatpy.replies.BaseReply"""
        content = {
            key: getattr(reply, key)
            for key in reply._fields
            if key not in ("id", "source", "target", "create_time", "time")
        }

        kwargs = dict(
            app=app,
            user=user,
            type=reply.type,
            content=content,
            # raw=reply.render(),
            direct=cls.Direct.APP2USER
        )
        if reply.time:
            kwargs["created_at"] = timezone.datetime.fromtimestamp(
                reply.time)
        return cls.objects.create(**kwargs)
