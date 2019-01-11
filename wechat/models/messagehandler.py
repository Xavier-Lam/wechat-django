from django.db import models

from . import WechatApp

class MessageHandler(models.Model):
    class Source(object):
        MP = 0 # 微信后台
        SELF = 1 # 自己的后台

    class ReplyStrategy(object):
        ALL = "reply_all"
        RANDOM = "random_one"

    app = models.ForeignKey(WechatApp, on_delete=models.CASCADE,
        related_name="message_handlers")
    src = models.PositiveSmallIntegerField(choices=(
        (Source.MP, "wechat"),
        (Source.SELF, "self")
    ))
    strategy = models.CharField(max_length=10, choices=(
        (ReplyStrategy.ALL, "reply_all"),
        (ReplyStrategy.RANDOM, "random_one")
    ))

    starts = models.DateTimeField(null=True, blank=True)
    ends = models.DateTimeField(null=True, blank=True)
    available = models.BooleanField(null=False, default=True)

    weight = models.IntegerField(default=0, null=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-weight", )
        # index_together = (
        #     ("app", "weight"),
        # )

    def match(self, message):
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