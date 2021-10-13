import json

from django.db import models as m
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from wechatpy.crypto import WeChatWxaCrypto
from wechatpy.utils import check_wxa_signature

from wechat_django.enums import AppType
from .mixins import JSAPIMixin, MessagePushApplicationMixin
from .ordinaryapplication import OrdinaryApplication


class MiniProgramApplicationMixin(m.Model):
    class Meta:
        abstract = True

    @cached_property
    def client(self):
        """
        :returns: wechatpy.client.api.WeChatWxa
        """
        return self.base_client.wxa

    def save(self, *args, **kwargs):
        self.type = AppType.MINIPROGRAM
        return super().save(*args, **kwargs)


class MiniProgramApplication(MiniProgramApplicationMixin,
                             JSAPIMixin,
                             MessagePushApplicationMixin,
                             OrdinaryApplication):
    class Meta:
        proxy = True
        verbose_name = _("Miniprogram application")
        verbose_name_plural = _("Miniprogram applications")

    def auth(self, code):
        """
        Validate user’s code got from wx.login and return an User instance
        """
        data = self.client.code_to_session(code)
        update = {
            "unionid": data.get("unionid"),
            "refresh_token": data["session_key"]
        }
        user, created = self.users.update_or_create(
            openid=data["openid"], defaults=update)
        user.created = created
        return user, data["session_key"]

    def decrypt_data(self, session_key, data, iv):
        """
        Decrypt encypted data

        :raises: ValueError
        """
        crypto = WeChatWxaCrypto(session_key, iv, self.appid)
        return crypto.decrypt_message(data)

    def validate_data(self, session_key, data, sign):
        """
        Validate data sent by client

        :raises: wechatpy.exceptions.InvalidSignatureException
        """
        check_wxa_signature(session_key, data, sign)
        return json.loads(data)
