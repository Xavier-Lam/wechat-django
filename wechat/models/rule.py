import re

from django.db import models
from django.utils.translation import ugettext as _
from jsonfield import JSONField
from wechatpy.events import BaseEvent

from .. import utils
from . import MessageHandler, ReceiveMsgType

class Rule(models.Model):
    class Type(object):
        MSGTYPE = "msg_type" # 类型匹配
        EVENT = "event" # 事件
        EVENTKEY = "eventkey" # 指定事件
        CONTAIN = "contain" # 包含
        EQUAL = "equal" # 匹配
        REGEX = "regex" # 正则
        ALL = "all" # 全部

    handler = models.ForeignKey(MessageHandler, on_delete=models.CASCADE, 
        related_name="rules", null=False)

    type = models.CharField(_("type"), max_length=16,
        choices=utils.enum2choices(Type)) # 规则类型
    rule = JSONField(blank=True) # 规则内容

    weight = models.IntegerField(_("weight"), default=0, null=False)
    created = models.DateTimeField(_("created"), auto_now_add=True)

    class Meta:
        ordering = ("-weight", )

    def match(self, message):
        """
        :type message: wechatpy.messages.BaseMessage
        """
        if self.type == self.Type.ALL:
            return True
        elif self.type == self.Type.MSGTYPE:
            return message.type == self.rule
        elif self.type == self.Type.EVENT:
            return (message.type == ReceiveMsgType.EVENT
                and message.event == self.rule)
        elif self.type == self.Type.EVENTKEY:
            return (message.type == ReceiveMsgType.EVENT
                and message.event == self.rule["event"]
                and message.key == self.rule["key"])
        elif self.type == self.Type.CONTAIN:
            return (message.type == ReceiveMsgType.TEXT 
                and message.content.find(self.rule) >= -1)
        elif self.type == self.Type.EQUAL:
            return (message.type == ReceiveMsgType.TEXT 
                and message.content == self.rule)
        elif self.type == self.Type.REGEX:
            return (message.type == ReceiveMsgType.TEXT 
                and re.search(self.rule, message.content))
        return False

    @classmethod
    def from_mp(cls, data):
        return cls(
            type=data["match_mode"],
            rule=data["content"]
        )