# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import random

from django.db import models as m, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from wechatpy.exceptions import WeChatClientException

from ..exceptions import MessageHandleError
from ..utils.admin import enum2choices
from ..utils.web import get_ip
from . import appmethod, MsgLogFlag, WeChatApp, WeChatModel


class MessageHandlerManager(m.Manager):
    def create_handler(self, rules=None, replies=None, **kwargs):
        """:rtype: wechat_django.models.MessageHandler"""
        handler = self.create(**kwargs)
        if rules:
            for rule in rules:
                rule.handler = handler
            handler.rules.bulk_create(rules)
        if replies:
            for reply in replies:
                reply.handler = handler
            handler.replies.bulk_create(replies)
        return handler


class MessageHandler(WeChatModel):
    class Source(object):
        SELF = 0  # 自己的后台
        MENU = 1  # 菜单
        MP = 2  # 微信后台

    class ReplyStrategy(object):
        REPLYALL = "reply_all"
        RANDOM = "random_one"
        NONE = "none"

    class EventType(object):
        SUBSCRIBE = "subscribe"
        UNSUBSCRIBE = "unsubscribe"
        SCAN = "SCAN"
        LOCATION = "LOCATION"
        CLICK = "CLICK"
        VIEW = "VIEW"

    class Flag(object):
        TERMINALONEXCEPTION = 0x01 # 当回复全部时 一个回复发生异常 中断其他回复

    app = m.ForeignKey(
        WeChatApp, on_delete=m.CASCADE, related_name="message_handlers",
        null=False, editable=False)
    name = m.CharField(_("name"), max_length=60)
    src = m.PositiveSmallIntegerField(choices=(
        (Source.MP, "wechat"),
        (Source.SELF, "self"),
        (Source.MENU, "menu")
    ), default=Source.SELF, editable=False)
    strategy = m.CharField(_("strategy"), max_length=10,
        choices=enum2choices(ReplyStrategy), default=ReplyStrategy.REPLYALL)

    flags = m.IntegerField(_("flags"), default=False)

    starts = m.DateTimeField(_("starts"), null=True, blank=True)
    ends = m.DateTimeField(_("ends"), null=True, blank=True)
    enabled = m.BooleanField(_("enabled"), null=False, default=True)

    weight = m.IntegerField(_("weight"), default=0, null=False)
    created_at = m.DateTimeField(_("created_at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated_at"), auto_now=True)

    objects = MessageHandlerManager()

    class Meta:
        verbose_name = _("message handler")
        verbose_name_plural = _("message handlers")

        ordering = ("-weight", "-created_at", "-id")
        index_together = (
            ("app", "weight", "created_at"),
        )

    @property
    def log_message(self):
        return bool(self.flags & MsgLogFlag.LOG_MESSAGE)

    def available(self):
        if not self.enabled:
            return False
        now = timezone.now()
        if self.starts and self.starts > now:
            return False
        if self.ends and self.ends < now:
            return False
        return True
    available.short_description = _("available")
    available.boolean = True

    @staticmethod
    def matches(message_info):
        """
        :type message_info: wechat_django.models.WeChatMessageInfo
        """
        handlers = message_info.app.message_handlers\
            .prefetch_related("rules").all()
        for handler in handlers:
            if handler.is_match(message_info):
                return (handler, )

    def is_match(self, message_info):
        if self.available():
            for rule in self.rules.all():
                if rule.match(message_info):
                    return self

    def reply(self, message_info):
        """
        :type message_info: wechat_django.models.WeChatMessageInfo
        :rtype: wechatpy.replies.BaseReply
        """
        reply = ""
        if self.strategy == self.ReplyStrategy.NONE:
            pass
        else:
            replies = list(self.replies.all())
            if not replies:
                pass
            elif self.strategy == self.ReplyStrategy.REPLYALL:
                for reply in replies[:-1]:
                    try:
                        reply.send(message_info)
                    except Exception as e:
                        # 发送异常 继续处理其他程序
                        log = self.handlerlog(message_info.request)
                        msg = "an unexcepted error occurred when send msg"
                        level = logging.WARNING\
                            if isinstance(e, WeChatClientException)\
                            else logging.ERROR
                        log(level, msg, exc_info=True)
                reply = replies[-1]
            elif self.strategy == self.ReplyStrategy.RANDOM:
                reply = random.choice(replies)
            else:
                raise MessageHandleError("incorrect reply strategy")
        return reply and reply.reply(message_info)

    @classmethod
    @appmethod("sync_message_handlers")
    def sync(cls, app):
        from . import Reply, Rule
        resp = app.client.message.get_autoreply_info()

        # 处理自动回复
        handlers = []

        # 成功后移除之前的自动回复并保存新加入的自动回复
        with transaction.atomic():
            app.message_handlers.filter(
                src=MessageHandler.Source.MP
            ).delete()

            if resp.get("message_default_autoreply_info"):
                # 自动回复
                handler = cls.objects.create_handler(
                    app=app,
                    name="微信配置自动回复",
                    src=MessageHandler.Source.MP,
                    enabled=bool(resp.get("is_autoreply_open")),
                    created_at=timezone.datetime.fromtimestamp(0),
                    rules=[Rule(type=Rule.Type.ALL)],
                    replies=[
                        Reply.from_mp(
                            resp["message_default_autoreply_info"], app)
                    ]
                )
                handlers.append(handler)

            if (resp.get("keyword_autoreply_info")
                and resp["keyword_autoreply_info"].get("list")):
                handlers_list = resp["keyword_autoreply_info"]["list"][::-1]
                handlers.extend(
                    MessageHandler.from_mp(handler, app)
                    for handler in handlers_list
                )

            if resp.get("add_friend_autoreply_info"):
                # 关注回复
                handler = cls.objects.create_handler(
                    app=app,
                    name="微信配置关注回复",
                    src=MessageHandler.Source.MP,
                    enabled=bool(resp.get("is_add_friend_reply_open")),
                    created_at=timezone.datetime.fromtimestamp(0),
                    rules=[Rule(
                        type=Rule.Type.EVENT,
                        event=cls.EventType.SUBSCRIBE
                    )],
                    replies=[
                        Reply.from_mp(resp["add_friend_autoreply_info"], app)
                    ]
                )
                handlers.append(handler)
                
            return handlers

    @classmethod
    def from_mp(cls, handler, app):
        from . import Reply, Rule
        return cls.objects.create_handler(
            app=app,
            name=handler["rule_name"],
            src=MessageHandler.Source.MP,
            created_at=timezone.datetime.fromtimestamp(handler["create_time"]),
            strategy=handler["reply_mode"],
            rules=[
                Rule.from_mp(rule)
                for rule in handler["keyword_list_info"][::-1]
            ],
            replies=[
                Reply.from_mp(reply, app)
                for reply in handler["reply_list_info"][::-1]
            ]
        )

    @classmethod
    def from_menu(cls, menu, data, app):
        """
        :type menu: .Menu
        """
        from . import Reply, Rule
        return cls.objects.create_handler(
            app=app,
            name="菜单[{0}]事件".format(data["name"]),
            src=cls.Source.MENU,
            rules=[Rule(
                type=Rule.Type.EVENTKEY,
                event=cls.EventType.CLICK,
                key=menu.content["key"]
            )],
            replies=[Reply.from_menu(data, app)]
        )

    @classmethod
    def handlerlog(cls, request):
        logger = logging.getLogger(
            "wechat.handler.{0}".format(request.wechat.appname))
        args = dict(
            params=request.GET,
            body=request.body,
            ip=get_ip(request)
        )
        s = "%s - {0}".format(args)
        return lambda lvl, msg, **kwargs: logger.log(lvl, s % msg, **kwargs)

    def __str__(self):
        return "{0}".format(self.name)
