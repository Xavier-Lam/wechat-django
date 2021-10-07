from django.utils.translation import ugettext_lazy as _

from wechat_django.utils.model import CacheField
from .base import Application, AccessTokenApplicationMixin


class OrdinaryApplication(AccessTokenApplicationMixin, Application):
    _jsapi_ticket = CacheField(expires_in=2*3600)
    _jsapi_ticket_expires_at = CacheField(expires_in=2*3600)
    _jsapi_card_ticket = CacheField(expires_in=2*3600)
    _jsapi_card_ticket_expires_at = CacheField(expires_in=2*3600)

    class Meta:
        proxy = True
        verbose_name = _("Ordinary application")
        verbose_name_plural = _("Ordinary applications")

    @property
    def jsapi_ticket(self):
        return self.base_client.jsapi.get_jsapi_ticket()

    @property
    def jsapi_card_ticket(self):
        return self.base_client.jsapi.get_jsapi_card_ticket()
