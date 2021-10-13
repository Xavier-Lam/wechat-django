from django.utils.translation import ugettext_lazy as _

from wechat_django.enums import WeChatOAuthScope
from .base import Application
from .mixins import AccessTokenApplicationMixin, OAuthApplicationMixin


class OrdinaryApplication(AccessTokenApplicationMixin, Application):
    """The default class for ordinary application"""
    class Meta:
        proxy = True
        verbose_name = _("Ordinary application")
        verbose_name_plural = _("Ordinary applications")


class WebApplication(OAuthApplicationMixin, OrdinaryApplication):
    """
    `The web application
    <https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html>`_
    """
    DEFAULT_AUTHORIZE_URL = "https://open.weixin.qq.com/connect/qrconnect"
    DEFAULT_SCOPES = WeChatOAuthScope.LOGIN

    class Meta:
        proxy = True
        verbose_name = _("Web application")
        verbose_name_plural = _("Web applications")
