from django.db import models as m
from django.utils.translation import ugettext_lazy as _

from wechat_django.enums import AppType, WeChatOAuthScope
from .mixins import (
    JSAPIMixin, MessagePushApplicationMixin, OAuthApplicationMixin)
from .ordinaryapplication import OrdinaryApplication


class OfficialAccountApplicationMixin(m.Model):
    DEFAULT_AUTHORIZE_URL = "https://open.weixin.qq.com/connect/oauth2/authorize"  # noqa
    DEFAULT_SCOPES = WeChatOAuthScope.BASE

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.type = AppType.OFFICIALACCOUNT
        return super().save(*args, **kwargs)


class OfficialAccountApplication(OfficialAccountApplicationMixin,
                                 JSAPIMixin,
                                 MessagePushApplicationMixin,
                                 OAuthApplicationMixin,
                                 OrdinaryApplication):
    class Meta:
        proxy = True
        verbose_name = _("Official account application")
        verbose_name_plural = _("Official account applications")
