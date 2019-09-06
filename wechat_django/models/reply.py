# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from copy import deepcopy

from django.db import models as m
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
import requests
from six import text_type
from wechatpy import replies

from ..exceptions import MessageHandleError
from ..utils.model import enum2choices, model_fields
from . import Material, MessageHandler, MsgType as BaseMsgType, WeChatModel


class Reply(WeChatModel):
    class MsgType(BaseMsgType):
        MUSIC = "music"
        NEWS = "news"

        CUSTOM = "custom"  # 自定义业务
        FORWARD = "forward"  # 转发

    handler = m.ForeignKey(
        MessageHandler, related_name="replies", on_delete=m.CASCADE)

    type = m.CharField(
        _("type"), db_column="type", max_length=16,
        choices=enum2choices(MsgType))
    _content = JSONField(db_column="content", default=dict)

    weight = m.IntegerField(_("weight"), default=0, null=False)
    created_at = m.DateTimeField(_("created_at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated_at"), auto_now=True)

    class Meta(object):
        verbose_name = _("reply")
        verbose_name_plural = _("replies")

        ordering = ("-weight", "id")

    @property
    def app(self):
        return self.handler.app

    @property
    def content(self):
        return self._content

    def __init__(self, *args, **kwargs):
        field_names = model_fields(self)
        content_keys = set(kwargs.keys()) - field_names
        content = dict()
        for key in content_keys:
            content[key] = kwargs.pop(key)
        kwargs["_content"] = content
        super(Reply, self).__init__(*args, **kwargs)

    def send(self, message_info):
        """主动回复
        :type message_info: wechat_django.models.WeChatMessageInfo
        """
        reply = self.reply(message_info)
        funcname, kwargs = self.reply2send(reply)
        func = funcname and getattr(self.app.client.message, funcname)
        return func and func(**kwargs)

    def reply(self, message_info):
        """被动回复
        :type message_info: wechat_django.models.WeChatMessageInfo
        :rtype: wechatpy.replies.BaseReply
        """
        if self.type == self.MsgType.FORWARD:
            # 转发业务
            reply = self.reply_forward(message_info)
        elif self.type == self.MsgType.CUSTOM:
            # 自定义业务
            reply = self.reply_custom(message_info)
        else:
            # 正常回复类型
            reply = self.normal_reply(message_info.message)
        return reply

    def reply_forward(self, message_info):
        """
        :type message_info: wechat_django.models.WeChatMessageInfo
        """
        resp = requests.post(
            self.content["url"], message_info.raw,
            params=message_info.request.GET, timeout=4.5)
        resp.raise_for_status()
        return replies.deserialize_reply(resp.content)

    def reply_custom(self, message_info):
        """
        :type message_info: wechat_django.models.WeChatMessageInfo
        """
        try:
            func = import_string(self.content["program"])
        except:
            raise MessageHandleError("custom bussiness not found")
        else:
            appname = message_info.app.name
            message = message_info.message
            if not hasattr(func, "message_handler"):
                e = "handler must be decorated by wechat_django.handler.message_handler"
                raise MessageHandleError(e)
            elif (hasattr(func.message_handler, "__contains__")
                and appname not in func.message_handler):
                e = "this handler cannot assigned to {0}".format(appname)
                raise MessageHandleError(e)
            reply = func(message_info)
            if not reply:
                return ""
            elif isinstance(reply, text_type):
                reply = replies.TextReply(content=reply)
            reply.source = message.target
            reply.target = message.source
            return reply

    def normal_reply(self, message):
        """
        :type message: wechatpy.messages.BaseMessage
        """
        if self.type == self.MsgType.NEWS:
            klass = replies.ArticlesReply
            media = self.app.materials.get(media_id=self.content["media_id"])
            # 将media_id转为content
            data = dict(
                articles=media.articles_json,
                media_id=self.content["media_id"]
            )
        elif self.type == self.MsgType.MUSIC:
            klass = replies.MusicReply
            data = dict(**self.content)
        elif self.type == self.MsgType.VIDEO:
            klass = replies.VideoReply
            data = dict(**self.content)
        elif self.type == self.MsgType.IMAGE:
            klass = replies.ImageReply
            data = dict(media_id=self.content["media_id"])
        elif self.type == self.MsgType.VOICE:
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
            kwargs["articles"] = deepcopy(reply.articles)
            for article in kwargs["articles"]:
                article["picurl"] = article["image"]
                del article["image"]
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
            raise MessageHandleError("unknown reply type")
        type = type or reply.type
        funcname = "send_" + type
        return funcname, kwargs

    @classmethod
    def from_mp(cls, app, data, src=None):
        type = data["type"]
        if type == "img":
            type = cls.MsgType.IMAGE
        elif type == cls.MsgType.VIDEO:
            # video是链接
            type = cls.MsgType.TEXT
            data = dict(content='<a href="{0}">{1}</a>'.format(
                data["content"], _("video")))

        kwargs = dict(type=type)
        if type == cls.MsgType.TEXT:
            kwargs.update(content=data["content"])
        elif type in (cls.MsgType.IMAGE, cls.MsgType.VOICE):
            # 按照文档 是临时素材 需要转换为永久素材
            media_id = app.as_permenant_material(data["content"], src=src,
                                                 save=False)
            kwargs.update(media_id=media_id)
        elif type == cls.MsgType.NEWS:
            media_id = data["content"]
            # 同步图文
            if src:
                media_id = app.migrate_articles(src, media_id).media_id
            else:
                app.sync_articles(media_id)
            kwargs.update(media_id=media_id,
                          content=data["news_info"]["list"])
        else:
            raise ValueError("unknown reply type {0}".format(type))
        return cls(**kwargs)

    @classmethod
    def from_menu(cls, menu, data, src=None):
        app = menu.app
        type = data["type"]
        if type == "img":
            type = cls.MsgType.IMAGE
        elif type == cls.MsgType.VIDEO:
            # video是链接
            type = cls.MsgType.TEXT
            data = dict(content='<a href="{0}">{1}</a>'.format(
                data["value"], data.get("name", _("video"))))

        kwargs = dict(type=type)
        if type == cls.MsgType.TEXT:
            kwargs.update(content=data["content"])
        elif type in (cls.MsgType.IMAGE, cls.MsgType.VOICE):
            media_id = app.as_permenant_material(
                data["value"], save=False, src=src) if app else data["value"]
            kwargs.update(media_id=media_id)
        elif type == cls.MsgType.NEWS:
            media_id = data["value"]
            # 同步图文
            if src:
                media_id = app.migrate_articles(src, media_id).media_id
            else:
                app.sync_articles(media_id)
            kwargs.update(media_id=media_id,
                          content=data["news_info"]["list"])
        else:
            raise ValueError("unknown menu reply type {0}".format(type))
        return cls(**kwargs)

    def __str__(self):
        if self.handler_id:
            return "{0} - {1}".format(self.handler.name, self.type)
        return "{0}".format(self.type)
