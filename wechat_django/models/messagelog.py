from django.db import models as m
from django.utils.translation import ugettext as _
from jsonfield import JSONField

from ..utils import enum2choices
from . import ReceiveMsgType, WeChatApp, WeChatUser

class MessageLog(m.Model):
    app = m.ForeignKey(WeChatApp)
    user = m.ForeignKey(WeChatUser)
    
    msg_id = m.BigIntegerField(_("msgid"))
    type = m.CharField(_("message type"), max_length=24,
        choices=enum2choices(ReceiveMsgType))
    content = JSONField()
    createtime = m.IntegerField(_("createtime"))

    created_at = m.DateTimeField(_("created_at"), auto_now_add=True)

    @classmethod
    def from_msg(cls, message):
        """
        :type app: WeChatApp
        :type message: wechatpy.messages.BaseMessage
        """
        content = {
            key: getattr(message, key)
            for key in message._fields
            if key not in ("id", "source", "target", "create_time", "time")
        }

        app = WeChatApp.get_by_appid(message.target)    
        return cls.objects.create(
            app=app,
            user=WeChatUser.get_by_openid(app, message.source),
            msg_id=message.id,
            type=message.type,
            createtime=message.time,
            content=content
        )