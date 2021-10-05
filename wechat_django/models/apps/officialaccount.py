from django.utils.translation import ugettext_lazy as _

from wechat_django.enums import AppType
from .base import ConfigurationProperty
from .ordinaryapplication import OrdinaryApplication


class OfficialAccountApplicationMixin:
    def save(self, *args, **kwargs):
        self.type = AppType.OFFICIALACCOUNT
        return super().save(*args, **kwargs)


class OfficialAccountApplication(OfficialAccountApplicationMixin,
                                 OrdinaryApplication):
    class EncryptStrategy:
        ENCRYPTED = 'encrypted'
        PLAIN = 'plain'

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
        proxy = True
        verbose_name = _("Official account application")
        verbose_name_plural = _("Official account applications")
