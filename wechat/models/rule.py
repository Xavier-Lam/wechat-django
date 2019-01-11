from django.db import models

from .. import utils
from . import MessageHandler

class Rule(models.Model):
    handler = models.ForeignKey(MessageHandler, on_delete=models.CASCADE, 
        related_name="rules")

    type = models.PositiveSmallIntegerField() # 规则类型
    rule = models.TextField() # 规则内容

    weight = models.IntegerField(default=0, null=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-weight", )

    def match(self, message):
        return False