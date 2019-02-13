#encoding: utf-8
from django.db import models as m
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _
from jsonfield import JSONField
import requests
from wechatpy import replies

from ..utils.admin import enum2choices
from . import (Article, Material, MessageHandler, MsgType as BaseMsgType,
    WeChatMessage)


class Reply(m.Model):
    class MsgType(BaseMsgType):  # 响应
        MUSIC = "music"
        NEWS = "news"

        # 自定义业务
        # LOG = "log"
        CUSTOM = "custom"
        FORWARD = "forward"  # 转发

    handler = m.ForeignKey(MessageHandler, on_delete=m.CASCADE,
        related_name="replies")

    msg_type = m.CharField(_("type"), max_length=16,
        choices=enum2choices(MsgType))
    content = JSONField()

    @property
    def app(self):
        return self.handler.app

    def send(self, message):
        """主动回复
        :type message: wechatpy.messages.BaseMessage
        """
        reply = self.reply(message)
        funcname, kwargs = self.reply2send(reply)
        return funcname and getattr(self.app.client.message, funcname)(**kwargs)

    def reply(self, message):
        """被动回复
        :type message: wechatpy.messages.BaseMessage
        :rtype: wechatpy.replies.BaseReply
        """
        if self.msg_type == self.MsgType.FORWARD:
            # 转发业务
            reply = self.reply_forward(message)
        elif self.msg_type == self.MsgType.CUSTOM:
            # 自定义业务
            reply = self.reply_custom(message)
        else:
            # 正常回复类型
            reply = self.normal_reply(message)
        return reply

    def reply_forward(self, message):
        resp = requests.post(self.content["url"], message.raw,
            params=message.request.GET, timeout=4.5)
        resp.raise_for_status()
        return replies.deserialize_reply(resp.content)

    def reply_custom(self, message):
        try:
            func = import_string(self.content["program"])
        except:
            raise NotImplementedError("custom bussiness not found")
        else:
            if not hasattr(func, "message_handler"):
                e = "handler must be decorated by wechat_django.decorators.message_handler"
                raise ValueError(e)
            elif (hasattr(func.message_handler, "__contains__") and
                self.app.name not in func.message_handler):
                e = "this handler cannot assigned to {0}".format(self.app.name)
                raise ValueError(e)
            reply = func(WeChatMessage(self.app, message))
            if not reply:
                return ""
            elif isinstance(reply, str):
                reply = replies.TextReply(content=reply)
            reply.source = message.target
            reply.target = message.source
            return reply

    def normal_reply(self, message):
        if self.msg_type == self.MsgType.NEWS:
            klass = replies.ArticlesReply
            articles = Material.get_by_media(
                self.content["media_id"]).articles_json
            # 将media_id转为content
            data = dict(articles=articles)
        elif self.msg_type == self.MsgType.MUSIC:
            klass = replies.MusicReply
            data = dict(**self.content)
        elif self.msg_type == self.MsgType.VIDEO:
            klass = replies.VideoReply
            data = dict(**self.content)
        elif self.msg_type == self.MsgType.IMAGE:
            klass = replies.ImageReply
            data = dict(media_id=self.content["media_id"])
        elif self.msg_type == self.MsgType.VOICE:
            klass = replies.VoiceReply
            data = dict(media_id=self.content["media_id"])
        else:
            klass = replies.TextReply
            data = dict(content=self.content["content"])
        return klass(message=message, **data)

    @staticmethod
    def reply2send(reply):
        """
        将主动回复生成的reply转换为被动回复的方法及变量
        :type reply: wechatpy.replies.BaseReply
        """
        if not reply or isinstance(reply, replies.EmptyReply):
            return None, None
        type = ""
        kwargs = dict(user_id=reply.target)
        if isinstance(reply, replies.ArticlesReply):
            kwargs["articles"] = reply.articles
            type = "articles"
        elif isinstance(reply, replies.MusicReply):
            kwargs["url"] = reply.music_url
            kwargs["hq_url"] = reply.hq_music_url
            kwargs["thumb_media_id"] = reply.thumb_media_id
            kwargs["title"] = reply.title
            kwargs["description"] = reply.description
        elif isinstance(reply, replies.VideoReply):
            kwargs["media_id"] = reply.media_id
            kwargs["title"] = reply.title
            kwargs["description"] = reply.description
        elif isinstance(reply, (replies.ImageReply, replies.VoiceReply)):
            kwargs["media_id"] = reply.media_id
        elif isinstance(reply, replies.TextReply):
            kwargs["content"] = reply.content
        else:
            raise ValueError("unknown reply type")
        type = type or reply.type
        funcname = "send_" + type
        return funcname, kwargs

    @classmethod
    def from_mp(cls, data, handler):
        type = data["type"]
        if type == "img":
            type = cls.MsgType.IMAGE
        elif type == cls.MsgType.VIDEO:
            # video是链接
            type = cls.MsgType.TEXT
            data = dict(content='<a href="{0}">{1}</a>'.format(
                data["content"], _("video")))

        reply = cls(msg_type=type, handler=handler)
        if type == cls.MsgType.TEXT:
            content = dict(content=data["content"])
        elif type in (cls.MsgType.IMAGE, cls.MsgType.VOICE):
            # 按照文档 是临时素材 需要转换为永久素材
            content = dict(media_id=Material.as_permenant(
                data["content"], handler.app, False))
        elif type == cls.MsgType.NEWS:
            media_id = data["content"]
            # 同步图文
            Article.sync(handler.app, media_id)
            content = dict(
                media_id=media_id,
                content=data["news_info"]["list"]
            )
        else:
            raise ValueError("unknown reply type %s"%type)
        reply.content = content
        return reply

    @classmethod
    def from_menu(cls, data, handler):
        type = data["type"]
        if type == "img":
            type = cls.MsgType.IMAGE
        elif type == cls.MsgType.VIDEO:
            # video是链接
            type = cls.MsgType.TEXT
            data = dict(content='<a href="{0}">{1}</a>'.format(
                data["value"], data.get("name", _("video"))))

        rv = cls(msg_type=type, handler=handler)
        if type == cls.MsgType.TEXT:
            content = dict(content=data["content"])
        elif type in (cls.MsgType.IMAGE, cls.MsgType.VOICE):
            content = dict(media_id=Material.as_permenant(
                data["value"], handler.app, False)) if handler else data["value"]
        elif type == cls.MsgType.NEWS:
            media_id = data["value"]
            # 同步图文
            Article.sync(handler.app, media_id)
            content = dict(
                media_id=media_id,
                content=data["news_info"]["list"]
            )
        else:
            raise ValueError("unknown menu reply type %s"%type)
        rv.content = content
        return rv

    def __str__(self):
        if self.handler:
            return self.handler.name
        return super(Reply, self).__str__()
