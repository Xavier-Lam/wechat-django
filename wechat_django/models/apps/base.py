from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.db import models as m
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from wechatpy.crypto import WeChatCrypto
from wechatpy.parser import parse_message
from wechatpy.session import SessionStorage

from wechat_django.enums import AppType, EncryptStrategy
from wechat_django.exceptions import AbilityError
from wechat_django.utils import logging
from wechat_django.utils.crypto import crypto
from wechat_django.utils.django import decriptor2contributor
from wechat_django.utils.model import CacheField, ModelPropertyDescriptor
from wechat_django.utils.wechatpy import WeChatClient
from wechat_django.wechat.messagehandler import PlainTextReply, reply2send


@decriptor2contributor
class ConfigurationProperty(ModelPropertyDescriptor):
    target = "configurations"


@decriptor2contributor
class StorageProperty(ModelPropertyDescriptor):
    target = "storage"


class Application(m.Model):
    title = m.CharField(_("Title"), max_length=16, null=False,
                        help_text=_("The human-readable name of the "
                                    "application"))
    name = m.CharField(_("Application name"), max_length=64, blank=False,
                       unique=True,
                       help_text=_("The program name of the application"))
    desc = m.TextField(_("Description"), default="", blank=True)
    type = m.IntegerField(_("Application type"), null=False, choices=(
        (AppType.UNKNOWN, _("Unknown application")),
        (AppType.MINIPROGRAM, _("Miniprogram")),
        (AppType.OFFICIALACCOUNT, _("Official account")),
        (AppType.WEBAPP, _("Web application")),
        (AppType.PAY, _("WeChat pay")),
        (AppType.MERCHANTPAY, _("WeChat pay merchant")),
        (AppType.HOSTED | AppType.PAY, _("Hosted WeChat pay")),
        (AppType.THIRDPARTYPLATFORM, _("Third party platform")),
        (AppType.HOSTED | AppType.MINIPROGRAM, _("Hosted miniprogram")),
        (AppType.HOSTED | AppType.OFFICIALACCOUNT,
         _("Hosted official account"))
    ))

    appid = m.SlugField(_("AppId"), max_length=32, null=False)
    appsecret = m.BinaryField(_("AppSecret"), max_length=256, blank=True,
                              editable=True)

    parent = m.ForeignKey("self", verbose_name=_("Parent application"),
                          on_delete=m.CASCADE, related_name="children",
                          null=True, blank=True)

    pays = m.ManyToManyField("self", verbose_name=_("WeChat pay"),
                             related_name="apps", blank=True,
                             limit_choices_to={"type__in": (
                                AppType.PAY, AppType.HOSTED | AppType.PAY)})

    configurations = JSONField(_("Configurations"), default={})
    storage = JSONField(default={})

    created_at = m.DateTimeField(_("Create at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Application")
        verbose_name_plural = _("Applications")

    @cached_property
    def session(self):
        return ApplicationStorage(self)

    @classmethod
    def from_db(cls, db, field_names, values):
        app_type = dict(zip(field_names, values)).get("type")
        model_cls = cls.get_class_by_type(app_type)
        return super().from_db.__func__(model_cls, db, field_names, values)

    @classmethod
    def get_class_by_type(cls, app_type):
        import wechat_django.models.apps as apps

        if app_type == AppType.OFFICIALACCOUNT:
            cls = apps.OfficialAccountApplication
        elif app_type == AppType.MINIPROGRAM:
            cls = apps.MiniProgramApplication
        elif app_type == AppType.THIRDPARTYPLATFORM:
            cls = apps.ThirdPartyPlatform
        elif app_type == AppType.PAY:
            cls = apps.PayApplication
        elif app_type == AppType.MERCHANTPAY:
            cls = apps.PayMerchant
        elif app_type & AppType.HOSTED:
            if app_type & AppType.OFFICIALACCOUNT:
                cls = apps.OfficialAccountAuthorizerApplication
            elif app_type & AppType.MINIPROGRAM:
                cls = apps.MiniProgramAuthorizerApplication
            elif app_type & AppType.PAY:
                cls = apps.HostedPayApplication
        else:
            cls = apps.OrdinaryApplication
        return cls

    def clean(self):
        not self.parent_id and validate_slug(self.name)
        return super().clean()

    def __str__(self):
        return "{0} ({1})".format(self.title, self.name)


class HostedApplicationMixin:
    def clean(self):
        if not self.name.startswith(self.parent.name + "."):
            raise ValidationError({
                "name": _("Hosted application's must be named as "
                          "'%s.<name>'") % self.parent.name
            })
        parent_name, child_name = self.name.split(".", 1)
        validate_slug(parent_name)
        validate_slug(child_name)
        return super().clean()

    def save(self, *args, **kwargs):
        self.type |= AppType.HOSTED
        return super().save(*args, **kwargs)


class AccessTokenApplicationMixin(m.Model):
    access_token_url = ConfigurationProperty(
        _("Access token url"),
        help_text=_("The url used to fetch access_token")
    )
    _access_token = CacheField(_("Access Token"), expires_in=2*3600)

    class Meta:
        abstract = True

    @cached_property
    def base_client(self):
        return WeChatClient(self)

    @cached_property
    def client(self):
        return self.base_client

    @property
    def access_token(self):
        return self.base_client.access_token


class MessagePushApplicationMixin(AccessTokenApplicationMixin):
    token = ConfigurationProperty(_("Token"))
    encoding_aes_key = ConfigurationProperty(_("Encoding AES Key"))
    encrypt_strategy = ConfigurationProperty(
        _("Encrypt Strategy"), default=EncryptStrategy.ENCRYPTED,
        choices=(
            (EncryptStrategy.ENCRYPTED, _(EncryptStrategy.ENCRYPTED)),
            (EncryptStrategy.PLAIN, _(EncryptStrategy.PLAIN)),
        )
    )

    class Meta:
        abstract = True

    @cached_property
    def crypto(self):
        if not self.token or not self.encoding_aes_key:
            raise AbilityError
        return WeChatCrypto(
            token=crypto.decrypt(self.token),
            encoding_aes_key=crypto.decrypt(self.encoding_aes_key),
            app_id=self.appid
        )

    def notify_url(self, request):
        path = reverse("wechat_django:handler",
                       kwargs={"app_name": self.name})
        return "{protocol}://{host}{path}".format(
            protocol=request.scheme,
            host=request.get_host(),
            path=path
        )

    def decrypt_message(self, request):
        raw_message = request.body
        if self.encrypt_strategy == EncryptStrategy.ENCRYPTED:
            raw_message = self.crypto.decrypt_message(
                raw_message,
                request.GET["msg_signature"],
                request.GET["timestamp"],
                request.GET["nonce"]
            )
        return raw_message

    def encrypt_message(self, reply, request):
        xml = reply.render()
        if self.encrypt_strategy == EncryptStrategy.ENCRYPTED\
                and not isinstance(reply, PlainTextReply):
            xml = self.crypto.encrypt_message(xml, request.GET["nonce"],
                                              request.GET["timestamp"])
        return xml

    def parse_message(self, raw_message):
        return parse_message(raw_message)

    def send_message(self, reply):
        func_name, kwargs = reply2send(reply)
        func_name and getattr(self.base_client.message, func_name)(**kwargs)


class ApplicationStorage(SessionStorage):
    BLACKHOLE = "BLACKHOLE"

    def __init__(self, app):
        super().__init__()
        self.app = app

    def get(self, key, default=None):
        key = self._fix_key(key)
        if key == self.BLACKHOLE:
            return None
        return getattr(self.app, key, default)

    def set(self, key, value, ttl=None):
        key = self._fix_key(key)
        key != self.BLACKHOLE and setattr(self.app, key, value)

    def delete(self, key):
        key = self._fix_key(key)
        key != self.BLACKHOLE and delattr(self.app, key)

    def _fix_key(self, key):
        # 去除component前缀
        if key == "component_access_token":
            return "_access_token"
        elif key == "component_verify_ticket":
            return "verify_ticket"
        # 去除appid前缀
        elif key.startswith(self.app.appid):
            return key[len(self.app.appid):]
        else:
            logging.warning("Unknown wechatpy cache key '{0}', you will not "
                            "get any results by using this key.".format(key))
            return self.BLACKHOLE
