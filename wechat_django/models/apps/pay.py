from django.utils.translation import ugettext_lazy as _

from wechat_django.enums import AppType
from wechat_django.utils.model import FieldAlias
from wechat_django.utils.wechatpy import WeChatPay
from .base import Application, ConfigurationProperty
from .mixins import HostedApplicationMixin


class PayApplication(Application):
    mchid = FieldAlias("appid", _("mch id"), null=False)
    api_key = FieldAlias("appsecret", _("API key"), null=False)
    mch_cert = ConfigurationProperty(_("mch_cert"), null=True)
    mch_key = ConfigurationProperty(_("mch_key"), null=True)

    class Meta:
        proxy = True
        verbose_name = _("WeChat pay application")
        verbose_name_plural = _("WeChat pay applications")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_clients = {}

    def save(self, *args, **kwargs):
        self.type = AppType.PAY
        return super().save(*args, **kwargs)

    def client(self, app):
        if app.name not in self._cached_clients:
            self._cached_clients[app.name] = WeChatPay(self, app)
        return self._cached_clients[app.name]


class PayMerchant(Application):
    mchid = ConfigurationProperty(_("Merchant's mchid"), null=False)
    api_key = FieldAlias("appsecret", _("API key"), null=False)
    mch_cert = ConfigurationProperty(_("mch_cert"), null=True)
    mch_key = ConfigurationProperty(_("mch_key"), null=True)

    class Meta:
        proxy = True
        verbose_name = _("WeChat pay merchant")
        verbose_name_plural = _("WeChat pay merchants")

    def save(self, *args, **kwargs):
        self.type = AppType.MERCHANTPAY
        return super().save(*args, **kwargs)

    @property
    def client(self):
        raise AttributeError


class HostedPayApplication(PayApplication, HostedApplicationMixin,
                           Application):
    _default_client = None

    class Meta:
        proxy = True
        verbose_name = _("Hosted WeChat pay application")
        verbose_name_plural = _("Hosted WeChat pay applications")

    def client(self, app=None):
        if not app:
            if not self._default_client:
                self._default_client = WeChatPay(self)
            return self._default_client
        return super().client(app)
