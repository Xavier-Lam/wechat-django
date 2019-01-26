from django.db import models as m
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _
from jsonfield import JSONField
import requests
from wechatpy import replies

from . import Article, Material, MessageHandler, ReplyMsgType
from .. import utils

class Reply(m.Model):
    handler = m.ForeignKey(MessageHandler, on_delete=m.CASCADE,
        related_name="replies")

    msg_type = m.CharField(_("type"), max_length=16,
        choices=utils.enum2choices(ReplyMsgType))
    content = JSONField()

    def reply(self, message):
        """
        :type message: wechatpy.messages.BaseMessage

        :returns: serialized xml response
        """
        if self.msg_type == ReplyMsgType.FORWARD:
            # 转发业务
            resp = requests.post(self.content["url"], message.raw, 
                params=message.request.GET, timeout=4.5)
            resp.raise_for_status()
            return resp.content
        else:
            reply = self._reply(message)
            return reply.render()
        
    def send(self, message):
        if self.msg_type == ReplyMsgType.FORWARD:
            raise NotImplementedError()
        else:
            reply = self._reply(message)
            funcname, kwargs = self.reply2send(reply)
            return getattr(self.app.client.message, funcname)(**kwargs)

    def _reply(self, message):
        assert self.msg_type != ReplyMsgType.FORWARD
        if self.msg_type == ReplyMsgType.CUSTOM:
            # 自定义业务
            try:
                func = import_string(self.content["program"])
            except:
                pass # TODO: 404
                return ""
            else:
                reply = func(message)
                if not reply:
                    return ""
                elif isinstance(reply, str):
                    reply = replies.TextReply(content=reply)
                reply.source = message.target
                reply.target = message.source
        else:
            # 正常回复类型
            if self.msg_type == ReplyMsgType.NEWS:
                klass = replies.ArticlesReply
                articles = Material.get_by_media(self.content["media_id"]).articles
                article_dicts = list(map(lambda o: dict(
                    title=o.title,
                    description=o.digest,
                    image=o.thumb_url,
                    url=o.url
                ), articles))
                # 将media_id转为content
                data = dict(articles=article_dicts)
            elif self.msg_type == ReplyMsgType.MUSIC:
                klass = replies.MusicReply
                data = dict(**self.content)
            elif self.msg_type == ReplyMsgType.VIDEO:
                klass = replies.VideoReply
                data = dict(**self.content)
            elif self.msg_type == ReplyMsgType.IMAGE:
                klass = replies.ImageReply
                data = dict(media_id=self.content["media_id"])
            elif self.msg_type == ReplyMsgType.VOICE:
                klass = replies.VoiceReply
                data = dict(media_id=self.content["media_id"])
            else:
                klass = replies.TextReply
                data = dict(content=self.content["content"])
            reply = klass(message=message, **data)    
        return reply

    @staticmethod
    def reply2send(reply):
        """
        :type reply: wechatpy.replies.BaseReply
        """
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
            # TODO: 自定义业务等
            raise ValueError("unknown reply type")
        type = type or reply.type
        funcname = "send_" + type
        return funcname, kwargs
    
    @classmethod
    def from_mp(cls, data, handler):
        type = data["type"]
        if type == ReplyMsgType.IMG:
            type = ReplyMsgType.IMAGE
        reply = cls(msg_type=type, handler=handler)
        if type == ReplyMsgType.TEXT:
            content = dict(content=data["content"])
        elif type in (ReplyMsgType.IMAGE, ReplyMsgType.VOICE):
            # 按照文档 是临时素材 需要转换为永久素材
            content = dict(media_id=Material.as_permenant(
                data["content"], app, False))
        elif type == ReplyMsgType.VIDEO:
            # TODO: 按照文档 这个为链接
            content = dict(media_id=data["content"])
        elif type == ReplyMsgType.NEWS:
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
        if type == ReplyMsgType.IMG:
            type = ReplyMsgType.IMAGE
        rv = cls(msg_type=type, handler=handler)
        if type == ReplyMsgType.TEXT:
            content = dict(content=data["content"])
        elif type in (ReplyMsgType.IMAGE, ReplyMsgType.VOICE):
            content = dict(media_id=Material.as_permenant(
                data["value"], handler.app, False)) if handler else data["value"]
        elif type == ReplyMsgType.VIDEO:
            # TODO: 按照文档 这个为链接
            content = dict(media_id=data["value"])
        elif type == ReplyMsgType.NEWS:
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
        return super().__str__()