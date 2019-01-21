import random

from django.db import models as m, transaction
from django.utils import timezone
from django.utils.translation import ugettext as _

from . import EventType, WeChatApp

class MessageHandler(m.Model):
    class Source(object):
        MP = 0 # 微信后台
        MENU = 1 # 菜单
        SELF = 2 # 自己的后台

    class ReplyStrategy(object):
        ALL = "reply_all"
        RANDOM = "random_one"
        NONE = "none"

    app = m.ForeignKey(WeChatApp, on_delete=m.CASCADE,
        related_name="message_handlers", null=False, editable=False)
    name = m.CharField(_("name"), max_length=60)
    src = m.PositiveSmallIntegerField(choices=(
        (Source.MP, "wechat"),
        (Source.SELF, "self"),
        (Source.MENU, "menu")
    ), default=Source.SELF, editable=False)
    strategy = m.CharField(_("strategy"), max_length=10, choices=(
        (ReplyStrategy.ALL, "reply_all"), # 待实现
        (ReplyStrategy.RANDOM, "random_one"),
        (ReplyStrategy.NONE, "none")
    ), default=ReplyStrategy.RANDOM)

    starts = m.DateTimeField(_("starts"), null=True, blank=True)
    ends = m.DateTimeField(_("ends"), null=True, blank=True)
    enabled = m.BooleanField(_("enabled"), null=False, default=True)

    weight = m.IntegerField(_("weight"), default=0, null=False)
    created = m.DateTimeField(_("created"), auto_now_add=True)
    updated = m.DateTimeField(_("updated"), auto_now=True)

    class Meta:
        ordering = ("-weight", "-created")
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

    def match(self, message):
        if self.available():
            for rule in self.rules:
                if rule.match(message):
                    return True
        return False

    def reply(self, message):
        """
        :type message: wechatpy.messages.BaseMessage
        """
        reply = None
        if self.strategy == self.ReplyStrategy.NONE:
            pass
        elif self.strategy == self.ReplyStrategy.ALL:
            for reply in self.replies[1:]:
                reply.send(message)
            reply = self.replies and self.replies[0]
        elif self.strategy == self.ReplyStrategy.RANDOM:
            reply = self.replies and random.choice(self.replies)
        else:
            raise ValueError("incorrect reply strategy")
        return reply.reply() if reply else ""

    @staticmethod
    def sync(app):
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
                handler = MessageHandler(
                    app=app,
                    name="微信配置自动回复",
                    src=MessageHandler.Source.MP,
                    enabled=bool(resp.get("is_autoreply_open")),
                    created=timezone.datetime.fromtimestamp(0)
                )
                handlers.append(handler)
                handler.save()
                reply = Reply.from_mp(resp["message_default_autoreply_info"], handler)
                rule = Rule(type=Rule.Type.ALL, handler=handler)
                reply.save()
                rule.save()
            if resp.get("add_friend_autoreply_info"):
                handler = MessageHandler(
                    app=app,
                    name="微信配置关注回复",
                    src=MessageHandler.Source.MP,
                    enabled=bool(resp.get("is_add_friend_reply_open")),
                    created=timezone.datetime.fromtimestamp(0)
                )
                handlers.append(handler)
                handler.save()
                reply = Reply.from_mp(resp["add_friend_autoreply_info"], handler)
                rule = Rule(
                    type=Rule.Type.EVENT, 
                    rule=dict(event=EventType.SUBSCRIBE),
                    handler=handler
                )
                reply.save()
                rule.save()
            if (resp.get("keyword_autoreply_info")
                and resp["keyword_autoreply_info"].get("list")):
                for handler in resp["keyword_autoreply_info"]["list"]:
                    handlers.append(MessageHandler.from_mp(handler, app))
            return handlers 

    @classmethod
    def from_mp(cls, handler, app):
        from . import Reply, Rule
        rv = cls(
            app=app,
            name=handler["rule_name"],
            src=MessageHandler.Source.MP,
            created=timezone.datetime.fromtimestamp(handler["create_time"]),
            strategy=handler["reply_mode"]
        )
        rv.save()
        rv.rules.bulk_create([
            Rule.from_mp(rule, rv) 
            for rule in handler["keyword_list_info"]
        ])
        rv.replies.bulk_create([
            Reply.from_mp(reply, rv) 
            for reply in handler["reply_list_info"]
        ])
        return rv

    @classmethod
    def from_menu(cls, menu, data, app):
        """
        :type menu: .Menu
        """
        from . import Reply, Rule
        handler = cls(
            app=app,
            name="菜单[{0}]事件".format(data["name"]),
            src=cls.Source.MENU
        )
        handler.save()
        Rule(
            type=Rule.Type.EVENTKEY,
            rule=dict(
                event=EventType.CLICK,
                key=menu.content["key"]
            ),
            handler=handler
        ).save()
        Reply.from_menu(data, handler).save()
        return handler

    def __str__(self):
        return self.name