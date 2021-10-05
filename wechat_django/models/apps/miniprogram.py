from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from wechat_django.enums import AppType
from .ordinaryapplication import OrdinaryApplication


class MiniProgramApplicationMixin:
    def save(self, *args, **kwargs):
        self.type = AppType.MINIPROGRAM
        return super().save(*args, **kwargs)


class MiniProgramApplication(MiniProgramApplicationMixin,
                             OrdinaryApplication):
    class Meta:
        proxy = True
        verbose_name = _("Miniprogram application")
        verbose_name_plural = _("Miniprogram applications")

    @cached_property
    def client(self):
        return self.base_client.wxa
