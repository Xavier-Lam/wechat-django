# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.db import models as m
from django.utils.translation import ugettext as _
from jsonfield import JSONField
from wechatpy.events import BaseEvent

from ..utils.admin import enum2choices
from . import MessageHandler, ReceiveMsgType


class Rule(m.Model):
    class Type(object):
        MSGTYPE = "msg_type"  # 类型匹配
        EVENT = "event"  # 事件
        EVENTKEY = "eventkey"  # 指定事件
        CONTAIN = "contain"  # 包含
        EQUAL = "equal"  # 匹配
        REGEX = "regex"  # 正则
        ALL = "all"  # 全部

    handler = m.ForeignKey(MessageHandler, on_delete=m.CASCADE,
        related_name="rules", null=False)

    type = m.CharField(_("type"), max_length=16,
        choices=enum2choices(Type))  # 规则类型
    rule = JSONField(blank=True)  # 规则内容

    weight = m.IntegerField(_("weight"), default=0, null=False)
    created = m.DateTimeField(_("created"), auto_now_add=True)

    class Meta:
        ordering = ("-weight", )

    def match(self, message):
        """
        :type message: wechatpy.messages.BaseMessage
        """
        s_eq = lambda a, b: a.lower() == b.lower()

        if self.type == self.Type.ALL:
            return True
        elif self.type == self.Type.MSGTYPE:
            return message.type == self.rule["msg_type"]
        elif self.type == self.Type.EVENT:
            return (message.type == ReceiveMsgType.EVENT
                and s_eq(message.event, self.rule["event"]))
        elif self.type == self.Type.EVENTKEY:
            return (message.type == ReceiveMsgType.EVENT
                and s_eq(message.event, self.rule["event"])
                and hasattr(message, "key")
                and message.key == self.rule["key"])
        elif self.type == self.Type.CONTAIN:
            return (message.type == ReceiveMsgType.TEXT
                and self.rule["pattern"] in message.content)
        elif self.type == self.Type.EQUAL:
            return (message.type == ReceiveMsgType.TEXT
                and message.content == self.rule["pattern"])
        elif self.type == self.Type.REGEX:
            return (message.type == ReceiveMsgType.TEXT
                and re.search(self.rule["pattern"], message.content))
        return False

    @classmethod
    def from_mp(cls, data, handler=None):
        return cls(
            handler=handler,
            type=data["match_mode"],
            rule=dict(pattern=data["content"])
        )

    def __str__(self):
        if hasattr(self, "handler") and self.handler is not None:
            return self.handler.name
        return "<Rule: {0}>".format(self.type)
