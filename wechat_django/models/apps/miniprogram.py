from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from wechat_django.enums import AppType
from wechat_django.models.apps.base import MessagePushApplicationMixin
from .ordinaryapplication import OrdinaryApplication


class MiniProgramApplicationMixin:
    @cached_property
    def client(self):
        return self.base_client.wxa

    def save(self, *args, **kwargs):
        self.type = AppType.MINIPROGRAM
        return super().save(*args, **kwargs)


class MiniProgramApplication(MiniProgramApplicationMixin,
                             MessagePushApplicationMixin,
                             OrdinaryApplication):
    class Meta:
        proxy = True
        verbose_name = _("Miniprogram application")
        verbose_name_plural = _("Miniprogram applications")
