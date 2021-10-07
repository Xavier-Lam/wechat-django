from django.utils.translation import ugettext_lazy as _

from wechat_django.enums import AppType
from .base import MessagePushApplicationMixin
from .ordinaryapplication import OrdinaryApplication


class OfficialAccountApplicationMixin:
    def save(self, *args, **kwargs):
        self.type = AppType.OFFICIALACCOUNT
        return super().save(*args, **kwargs)


class OfficialAccountApplication(OfficialAccountApplicationMixin,
                                 MessagePushApplicationMixin,
                                 OrdinaryApplication):
    class Meta:
        proxy = True
        verbose_name = _("Official account application")
        verbose_name_plural = _("Official account applications")
