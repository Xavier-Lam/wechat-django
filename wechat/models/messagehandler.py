import datetime

from django.db import models, transaction
from django.utils.translation import ugettext as _

from . import EventType, WechatApp

class MessageHandler(models.Model):
    class Source(object):
        MP = 0 # 微信后台
        MENU = 1 # 菜单
        SELF = 2 # 自己的后台

    class ReplyStrategy(object):
        ALL = "reply_all"
        RANDOM = "random_one"

    app = models.ForeignKey(WechatApp, on_delete=models.CASCADE,
        related_name="message_handlers", null=False, editable=False)
    name = models.CharField(_("name"), max_length=60)
    src = models.PositiveSmallIntegerField(choices=(
        (Source.MP, "wechat"),
        (Source.SELF, "self"),
        (Source.MENU, "menu")
    ), default=Source.SELF, editable=False)
    strategy = models.CharField(_("strategy"), max_length=10, choices=(
        (ReplyStrategy.ALL, "reply_all"), # 待实现
        (ReplyStrategy.RANDOM, "random_one")
    ), default=ReplyStrategy.RANDOM)

    starts = models.DateTimeField(_("starts"), null=True, blank=True)
    ends = models.DateTimeField(_("ends"), null=True, blank=True)
    available = models.BooleanField(_("available"), null=False, default=True)

    weight = models.IntegerField(_("weight"), default=0, null=False)
    created = models.DateTimeField(_("created"), auto_now_add=True)
    updated = models.DateTimeField(_("updated"), auto_now=True)

    class Meta:
        ordering = ("-weight", "-created")
        index_together = (
            ("app", "weight", "created"),
        )

    def match(self, message):
        if not self.available:
            return False
        now = datetime.datetime.now()
        if self.starts and self.starts > now:
            return False
        if self.ends and self.ends < now:
            return False
        for rule in self.rules:
            if rule.match(message):
                return True
        return False

    def reply(self, message):
        """
        :type message: wechatpy.messages.BaseMessage
        """
        reply = self.replies and self.replies[0]
        if reply:
            return reply.reply(message)
        return ""

    @staticmethod
    def sync(app):
        from . import Reply, Rule
        resp = app.client.message.get_autoreply_info()
        
        # 处理自动回复
        handlers = []
        if resp.get("add_friend_autoreply_info"):
            handlers.append(MessageHandler(
                app=app,
                name="微信配置关注回复",
                src=MessageHandler.Source.MP,
                replies=Reply.from_mp(resp["add_friend_autoreply_info"]),
                available=bool(resp.get("is_add_friend_reply_open")),
                rules=[Rule(type=Rule.Type.EVENT, rule=EventType.SUBSCRIBE)],
                created=datetime.datetime.fromtimestamp(0)
            ))
        if resp.get("message_default_autoreply_info"):
            handlers.append(MessageHandler(
                app=app,
                name="微信配置自动回复",
                src=MessageHandler.Source.MP,
                replies=Reply.from_mp(resp["message_default_autoreply_info"]),
                available=bool(resp.get("is_autoreply_open")),
                rules=[Rule(type=Rule.Type.ALL)],
                created=datetime.datetime.fromtimestamp(0)
            ))
        if (resp.get("keyword_autoreply_info")
            and resp["keyword_autoreply_info"].get("list")):
            for handler in resp["keyword_autoreply_info"]["list"]:
                handlers.append(
                    MessageHandler.from_mp(handler)
                )

        # 成功后移除之前的自动回复并保存新加入的自动回复
        with transaction.atomic():
            app.message_handlers.filter(
                src=MessageHandler.Source.MP
            ).all()
            MessageHandler.objects.bulk_create(handlers)           

    @classmethod
    def from_mp(cls, handler):
        from . import Reply, Rule
        return cls(
            name=handler["rule_name"],
            created_at=datetime.datetime.fromtimestamp(handler["create_time"]),
            replies=[Reply.from_mp(reply) for reply in handler["reply_list_info"]],
            rules=[Rule.from_mp(rule) for rule in handler["reply_list_info"]],
            strategy=handler["reply_mode"]
        )

    @classmethod
    def from_menu(cls, menu, data, app):
        """
        :type menu: .Menu
        """
        from . import Reply, Rule
        return cls(
            app=app,
            name="菜单[{0}]事件".format(data["name"]),
            src=cls.Source.MENU,
            rules=[Rule(
                type=Rule.Type.EVENTKEY,
                rule=dict(
                    event=EventType.CLICK,
                    key=menu.content
                ),
            )],
            replies=[Reply.from_menu(data)]
        )

    def __str__(self):
        return self.name