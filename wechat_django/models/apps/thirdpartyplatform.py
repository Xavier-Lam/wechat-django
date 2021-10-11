from urllib.parse import urlencode
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from wechatpy.component import COMPONENT_MESSAGE_TYPES, ComponentUnknownMessage
from wechatpy.parser import parse_message
from wechatpy.utils import to_text
import xmltodict

from wechat_django.enums import AppType, EncryptStrategy
from wechat_django.messagehandler import reply2send
from wechat_django.utils.wechatpy import (
    ComponentOAuth, WeChatComponent, WeChatComponentClient)
from . import mixins
from .base import Application, StorageProperty
from .miniprogram import MiniProgramApplicationMixin
from .ordinaryapplication import OrdinaryApplication
from .officialaccount import OfficialAccountApplicationMixin


class ThirdPartyPlatform(mixins.MessagePushApplicationMixin, Application):
    encrypt_strategy = EncryptStrategy.ENCRYPTED
    verify_ticket = StorageProperty(_("Component verify ticket"),
                                    auto_commit=True)

    class Meta:
        proxy = True
        verbose_name = _("Third party platform")
        verbose_name_plural = _("Third party platforms")

    @cached_property
    def base_client(self):
        return WeChatComponent(self)

    def parse_message(self, raw_message):
        message = xmltodict.parse(to_text(raw_message))["xml"]
        type = message["InfoType"].lower()
        cls = COMPONENT_MESSAGE_TYPES.get(type, ComponentUnknownMessage)
        return cls(message)

    def send_message(self, reply):
        raise NotImplementedError

    def query_auth(self, authorization_code):
        result = self.client._query_auth(authorization_code)
        info = result['authorization_info']
        appid = info['authorizer_appid']
        authorizer = self.children.get(appid=appid)
        authorizer._access_token = info['authorizer_access_token']
        authorizer.storage["func_info"] = info.get("func_info", None)
        authorizer.refresh_token = info['authorizer_refresh_token']
        return authorizer

    def authorizer_notify_url(self, request):
        path = reverse("wechat_django:authorizer_handler",
                       kwargs={"app_name": self.name, "appid": "$APPID$"})
        return "{protocol}//{host}{path}".format(
            protocol="https" if request.is_secure() else "http",
            host=request.host,
            path=path
        )

    def save(self, *args, **kwargs):
        self.type = AppType.THIRDPARTYPLATFORM
        return super().save(*args, **kwargs)


class AuthorizerApplication(mixins.HostedApplicationMixin,
                            mixins.JSAPIMixin,
                            mixins.MessagePushApplicationMixin,
                            OrdinaryApplication):
    refresh_token = StorageProperty(_("Refresh token"), auto_commit=True)

    class Meta:
        proxy = True
        verbose_name = _("Authorizer application")
        verbose_name_plural = _("Authorizer applications")

    @cached_property
    def base_client(self):
        return WeChatComponentClient(self)

    @property
    def token(self):
        raise AttributeError

    @property
    def encoding_aes_key(self):
        raise AttributeError

    @property
    def encrypt_strategy(self):
        raise AttributeError

    @property
    def crypto(self):
        return self.parent.crypto

    def authorize_url(self, request):
        kwargs = {"app_name": self.name}
        path = reverse("wechat_django:thirdpartyplatform_auth", kwargs=kwargs)
        return request.build_absolute_uri(
            "{0}?{1}".format(path, urlencode({"biz_appid": self.appid})))

    def decrypt_message(self, request):
        return self.parent.decrypt_message(request)

    def encrypt_message(self, reply, request):
        return self.parent.encrypt_message(reply, request)

    def parse_message(self, raw_message):
        return parse_message(raw_message)

    def send_message(self, reply):
        func_name, kwargs = reply2send(reply)
        func_name and getattr(self.base_client.message, func_name)(**kwargs)


class MiniProgramAuthorizerApplication(MiniProgramApplicationMixin,
                                       AuthorizerApplication):
    class Meta:
        proxy = True
        verbose_name = _("Hosted miniprogram application")
        verbose_name_plural = _("Hosted miniprogram applications")


class OfficialAccountAuthorizerApplication(OfficialAccountApplicationMixin,
                                           mixins.OAuthApplicationMixin,
                                           AuthorizerApplication):
    class Meta:
        proxy = True
        verbose_name = _("Hosted official account application")
        verbose_name_plural = _("Hosted official account applications")

    @cached_property
    def oauth(self):
        return ComponentOAuth(self)
