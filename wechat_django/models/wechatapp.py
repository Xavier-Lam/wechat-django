import datetime

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from wechatpy import WeChatClient

from . import EventType

class WechatApp(models.Model):
    class EncodingMode(object):
        PLAIN = 0
        BOTH = 1
        SAFE = 2

    title = models.CharField(_("title"), max_length=16, null=False)
    name = models.CharField(_("name"), help_text=_("公众号标识"),
        max_length=16, blank=False, null=False, 
        unique=True)
    desc = models.TextField(_("description"), default="", blank=True)

    appid = models.CharField(_("AppId"), 
        max_length=32, null=False, unique=True)
    appsecret = models.CharField(_("AppSecret"), 
        max_length=64, null=False)
    token = models.CharField(max_length=32, null=True, blank=True)
    encoding_aes_key = models.CharField(_("EncodingAESKey"), 
        max_length=43, null=True, blank=True)
    encoding_mode = models.PositiveSmallIntegerField(_("encoding mode"), choices=(
        (EncodingMode.PLAIN, _("plain")),
        # (EncodingMode.BOTH, "both"),
        (EncodingMode.SAFE, _("safe"))
    ), default=EncodingMode.PLAIN)

    # api用key 当不想暴露secretkey 给第三方时
    # secretkey = models.CharField(max_length=32)

    created = models.DateTimeField(_("created"), auto_now_add=True)
    updated = models.DateTimeField(_("updated"), auto_now=True)

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

# TODO: 管理权限
permissions = (
    "{appname}_manage",
    "{appname}_menu",
    "{appname}_handlemessage",
)

@receiver(models.signals.post_save, sender=WechatApp)
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

@receiver(models.signals.post_delete, sender=WechatApp)
def execute_after_delete(sender, instance, *args, **kwargs):
    content_type = ContentType.objects.get_for_model(WechatApp)
    Permission.objects.filter(
        content_type=content_type,
        codename__in=[permission.format(appname=instance.name) \
            for permission in permissions]
    ).delete()