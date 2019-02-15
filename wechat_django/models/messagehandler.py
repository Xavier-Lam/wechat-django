# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random

from django.db import models as m, transaction
from django.utils import timezone
from django.utils.translation import ugettext as _

from ..exceptions import HandleMessageError
from . import WeChatApp


class MessageHandler(m.Model):
    class Source(object):
        SELF = 0  # 自己的后台
        MENU = 1  # 菜单
        MP = 2  # 微信后台

    class ReplyStrategy(object):
        ALL = "reply_all"
        RANDOM = "random_one"
        NONE = "none"

    class EventType(object):
        SUBSCRIBE = "subscribe"
        UNSUBSCRIBE = "unsubscribe"
        SCAN = "SCAN"
        LOCATION = "LOCATION"
        CLICK = "CLICK"
        VIEW = "VIEW"

    app = m.ForeignKey(WeChatApp, on_delete=m.CASCADE,
        related_name="message_handlers", null=False, editable=False)
    name = m.CharField(_("name"), max_length=60)
    src = m.PositiveSmallIntegerField(choices=(
        (Source.MP, "wechat"),
        (Source.SELF, "self"),
        (Source.MENU, "menu")
    ), default=Source.SELF, editable=False)
    strategy = m.CharField(_("strategy"), max_length=10, choices=(
        (ReplyStrategy.ALL, "reply_all"),
        (ReplyStrategy.RANDOM, "random_one"),
        (ReplyStrategy.NONE, "none")
    ), default=ReplyStrategy.ALL)
    log = m.BooleanField(_("log"), default=False)

    starts = m.DateTimeField(_("starts"), null=True, blank=True)
    ends = m.DateTimeField(_("ends"), null=True, blank=True)
    enabled = m.BooleanField(_("enabled"), null=False, default=True)

    weight = m.IntegerField(_("weight"), default=0, null=False)
    created = m.DateTimeField(_("created"), auto_now_add=True)
    updated = m.DateTimeField(_("updated"), auto_now=True)

    class Meta:
        ordering = ("-weight", "-created", "-id")
        index_together = (
            ("app", "weight", "created"),
        )

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
    def matches(app, message):
        """
        :type app: wechat_django.models.WeChatApp
        :type message: wechat_django.models.WeChatMessage
        """
        handlers = app.message_handlers.prefetch_related("rules").all()
        for handler in handlers:
            if handler.is_match(message):
                return (handler, )

    def is_match(self, message):
        if self.available():
            for rule in self.rules.all():
                if rule.match(message):
                    return self

    def reply(self, message):
        """
        :type message: wechatpy.messages.BaseMessage
        :rtype: wechatpy.replies.BaseReply
        """
        reply = ""
        if self.strategy == self.ReplyStrategy.NONE:
            pass
        else:
            replies = list(self.replies.all())
            if not replies:
                pass
            elif self.strategy == self.ReplyStrategy.ALL:
                for reply in replies[1:]:
                    # TODO: 异常处理
                    reply.send(message)
                reply = replies[0]
            elif self.strategy == self.ReplyStrategy.RANDOM:
                reply = random.choice(replies)
            else:
                raise HandleMessageError("incorrect reply strategy")
        return reply and reply.reply(message)

    @classmethod
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
                handler = MessageHandler.objects.create(
                    app=app,
                    name="微信配置自动回复",
                    src=MessageHandler.Source.MP,
                    enabled=bool(resp.get("is_autoreply_open")),
                    created=timezone.datetime.fromtimestamp(0)
                )
                handlers.append(handler)
                rule = Rule.objects.create(type=Rule.Type.ALL, handler=handler)
                reply = Reply.from_mp(resp["message_default_autoreply_info"],
                    handler)
                reply.save()

            if resp.get("add_friend_autoreply_info"):
                # 关注回复
                handler = MessageHandler.objects.create(
                    app=app,
                    name="微信配置关注回复",
                    src=MessageHandler.Source.MP,
                    enabled=bool(resp.get("is_add_friend_reply_open")),
                    created=timezone.datetime.fromtimestamp(0)
                )
                handlers.append(handler)
                rule = Rule.objects.create(
                    type=Rule.Type.EVENT,
                    rule=dict(event=cls.EventType.SUBSCRIBE),
                    handler=handler
                )
                reply = Reply.from_mp(resp["add_friend_autoreply_info"], handler)
                reply.save()

            if (resp.get("keyword_autoreply_info")
                and resp["keyword_autoreply_info"].get("list")):
                for handler in resp["keyword_autoreply_info"]["list"][::-1]:
                    handlers.append(MessageHandler.from_mp(handler, app))
            return handlers

    @classmethod
    def from_mp(cls, handler, app):
        from . import Reply, Rule
        rv = cls.objects.create(
            app=app,
            name=handler["rule_name"],
            src=MessageHandler.Source.MP,
            created=timezone.datetime.fromtimestamp(handler["create_time"]),
            strategy=handler["reply_mode"]
        )
        rv.rules.bulk_create([
            Rule.from_mp(rule, rv)
            for rule in handler["keyword_list_info"][::-1]
        ])
        rv.replies.bulk_create([
            Reply.from_mp(reply, rv)
            for reply in handler["reply_list_info"][::-1]
        ])
        return rv

    @classmethod
    def from_menu(cls, menu, data, app):
        """
        :type menu: .Menu
        """
        from . import Reply, Rule
        handler = cls.objects.create(
            app=app,
            name="菜单[{0}]事件".format(data["name"]),
            src=cls.Source.MENU
        )
        Rule.objects.create(
            type=Rule.Type.EVENTKEY,
            rule=dict(
                event=cls.EventType.CLICK,
                key=menu.content["key"]
            ),
            handler=handler
        )
        Reply.from_menu(data, handler).save()
        return handler

    def __str__(self):
        return self.name
