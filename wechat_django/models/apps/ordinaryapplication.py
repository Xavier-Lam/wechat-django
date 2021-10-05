from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from wechat_django.utils.model import CacheField
from wechat_django.utils.wechatpy import WeChatClient
from .base import Application


class OrdinaryApplication(Application):
    _access_token = CacheField(_("Access Token"), expires_in=2*3600)

    _jsapi_ticket = CacheField(expires_in=2*3600)
    _jsapi_ticket_expires_at = CacheField(expires_in=2*3600)
    _jsapi_card_ticket = CacheField(expires_in=2*3600)
    _jsapi_card_ticket_expires_at = CacheField(expires_in=2*3600)

    class Meta:
        proxy = True
        verbose_name = _("Ordinary application")
        verbose_name_plural = _("Ordinary applications")

    @cached_property
    def base_client(self):
        return WeChatClient(self)

    @cached_property
    def client(self):
        return self.base_client

    @property
    def access_token(self):
        return self.base_client.access_token

    @property
    def jsapi_ticket(self):
        return self.base_client.jsapi.get_jsapi_ticket()

    @property
    def jsapi_card_ticket(self):
        return self.base_client.jsapi.get_jsapi_card_ticket()
