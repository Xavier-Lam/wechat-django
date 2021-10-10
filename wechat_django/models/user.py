from django.db import models as m
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from wechat_django.utils.model import CacheField

from .apps import Application


class WeChatUser(m.Model):
    app = m.ForeignKey(Application, related_name="users", on_delete=m.CASCADE,
                       verbose_name=_("WeChat app"), null=False,
                       editable=False)
    openid = m.SlugField(_("openid"), max_length=36, null=False)
    unionid = m.SlugField(_("unionid"), max_length=36, null=True)
    alias = m.CharField(_("Alias"), max_length=16, blank=True, null=True,
                        help_text=_("An alias for user"))

    nickname = m.CharField(_("Nickname"), max_length=32, null=True)
    avatar_url = m.URLField(_("Avatar URL"), max_length=256, null=True)
    language = m.CharField(_("Language"), max_length=24, null=True)

    ext_info = JSONField(_("Extension information"))

    remark = m.CharField(_("WeChat remark"), max_length=30, blank=True,
                         null=True)
    comment = m.TextField(_("Remark"), blank=True, null=True)

    synchronized_at = m.DateTimeField(_("Last synchronized at"), null=True,
                                      default=None)

    access_token = CacheField(_("Access token"), expires_in=2*3600)
    refresh_token = m.CharField(_("Refresh token"), max_length=256, null=True)

    created_at = m.DateTimeField(_("Create at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("Updated at"), auto_now=True)

    class Meta(object):
        verbose_name = _("WeChat user")
        verbose_name_plural = _("WeChat users")

        ordering = ("app", "-created_at")
        unique_together = (("app", "openid"), ("unionid", "app"),
                           ("app", "alias"))

    @property
    def union_users(self):
        return self.__class__.objects.filter(unionid=self.unionid)
