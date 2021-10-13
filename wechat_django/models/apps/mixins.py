from urllib.parse import urlencode
from django.db import models as m
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from wechatpy.crypto import WeChatCrypto
from wechatpy.parser import parse_message

from wechat_django.enums import AppType, EncryptStrategy, WeChatOAuthScope
from wechat_django.exceptions import AbilityError
from wechat_django.messagehandler.base import PlainTextReply, reply2send
from wechat_django.utils.wechatpy import WeChatClient, WeChatOAuth
from wechat_django.utils.crypto import crypto
from wechat_django.utils.model import CacheField
from .base import ConfigurationProperty


class AccessTokenApplicationMixin(m.Model):
    """This application can request APIs"""

    access_token_url = ConfigurationProperty(
        _("Access token url"),
        help_text=_("The url used to fetch access_token"))
    _access_token = CacheField(_("Access Token"), expires_in=2*3600)

    class Meta:
        abstract = True

    @cached_property
    def base_client(self):
        """The base api client of this application"""
        return WeChatClient(self)

    @cached_property
    def client(self):
        """The api client of this application"""
        return self.base_client

    @property
    def access_token(self):
        """The validate access token for this application"""
        return self.base_client.access_token


class HostedApplicationMixin(m.Model):
    """This application belongs to another application"""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.type |= AppType.HOSTED
        return super().save(*args, **kwargs)


class JSAPIMixin(AccessTokenApplicationMixin):
    """This application can fetch some JSAPI tickets"""

    _jsapi_ticket = CacheField(expires_in=2*3600)
    _jsapi_ticket_expires_at = CacheField(expires_in=2*3600, default=0)
    _jsapi_card_ticket = CacheField(expires_in=2*3600)
    _jsapi_card_ticket_expires_at = CacheField(expires_in=2*3600, default=0)

    class Meta:
        abstract = True

    @property
    def jsapi_ticket(self):
        """The validate JSAPI ticket"""
        return self.base_client.jsapi.get_jsapi_ticket()

    @property
    def jsapi_card_ticket(self):
        """The validate JSAPI card ticket"""
        return self.base_client.jsapi.get_jsapi_card_ticket()


class MessagePushApplicationMixin(AccessTokenApplicationMixin):
    """This application can receive messages sent by WeChat server"""

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
        """
        The :class:`~wechatpy.crypto.WeChatCrypto` object for this application

        :return: `wechatpy.crypto.WeChatCrypto`
        """
        if not self.token or not self.encoding_aes_key:
            raise AbilityError
        return WeChatCrypto(
            token=crypto.decrypt(self.token),
            encoding_aes_key=crypto.decrypt(self.encoding_aes_key),
            app_id=self.appid
        )

    def notify_url(self, request):
        """
        Messages will be sent to this url
        """
        path = reverse("wechat_django:handler",
                       kwargs={"app_name": self.name})
        return "{protocol}://{host}{path}".format(
            protocol=request.scheme,
            host=request.get_host(),
            path=path
        )

    def decrypt_message(self, request):
        """
        Decrypt a WeChat message
        """
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
        """
        Encrypt a WeChat message
        """
        xml = reply.render()
        if self.encrypt_strategy == EncryptStrategy.ENCRYPTED\
                and not isinstance(reply, PlainTextReply):
            xml = self.crypto.encrypt_message(xml, request.GET["nonce"],
                                              request.GET["timestamp"])
        return xml

    def parse_message(self, raw_message):
        """
        Transfer a XML message to a :class:`~wechatpy.messages.BaseMessage`
        instance

        :return: wechatpy.messages.BaseMessage
        """
        return parse_message(raw_message)

    def send_message(self, reply):
        """
        Send a message actively

        :type reply: wechatpy.replies.BaseReply
        """
        func_name, kwargs = reply2send(reply)
        func_name and getattr(self.base_client.message, func_name)(**kwargs)


class OAuthApplicationMixin(m.Model):
    DEFAULT_AUTHORIZE_URL = ""
    DEFAULT_SCOPES = ""

    _authorize_url = ConfigurationProperty(_("Authorize URL"))
    oauth_url = ConfigurationProperty(_("OAuth URL"))

    class Meta:
        abstract = True

    @property
    def authorize_url(self):
        """The OAuth2 authorization url"""
        return self._authorize_url or self.DEFAULT_AUTHORIZE_URL

    def build_oauth_url(self, request, next, scope=None, state="",
                        oauth_url=None):
        """
        Build a OAuth2 authorization url

        :param next: The eventual url returned to after user has authorized
        :param oauth_url: The proxy page url redirected to after user has
                          authorized, by default, it use the url of WeChat-
                          Django's
                          :class:`~wechat_django.views.oauth.OAuthProxyView`.
                          Set it to `False` if you want to redirect to above
                          next url directly.
        """
        next = request.build_absolute_uri(next)
        if oauth_url is False:
            # 授权完成直接跳转至重定向地址
            redirect_url = next
        else:
            # 授权完成跳转至中间地址
            if oauth_url:
                base_url = oauth_url
            elif self.oauth_url:
                base_url = self.oauth_url
            else:
                base_url = reverse("wechat_django:oauth_proxy",
                                   kwargs={"app_name": self.name})
            base_url = request.build_absolute_uri(base_url)
            redirect_url = "{0}?{1}".format(base_url,
                                            urlencode({"redirect_uri": next}))
        return self.oauth.get_authorize_url(
            redirect_uri=redirect_url,
            scope=scope or self.DEFAULT_SCOPES,
            state=state
        )

    @cached_property
    def oauth(self):
        """
        The :class:`wechatpy.WeChatOAuth` object for this application

        :return: `wechatpy.WeChatOAuth`
        """
        return WeChatOAuth(self)

    def auth(self, code, scopes):
        """
        Validate user's authorization code and return an
        :class:`~wechat_django.models.User` instance

        :return: `wechat_django.models.User`
        """
        if isinstance(scopes, str):
            scopes = (scopes,)

        data = self.oauth.fetch_access_token(code)
        update = {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"]
        }
        if WeChatOAuthScope.USERINFO in scopes:
            user_info = self.oauth.get_user_info()
            update.update({
                "synchronized_at": tz.now(),
                "avatar_url": user_info.pop("headimgurl"),
                "nickname": user_info.pop("nickname"),
                "unionid": user_info.pop("unionid", None),
                "language": user_info.pop("language", None)
            })
            if "remark" in user_info:
                update["remark"] = user_info.pop("remark")
            update["ext_info"] = user_info
        user, created = self.users.update_or_create(
            openid=data["openid"], defaults=update)
        user.created = created
        return user
