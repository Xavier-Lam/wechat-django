import logging

from django.core.exceptions import ValidationError
from django.core.validators import _lazy_re_compile
from django.db import models as m
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from wechatpy.session import SessionStorage

from wechat_django.enums import AppType
from wechat_django.utils.django import decriptor2contributor
from wechat_django.utils.model import ModelPropertyDescriptor


@decriptor2contributor
class ConfigurationProperty(ModelPropertyDescriptor):
    target = "configurations"


@decriptor2contributor
class StorageProperty(ModelPropertyDescriptor):
    target = "storage"


app_name_re = _lazy_re_compile(r"^[-a-zA-Z0-9_\.]+\Z")


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

    access_token_url = ConfigurationProperty(
        _("Access Token Url"),
        help_text=_("The url used to fetch access_token")
    )

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
        if not self.parent_id and "." in self.name:
            raise ValidationError({
                "name": _("Application's name can only include letters, "
                          "numbers, underscores or hyphens")
            })
        if not app_name_re.match(self.name):
            raise ValidationError({
                "name": _("Application's name can only include letters, "
                          "numbers, underscores or hyphens")
            })
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
        return super().clean()

    def save(self, *args, **kwargs):
        self.type |= AppType.HOSTED
        return super().save(*args, **kwargs)


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
            logging.getLogger("wechat-django").warning(
                "Unknown wechatpy cache key '{0}', you will not get any "
                "results by using this key.".format(key))
            return self.BLACKHOLE
