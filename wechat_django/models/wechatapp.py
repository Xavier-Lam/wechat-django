import datetime

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models as m
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from wechatpy import WeChatClient

from . import EventType

class WechatApp(m.Model):
    class EncodingMode(object):
        PLAIN = 0
        BOTH = 1
        SAFE = 2

    title = m.CharField(_("title"), max_length=16, null=False)
    name = m.CharField(_("name"), help_text=_("公众号标识"),
        max_length=16, blank=False, null=False, 
        unique=True)
    desc = m.TextField(_("description"), default="", blank=True)

    appid = m.CharField(_("AppId"), 
        max_length=32, null=False, unique=True)
    appsecret = m.CharField(_("AppSecret"), 
        max_length=64, null=False)
    token = m.CharField(max_length=32, null=True, blank=True)
    encoding_aes_key = m.CharField(_("EncodingAESKey"), 
        max_length=43, null=True, blank=True)
    encoding_mode = m.PositiveSmallIntegerField(_("encoding mode"), choices=(
        (EncodingMode.PLAIN, _("plain")),
        # (EncodingMode.BOTH, "both"),
        (EncodingMode.SAFE, _("safe"))
    ), default=EncodingMode.PLAIN)

    # api用key 当不想暴露secretkey 给第三方时
    # secretkey = m.CharField(max_length=32)

    created = m.DateTimeField(_("created"), auto_now_add=True)
    updated = m.DateTimeField(_("updated"), auto_now=True)

    @classmethod
    def get_by_id(cls, id):
        return cls.objects.filter(id=id).first()

    @classmethod
    def get_by_name(cls, name):
        return cls.objects.filter(name=name).first()

    @property
    def client(self):
        if not self._client:
            self._client = WeChatClient(
                self.appid,
                self.secret
                # TODO: 配置session
            )
        return self._client

    def interactable(self):
        return bool(self.token and self.encoding_aes_key)
    interactable.boolean = True
    interactable.short_description = _("interactable")

    def match(self, message):
        if not message: return
        for handler in self.message_handlers:
            if handler.match(message):
                return handler

    def __str__(self):
        return "{title} ({name})".format(title=self.title, name=self.name)

permissions = (
    "{appname}_full",
    "{appname}_manage",
    "{appname}_menu",
    "{appname}_handlemessage",
)

@receiver(m.signals.post_save, sender=WechatApp)
def execute_after_save(sender, instance, created, *args, **kwargs):
    if created:
        # 添加
        content_type = ContentType.objects.get_for_model(WechatApp)
        Permission.objects.bulk_create(
            Permission(
                codename=permission.format(appname=instance.name),
                name=permission.format(appname=instance.name),
                content_type=content_type
            )
            for permission in permissions
        )

@receiver(m.signals.post_delete, sender=WechatApp)
def execute_after_delete(sender, instance, *args, **kwargs):
    content_type = ContentType.objects.get_for_model(WechatApp)
    Permission.objects.filter(
        content_type=content_type,
        codename__in=[permission.format(appname=instance.name) \
            for permission in permissions]
    ).delete()