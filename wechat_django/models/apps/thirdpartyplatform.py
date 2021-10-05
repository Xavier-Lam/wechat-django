from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from wechat_django.enums import AppType
from wechat_django.utils.model import CacheField
from wechat_django.utils.wechatpy import WeChatComponent, WeChatComponentClient
from .base import (Application, ConfigurationProperty, HostedApplicationMixin,
                   StorageProperty)
from .miniprogram import MiniProgramApplicationMixin
from .ordinaryapplication import OrdinaryApplication
from .officialaccount import OfficialAccountApplicationMixin


class ThirdPartyPlatform(Application):
    token = ConfigurationProperty(_("Token"))
    encoding_aes_key = ConfigurationProperty(_("Encoding AES Key"))
    verify_ticket = StorageProperty(_("Component Verify Ticket"),
                                    auto_commit=True)

    _access_token = CacheField(_("Access Token"), expires_in=2*3600)

    class Meta:
        proxy = True
        verbose_name = _("Third party platform")
        verbose_name_plural = _("Third party platforms")

    @cached_property
    def client(self):
        return WeChatComponent(self)

    @property
    def access_token(self):
        return self.client.access_token

    def query_auth(self, authorization_code):
        result = self.client._query_auth(authorization_code)
        info = result['authorization_info']
        appid = info['authorizer_appid']
        authorizer = self.children.get(appid=appid)
        authorizer._access_token = info['authorizer_access_token']
        authorizer.refresh_token = info['authorizer_refresh_token']
        return result

    def save(self, *args, **kwargs):
        self.type = AppType.THIRDPARTYPLATFORM
        return super().save(*args, **kwargs)


class AuthorizerApplication(HostedApplicationMixin, OrdinaryApplication):
    _access_token = CacheField(_("Access Token"), expires_in=2*3600)
    refresh_token = StorageProperty(_("Refresh Token"), auto_commit=True)

    class Meta:
        proxy = True
        verbose_name = _("Authorizer application")
        verbose_name_plural = _("Authorizer applications")

    @cached_property
    def base_client(self):
        return WeChatComponentClient(self)

    @cached_property
    def client(self):
        return self.base_client

    @property
    def access_token(self):
        return self.base_client.access_token


class MiniProgramAuthorizerApplication(MiniProgramApplicationMixin,
                                       AuthorizerApplication):
    class Meta:
        proxy = True
        verbose_name = _("Hosted miniprogram application")
        verbose_name_plural = _("Hosted miniprogram applications")

    @cached_property
    def client(self):
        return self.base_client.wxa


class OfficialAccountAuthorizerApplication(OfficialAccountApplicationMixin,
                                           AuthorizerApplication):
    class Meta:
        proxy = True
        verbose_name = _("Hosted official account application")
        verbose_name_plural = _("Hosted official account applications")
